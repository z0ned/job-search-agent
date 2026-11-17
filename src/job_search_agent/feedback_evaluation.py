"""Benchmark the feedback interpreter against the frozen gold suite."""

import argparse
from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter

from .feedback import FeedbackProviderError, OpenAIFeedbackProvider, interpret_feedback

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


def collect_predictions(suite, interpret):
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
        if not exact:
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
            failures.append(failure)

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
    }


def _consistency(suite, predictions):
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
                _signals(signals, SIGNAL_FIELDS[:-1]),
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenarios", nargs="?", type=Path, default=GOLD_FILE)
    parser.add_argument("--model", help="OpenAI model, otherwise read from the environment")
    parser.add_argument("--temperature", type=float, help="Override sampling temperature for supported models")
    parser.add_argument("--runs", type=int, default=2, help="Number of live passes (default: 2)")
    parser.add_argument(
        "--predictions", type=Path, action="append",
        help="Score saved predictions by case ID. Repeat for separate passes.",
    )
    args = parser.parse_args(argv)
    if args.runs < 1:
        parser.error("--runs must be positive")
    if args.predictions and (args.model or args.temperature is not None):
        parser.error("--model and --temperature apply to live evaluation only")

    started = perf_counter()
    try:
        suite = load_suite(args.scenarios)
        predictions, reports = [], []
        if args.predictions:
            for path in args.predictions:
                run_started = perf_counter()
                data, prediction = _read_json(path)
                reports.append(evaluate(suite, prediction))
                reports[-1]["elapsed_seconds"] = round(perf_counter() - run_started, 3)
                reports[-1]["predictions_sha256"] = hashlib.sha256(data).hexdigest()
                predictions.append(prediction)
            source = {"mode": "replay"}
        else:
            provider = OpenAIFeedbackProvider(model=args.model, temperature=args.temperature)
            source = {"mode": "live", "requested_model": provider.model, "temperature_override": args.temperature}

            def run(decision, feedback, context):
                return interpret_feedback(decision, feedback, context, provider=provider, hard_rules=suite.hard_rules)

            for _ in range(args.runs):
                run_started = perf_counter()
                prediction = collect_predictions(suite, run)
                reports.append(evaluate(suite, prediction))
                reports[-1]["elapsed_seconds"] = round(perf_counter() - run_started, 3)
                predictions.append(prediction)
    except (ValueError, FeedbackProviderError) as exc:
        print(f"Evaluation could not start. {exc}", file=sys.stderr)
        return 2

    repeated = len(predictions) >= 2
    full_protocol = sum(not run["execution_errors"] for run in reports) >= 2
    report = {
        "suite_version": suite.version,
        "suite_sha256": suite.sha256,
        "signal_label_matching": "Exact feature, polarity, and context scope. No synonym mappings supplied.",
        "evaluation_source": source,
        "runs": reports,
        "repeated_pass_requirement_met": full_protocol,
        "consistency": _consistency(suite, predictions) if repeated else None,
        "elapsed_seconds": round(perf_counter() - started, 3),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return int(not full_protocol or not all(report["quality_gates_passed"] for report in reports))


if __name__ == "__main__":
    sys.exit(main())
