"""Benchmark the feedback interpreter against the frozen gold suite."""

import argparse
from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter

from .feedback import (
    PROMPT_VERSION, _INSTRUCTIONS, _PROPOSAL_SCHEMA, FeedbackProviderError, OpenAIFeedbackProvider, interpret_feedback,
)
from .feedback_semantic_evaluation import compare_signals, consistency_signature
from .feedback_taxonomy import TAXONOMY_VERSION

GOLD_FILE = Path("feedback_interpretation_gold_cases_v1.json")
RULE_ASSUMPTIONS = (
    "permanent_base_minimum_usd", "w2_hourly_minimum_usd", "1099_hourly_minimum_usd",
    "c2c_hourly_minimum_usd", "unknown_salary_remains_eligible",
)
COMMUTE_RULES = [
    "Within 10 driving miles: onsite acceptable.",
    "Greater than 10 and less than 30 driving miles: Mondays and Fridays must be remote. "
    "Unknown days require verification.",
    "At least 30 driving miles: regular work must be fully remote. "
    "Occasional visits or business trips are allowed.",
]
CLEAR = "PENDING_APPROVAL"
CLARIFY = "NEEDS_CLARIFICATION"
PROFILE_FACT = "PROFILE_FACT_REVIEW"
ACTIVE_ROUTES = {CLEAR, CLARIFY, PROFILE_FACT}
ACTION_VALUES = {
    "UNCHANGED", "REPORT_EXISTING_ELIGIBILITY_VIOLATION",
    "REQUIRES_SEPARATE_EXPLICIT_RULE_CONFIRMATION",
}
SIGNAL_FIELDS = ("dimension", "feature", "polarity", "strength", "scope", "condition", "evidence_quote")
PROTOCOL_FIELDS = ("feature", "polarity", "scope")
DIMENSION_SCOPE_FIELDS = ("dimension", "scope")
BENCHMARK_VERSION = "2.0"
PREDICTION_FIELDS = {
    "decision", "original_feedback", "review_status", "interpretations", "clarification_question",
    "profile_fact_candidate", "hard_constraint_action", "hard_constraints_mutated", "model", "prompt_version",
}
SIGNAL_FIELD_SET = set(SIGNAL_FIELDS)


@dataclass(frozen=True)
class GoldSuite:
    version: str
    sha256: str
    cases: list[dict]
    hard_rules: dict


def _read_json(path):
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise ValueError("could not read the JSON file") from exc
    try:
        return data, json.loads(data)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("file must contain valid JSON") from exc


def _nonblank(value):
    return isinstance(value, str) and bool(value.strip())


def _scope(signal):
    scope = signal["scope"]
    return scope["type"], scope["value"]


def _field(signal, name):
    return _scope(signal) if name == "scope" else signal.get(name)


def _signals(signals, fields):
    return Counter(tuple(_field(signal, field) for field in fields) for signal in signals)


def _check_signal(signal):
    if not isinstance(signal, Mapping):
        raise ValueError("signal must be an object")
    for name in ("dimension", "feature", "polarity", "strength"):
        if not _nonblank(signal.get(name)):
            raise ValueError(f"signal requires {name}")
    scope = signal.get("scope")
    if not isinstance(scope, Mapping) or not all(_nonblank(scope.get(key)) for key in ("type", "value")):
        raise ValueError("signal requires scope.type and scope.value")
    for name in ("evidence_quote", "condition"):
        if signal.get(name) is not None and not isinstance(signal[name], str):
            raise ValueError(f"signal {name} must be text")


def _has_evidence(signal, feedback):
    quote = signal.get("evidence_quote")
    return _nonblank(quote) and quote in feedback


def load_suite(path: str | Path, *, expected_count: int = 50) -> GoldSuite:
    """Load the authored case format and fingerprint the exact input bytes."""
    data, raw = _read_json(path)
    if not isinstance(raw, dict) or not _nonblank(raw.get("suite_version")):
        raise ValueError("gold file requires suite_version")
    cases = raw.get("test_cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("gold file requires a nonempty test_cases array")
    if len(cases) != expected_count:
        raise ValueError(f"expected {expected_count} scenarios, found {len(cases)}")
    assumptions = raw.get("assumptions")
    if not isinstance(assumptions, dict) or any(field not in assumptions for field in RULE_ASSUMPTIONS):
        raise ValueError("gold file requires the eligibility assumptions")
    identifiers = set()
    for index, case in enumerate(cases, start=1):
        try:
            if not isinstance(case, dict):
                raise ValueError("case must be an object")
            case_id = case.get("case_id")
            if not _nonblank(case_id) or case_id in identifiers:
                raise ValueError("case_id must be a unique nonblank string")
            if case.get("decision") not in ("interested", "rejected") or not _nonblank(case.get("original_feedback")):
                raise ValueError("case requires an interested or rejected decision and original feedback")
            if not isinstance(case.get("job_context"), dict):
                raise ValueError("case requires a job_context object")
            if case.get("expected_review_status") not in ACTIVE_ROUTES:
                raise ValueError("unexpected reference review status")
            if case.get("expected_hard_constraint_action") not in ACTION_VALUES:
                raise ValueError("unexpected reference hard constraint action")
            if type(case.get("expected_category_interest_change")) is not bool:
                raise ValueError("case requires the expected category interest change indicator")
            signals = case.get("expected_interpretations")
            if not isinstance(signals, list):
                raise ValueError("case requires an expected_interpretations list")
            for signal in signals:
                _check_signal(signal)
                if not _has_evidence(signal, case["original_feedback"]):
                    raise ValueError("reference evidence_quote must be present verbatim in original feedback")
        except (ValueError, TypeError) as exc:
            raise ValueError(f"case {index}: {exc}") from exc
        identifiers.add(case_id)
    hard_rules = {field: assumptions[field] for field in RULE_ASSUMPTIONS}
    hard_rules["commute_rules"] = COMMUTE_RULES
    return GoldSuite(raw["suite_version"], hashlib.sha256(data).hexdigest(), cases, hard_rules)


def collect_predictions(suite, interpret, *, on_case_complete=None):
    """Pass only original inputs to the supplied interpreter, in official case order."""
    predictions = {}
    for case in suite.cases:
        try:
            result = interpret(case["decision"], case["original_feedback"], case["job_context"])
            if not isinstance(result, Mapping):
                result = result.to_dict()
        except Exception as exc:
            result = {"evaluation_error": type(exc).__name__}
        predictions[case["case_id"]] = result
        if on_case_complete is not None:
            on_case_complete(case["case_id"])
    return predictions


def _prediction(result):
    if not isinstance(result, Mapping):
        raise ValueError("prediction must be an object")
    if result.get("review_status") not in ACTIVE_ROUTES:
        raise ValueError("unknown review status")
    interpretations = result.get("interpretations")
    if not isinstance(interpretations, list):
        raise ValueError("prediction requires an interpretations list")
    for signal in interpretations:
        _check_signal(signal)
    return interpretations


def _ratio(correct, total):
    return {"correct": correct, "total": total, "accuracy": correct / total if total else None}


def _route_matches(expected, result):
    actual = result.get("review_status")
    if actual != expected:
        return False
    question = result.get("clarification_question")
    candidate = result.get("profile_fact_candidate")
    question_matches = _nonblank(question) if actual == CLARIFY else question is None
    candidate_matches = _nonblank(candidate) if actual == PROFILE_FACT else candidate is None
    return question_matches and candidate_matches


def _within_prediction_contract(result, signals):
    return result.keys() <= PREDICTION_FIELDS and all(
        signal.keys() <= SIGNAL_FIELD_SET and signal["scope"].keys() <= {"type", "value"}
        for signal in signals
    )


def _semantic_summary(counts, legacy_gates, semantic_cases):
    total = len(semantic_cases)
    scope = _ratio(counts["semantic_clear_scope_correct"], counts["clear_cases"])
    recall = _ratio(counts["semantic_matched"], counts["expected_signals"])
    precision = _ratio(counts["semantic_matched"], counts["emitted_signals"])
    gates = {
        "all_cases_completed": legacy_gates["all_cases_completed"],
        "hard_constraints_unchanged": legacy_gates["hard_constraints_unchanged"],
        "all_hard_rule_actions_authorized": counts["authorized_rule_action"] == total,
        "no_unsupported_career_category_downgrades": counts["semantic_downgrade_cases_clear"] == total,
        "clear_case_dimension_and_scope_at_least_95_percent": (scope["accuracy"] or 0) >= 0.95,
        "explicit_signal_recall_at_least_90_percent": (recall["accuracy"] or 0) >= 0.90,
        "all_ambiguity_and_profile_facts_routed_safely": legacy_gates["all_ambiguity_and_profile_facts_routed_safely"],
        "all_emitted_evidence_quotes_grounded": legacy_gates["all_emitted_evidence_quotes_grounded"],
    }
    return {
        "clear_case_dimension_and_scope_accuracy": scope,
        "explicit_signal_recall": recall,
        "signal_precision": precision,
        "missed_signals": counts["expected_signals"] - counts["semantic_matched"],
        "extra_signals": counts["emitted_signals"] - counts["semantic_matched"],
        "incorrectly_scoped_signals": counts["semantic_wrong_scope"],
        "incorrectly_conditioned_signals": counts["semantic_wrong_condition"],
        "unsupported_career_category_downgrades": counts["semantic_unsupported_downgrades"],
        "cases_without_unsupported_career_category_downgrades": _ratio(
            counts["semantic_downgrade_cases_clear"], total,
        ),
        "authorized_hard_rule_actions": _ratio(counts["authorized_rule_action"], total),
        "quality_gates": gates,
        "quality_gates_passed": all(gates.values()),
        "cases": semantic_cases,
    }


def evaluate(suite: GoldSuite, predictions: Mapping):
    """Score a complete prediction set without exposing original feedback in the report."""
    ids = {case["case_id"] for case in suite.cases}
    if not isinstance(predictions, Mapping) or set(predictions) != ids:
        raise ValueError("prediction IDs must match the full gold case set")
    counts = Counter()
    confusion = defaultdict(Counter)
    errors = Counter()
    versions = defaultdict(set)
    failures = []
    semantic_cases = []
    for case in suite.cases:
        case_id = case["case_id"]
        expected = case["expected_interpretations"]
        expected_route = case["expected_review_status"]
        expected_action = case["expected_hard_constraint_action"]
        result = predictions[case_id]
        error = result.get("evaluation_error") if isinstance(result, Mapping) else None
        try:
            actual = [] if error else _prediction(result)
        except (ValueError, TypeError):
            actual, error = [], "InvalidPrediction"
        if error:
            error = error if isinstance(error, str) and error.isidentifier() else "PredictionError"
            errors[error] += 1
            result = {}

        expected_signals = _signals(expected, PROTOCOL_FIELDS)
        actual_signals = _signals(actual, PROTOCOL_FIELDS)
        missed = (expected_signals - actual_signals).total()
        extra = (actual_signals - expected_signals).total()
        counts["expected_signals"] += len(expected)
        counts["emitted_signals"] += len(actual)
        counts["missed_signals"] += missed
        counts["false_positive_signals"] += extra

        route_correct = _route_matches(expected_route, result)
        actual_action = result.get("hard_constraint_action")
        action_correct = actual_action == expected_action
        no_hard_mutation = result.get("hard_constraints_mutated") is False
        expected_categories = {
            (signal["polarity"], _scope(signal)) for signal in expected
            if signal["dimension"] == "career_category"
        }
        actual_categories = {
            (signal["polarity"], _scope(signal)) for signal in actual
            if signal["dimension"] == "career_category" or signal["scope"]["type"] == "career_category"
        }
        unmatched_categories = actual_categories - expected_categories
        unmatched_downgrade = any(polarity == "negative" for polarity, _ in unmatched_categories)
        category_correct = bool(actual_categories) == case["expected_category_interest_change"]
        dimension_scope_correct = (
            _signals(expected, DIMENSION_SCOPE_FIELDS) == _signals(actual, DIMENSION_SCOPE_FIELDS)
        )
        unsupported_evidence = sum(not _has_evidence(signal, case["original_feedback"]) for signal in actual)
        original_preserved = result.get("original_feedback") == case["original_feedback"]
        confusion[expected_route][result.get("review_status", "EXECUTION_ERROR")] += 1
        counts["route_correct"] += route_correct
        counts[f"{expected_route}_cases"] += 1
        counts[f"{expected_route}_correct"] += route_correct and action_correct
        counts["clear_cases"] += expected_route == CLEAR
        counts["clear_dimension_scope_correct"] += expected_route == CLEAR and dimension_scope_correct
        counts["hard_action_correct"] += action_correct
        counts["no_hard_mutation"] += no_hard_mutation
        counts["no_unmatched_downgrade"] += not error and not unmatched_downgrade
        counts["unmatched_categories"] += len(unmatched_categories)
        counts["unsupported_evidence"] += unsupported_evidence
        counts["category_correct"] += category_correct and not error

        for field in ("model", "prompt_version"):
            if isinstance(result.get(field), str):
                versions[field].add(result[field])
        mismatched_fields = [
            field for field in SIGNAL_FIELDS if _signals(expected, (field,)) != _signals(actual, (field,))
        ]
        exact = (
            not error and route_correct and action_correct and no_hard_mutation and category_correct
            and original_preserved and _signals(expected, SIGNAL_FIELDS) == _signals(actual, SIGNAL_FIELDS)
        )
        counts["exact_cases"] += bool(exact)
        failure = {
            "case_id": case_id,
            "expected_route": expected_route,
            "actual_route": result.get("review_status"),
            "route_correct": route_correct,
            "expected_hard_action": expected_action,
            "actual_hard_action": (
                actual_action if isinstance(actual_action, str) and actual_action in ACTION_VALUES else None
            ),
            "hard_constraint_nonmutation_confirmed": no_hard_mutation,
            "category_interest_indicator_correct": category_correct and not error,
            "unmatched_career_category_signals": len(unmatched_categories),
            "unmatched_career_category_downgrade": unmatched_downgrade,
            "dimension_and_scope_correct": dimension_scope_correct,
            "missed_signals": missed,
            "false_positive_signals": extra,
            "unsupported_evidence_quotes": unsupported_evidence,
            "signal_fields_with_differences": mismatched_fields,
            "original_feedback_preserved": original_preserved,
        }
        if error:
            failure["execution_error"] = error
        if not exact:
            failures.append(failure)

        semantic = compare_signals(expected, actual, case["original_feedback"])
        unsupported_downgrades = semantic["unsupported_career_category_downgrades"]
        authorized_rule_action = (
            action_correct and no_hard_mutation and _within_prediction_contract(result, actual)
            and (actual_action != "REQUIRES_SEPARATE_EXPLICIT_RULE_CONFIRMATION"
                 or result.get("review_status") == PROFILE_FACT)
        )
        counts["semantic_matched"] += len(semantic["correct_signals"])
        counts["semantic_wrong_scope"] += len(semantic["incorrectly_scoped_signals"])
        counts["semantic_wrong_condition"] += len(semantic["incorrectly_conditioned_signals"])
        counts["semantic_unsupported_downgrades"] += len(unsupported_downgrades)
        counts["semantic_downgrade_cases_clear"] += not error and not unsupported_downgrades
        counts["semantic_clear_scope_correct"] += expected_route == CLEAR and semantic["dimension_and_scope_correct"]
        counts["authorized_rule_action"] += authorized_rule_action
        classifications = [name for name, detected in (
            ("route_mismatch", not route_correct),
            ("unauthorized_hard_rule_action", not authorized_rule_action),
            ("unsupported_career_category_downgrade", unsupported_downgrades),
            ("unsupported_evidence", unsupported_evidence),
            ("missed_signal", semantic["missed_signals"]),
            ("extra_signal", semantic["extra_signals"]),
            ("incorrect_scope", semantic["incorrectly_scoped_signals"]),
            ("incorrect_condition", semantic["incorrectly_conditioned_signals"]),
            ("changed_feedback", not original_preserved),
        ) if detected]
        semantic_cases.append({
            "case_id": case_id,
            "literal_case_match": bool(exact),
            "expected_route": expected_route,
            "actual_route": result.get("review_status"),
            "expected_hard_action": expected_action,
            "actual_hard_action": failure["actual_hard_action"],
            "hard_rule_action_authorized": authorized_rule_action,
            "validation_status": "execution_error" if error else "accepted",
            "failure_classifications": ["execution_error"] if error else classifications,
            **({"execution_error": error} if error else {}),
            **semantic,
        })

    total = len(suite.cases)
    expected_total = counts["expected_signals"]
    emitted_total = counts["emitted_signals"]
    matched_total = expected_total - counts["missed_signals"]
    clear_scope = _ratio(counts["clear_dimension_scope_correct"], counts["clear_cases"])
    signal_recall = _ratio(matched_total, expected_total)
    safe_clarification = _ratio(counts[f"{CLARIFY}_correct"], counts[f"{CLARIFY}_cases"])
    safe_profile_fact = _ratio(counts[f"{PROFILE_FACT}_correct"], counts[f"{PROFILE_FACT}_cases"])
    safe_special_routes = _ratio(
        safe_clarification["correct"] + safe_profile_fact["correct"],
        safe_clarification["total"] + safe_profile_fact["total"],
    )
    gates = {
        "all_cases_completed": not errors,
        "hard_constraints_unchanged": counts["no_hard_mutation"] == total,
        "no_unmatched_career_category_downgrades": counts["no_unmatched_downgrade"] == total,
        "clear_case_dimension_and_scope_at_least_95_percent": (clear_scope["accuracy"] or 0) >= 0.95,
        "explicit_signal_recall_at_least_90_percent": (signal_recall["accuracy"] or 0) >= 0.90,
        "all_ambiguity_and_profile_facts_routed_safely": safe_special_routes["correct"] == safe_special_routes["total"],
        "all_emitted_evidence_quotes_grounded": counts["unsupported_evidence"] == 0,
    }
    return {
        "scenario_count": total,
        "exact_case_match": _ratio(counts["exact_cases"], total),
        "route_accuracy": _ratio(counts["route_correct"], total),
        "route_confusion": {route: dict(values) for route, values in confusion.items()},
        "ambiguity_and_profile_fact_routing": safe_special_routes,
        "clarification_routing": safe_clarification,
        "profile_fact_routing": safe_profile_fact,
        "hard_constraint_no_mutation": _ratio(counts["no_hard_mutation"], total),
        "expected_hard_action_accuracy": _ratio(counts["hard_action_correct"], total),
        "cases_without_unmatched_career_category_downgrades": _ratio(counts["no_unmatched_downgrade"], total),
        "unmatched_career_category_signals": counts["unmatched_categories"],
        "category_interest_indicator_accuracy": _ratio(counts["category_correct"], total),
        "clear_case_dimension_and_scope_accuracy": clear_scope,
        "explicit_signal_recall": signal_recall,
        "signal_precision": _ratio(matched_total, emitted_total),
        "missed_signals": counts["missed_signals"],
        "false_positive_signals": counts["false_positive_signals"],
        "evidence_grounding": _ratio(emitted_total - counts["unsupported_evidence"], emitted_total),
        "unsupported_evidence_quotes": counts["unsupported_evidence"],
        "quality_gates": gates,
        "quality_gates_passed": all(gates.values()),
        "execution_errors": dict(errors),
        "versions": {name: sorted(values) for name, values in versions.items()},
        "failures": failures,
        "semantic": _semantic_summary(counts, gates, semantic_cases),
    }


def _consistency(suite, predictions, *, semantic=False):
    changed, unverified = [], []
    for case in suite.cases:
        case_id = case["case_id"]
        signatures = []
        for run in predictions:
            result = run[case_id]
            try:
                signals = _prediction(result)
                if result.get("evaluation_error"):
                    raise ValueError("prediction failed")
            except (ValueError, TypeError):
                unverified.append(case_id)
                break
            signatures.append((
                result["review_status"], result.get("hard_constraint_action"),
                consistency_signature(signals) if semantic else _signals(signals, SIGNAL_FIELDS[:-1]),
            ))
        else:
            if any(signature != signatures[0] for signature in signatures[1:]):
                changed.append(case_id)
    total = len(suite.cases)
    return {
        "unchanged_cases": _ratio(total - len(changed) - len(unverified), total),
        "changed_case_ids": changed,
        "unverified_case_ids": unverified,
    }


class _RecordingProvider:
    def __init__(self, provider):
        self._provider = provider
        self.model = provider.model
        self.proposals = {}
        self._current_proposal = None

    def propose(self, decision, feedback, job_context, hard_rules):
        self._current_proposal = self._provider.propose(decision, feedback, job_context, hard_rules)
        return self._current_proposal

    def finish_case(self, case_id):
        self.proposals[case_id] = self._current_proposal
        self._current_proposal = None


def _save_json(path, value):
    data = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    with path.open("xb") as file:
        file.write(data)
    return hashlib.sha256(data).hexdigest()


def _prompt_fingerprints():
    schema = json.dumps(_PROPOSAL_SCHEMA, sort_keys=True, separators=(",", ":")).encode()
    return {
        "instructions_sha256": hashlib.sha256(_INSTRUCTIONS.encode()).hexdigest(),
        "proposal_schema_sha256": hashlib.sha256(schema).hexdigest(),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenarios", nargs="?", type=Path, default=GOLD_FILE)
    parser.add_argument("--model", help="OpenAI model, otherwise read from the environment")
    parser.add_argument("--temperature", type=float, help="Override sampling temperature for supported models")
    parser.add_argument("--runs", type=int, default=2, help="Number of live passes (default: 2)")
    parser.add_argument("--expected-count", type=int, default=50, help="Case count for a separate fixture")
    parser.add_argument(
        "--save-predictions", type=Path,
        help="Write validated predictions, raw structured proposals and configuration to a new directory",
    )
    parser.add_argument(
        "--predictions", type=Path, action="append",
        help="Score saved predictions by case ID. Repeat for separate passes.",
    )
    args = parser.parse_args(argv)
    if args.runs < 1:
        parser.error("--runs must be positive")
    if args.expected_count < 1:
        parser.error("--expected-count must be positive")
    if args.scenarios.name == GOLD_FILE.name and args.expected_count != 50:
        parser.error("the original gold suite requires 50 scenarios")
    if args.predictions and (args.model or args.temperature is not None or args.save_predictions):
        parser.error("--model, --temperature and --save-predictions apply to live evaluation only")

    started = perf_counter()
    started_at = datetime.now(UTC).isoformat(timespec="seconds")
    try:
        suite = load_suite(args.scenarios, expected_count=args.expected_count)
        predictions, reports = [], []
        configuration = {
            "benchmark_version": BENCHMARK_VERSION,
            "taxonomy_version": TAXONOMY_VERSION,
            "suite_file": str(args.scenarios),
            "suite_version": suite.version,
            "suite_sha256": suite.sha256,
            "scenario_count": len(suite.cases),
            "hard_rules": suite.hard_rules,
            "started_at_utc": started_at,
            "python_version": sys.version.split()[0],
        }
        if args.predictions:
            for path in args.predictions:
                run_started = perf_counter()
                data, prediction = _read_json(path)
                reports.append(evaluate(suite, prediction))
                reports[-1]["elapsed_seconds"] = round(perf_counter() - run_started, 3)
                reports[-1]["predictions_sha256"] = hashlib.sha256(data).hexdigest()
                predictions.append(prediction)
            source = {"mode": "replay", "passes": len(predictions)}
        else:
            provider = OpenAIFeedbackProvider(model=args.model, temperature=args.temperature)
            source = {
                "mode": "live", "requested_model": provider.model, "temperature_override": args.temperature,
                "prompt_version": PROMPT_VERSION, "passes": args.runs, **_prompt_fingerprints(),
            }
            if args.save_predictions:
                args.save_predictions.mkdir(parents=True)
                _save_json(args.save_predictions / "configuration.json", {**configuration, "evaluation_source": source})

            for pass_number in range(1, args.runs + 1):
                recorder = _RecordingProvider(provider) if args.save_predictions else None
                live_provider = recorder or provider

                def run(decision, feedback, context):
                    return interpret_feedback(
                        decision, feedback, context, provider=live_provider, hard_rules=suite.hard_rules,
                    )

                on_complete = recorder.finish_case if recorder else None
                run_started = perf_counter()
                prediction = collect_predictions(suite, run, on_case_complete=on_complete)
                metadata = {}
                if recorder:
                    predictions_file = f"pass-{pass_number}.json"
                    proposals_file = f"pass-{pass_number}.proposals.json"
                    metadata["capture_files"] = {
                        "predictions": predictions_file,
                        "proposals": proposals_file,
                    }
                    metadata["predictions_sha256"] = _save_json(
                        args.save_predictions / predictions_file, prediction,
                    )
                    metadata["proposals_sha256"] = _save_json(
                        args.save_predictions / proposals_file, recorder.proposals,
                    )
                report = evaluate(suite, prediction)
                reports.append({**report, **metadata, "elapsed_seconds": round(perf_counter() - run_started, 3)})
                predictions.append(prediction)
    except (ValueError, OSError, FeedbackProviderError) as exc:
        print(f"Evaluation could not start. {exc}", file=sys.stderr)
        return 2

    repeated = len(predictions) >= 2
    full_protocol = sum(not run["execution_errors"] for run in reports) >= 2
    report = {
        "suite_version": suite.version,
        "suite_sha256": suite.sha256,
        "configuration": configuration,
        "signal_label_matching": "Exact feature, polarity, and context scope. No synonym mappings supplied.",
        "semantic_signal_matching": "Dimension, canonical feature, polarity, canonical context scope, and exact condition.",
        "evaluation_source": source,
        "runs": reports,
        "repeated_pass_requirement_met": full_protocol,
        "consistency": _consistency(suite, predictions) if repeated else None,
        "semantic_consistency": _consistency(suite, predictions, semantic=True) if repeated else None,
        "elapsed_seconds": round(perf_counter() - started, 3),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return int(not full_protocol or not all(report["semantic"]["quality_gates_passed"] for report in reports))


if __name__ == "__main__":
    sys.exit(main())
