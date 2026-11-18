"""Capture and score independent v3 feedback interpreter benchmark passes."""

import argparse
from collections import Counter
from collections.abc import Mapping
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter
from uuid import uuid4

from . import feedback_extraction_v3 as extraction
from .feedback import FeedbackProviderError
from .feedback_evaluation import (
    ACTION_VALUES, ACTIVE_ROUTES, CLEAR, CLARIFY, PROFILE_FACT,
    _RecordingProvider, _nonblank, _ratio, _read_json, _save_json, collect_predictions, load_suite,
)
from .feedback_extraction_v3 import OpenAIFeedbackProviderV3
from .feedback_taxonomy import TAXONOMY_VERSION, canonicalize_signal
from .feedback_v3 import _feature_id, _label_key, interpret_feedback_v3


SUITE_COUNTS = {"gold": 50, "regression": 12, "holdout": 12}
HIGH_RISK_CASE_IDS = {
    "gold": ("FI-012", "FI-016", "FI-035"),
    "regression": ("FH-003", "FH-007", "FH-012"),
    "holdout": ("FH3-001", "FH3-002", "FH3-006", "FH3-007", "FH3-008", "FH3-012"),
}
PASS_COUNT = 2
BENCHMARK_VERSION = "3.0"


def _fingerprint(data):
    return sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _has_value(value):
    return value is not None and (not isinstance(value, str) or bool(value.strip()))


def load_v3_suite(path, suite_kind):
    suite = load_suite(path, expected_count=SUITE_COUNTS[suite_kind])
    for case in suite.cases:
        for signal in case["expected_interpretations"]:
            qualifiers = signal.get("qualifiers", [])
            if not isinstance(qualifiers, list) or any(
                not isinstance(qualifier, Mapping) or not _nonblank(qualifier.get("kind"))
                or not _has_value(qualifier.get("value")) for qualifier in qualifiers
            ):
                raise ValueError(f"{case['case_id']} has invalid reference qualifiers")
            if len({qualifier["kind"] for qualifier in qualifiers}) != len(qualifiers):
                raise ValueError(f"{case['case_id']} has repeated reference qualifier kinds")
    return suite


def _literal_identity(signal, *, reference):
    scope = signal["scope"]
    label = signal["feature"] if reference else signal["display_label"]
    referent = scope["value"] if reference else scope["referent"]
    return label, signal["polarity"], scope["type"], referent


def _exact_identity(signal, *, reference):
    condition = signal.get("condition")
    quote = signal.get("evidence_quote") if reference else signal["evidence"][0]["quote"]
    qualifiers = signal.get("qualifiers", []) if reference else signal["scope"]["qualifiers"]
    return (
        *_literal_identity(signal, reference=reference), signal["dimension"], signal["strength"],
        condition if reference or condition is None else condition["quote"], quote,
        tuple(sorted((item["kind"], _fingerprint(item["value"])) for item in qualifiers)),
    )


def _canonical_identity(signal, *, reference):
    label, polarity, scope_type, referent = _literal_identity(signal, reference=reference)
    dimension = signal["dimension"]
    scope = {"type": scope_type, "value": referent}
    canonical = canonicalize_signal({"dimension": dimension, "feature": label, "polarity": polarity, "scope": scope})
    qualifiers = signal.get("qualifiers", []) if reference else signal["scope"]["qualifiers"]
    feature_id = (_feature_id(dimension, label, {"type": scope_type, "referent": referent, "qualifiers": qualifiers}, polarity)
                  if reference else signal["feature_id"])
    if feature_id is None:
        return None
    condition = signal.get("condition")
    if not reference and condition is not None:
        condition = condition["quote"]
    return (
        dimension, feature_id, polarity, scope_type, canonical.scope_id,
        tuple(sorted((qualifier["kind"], _fingerprint(qualifier["value"])) for qualifier in qualifiers)),
        condition,
    )


def _matched(expected, actual, identity):
    expected_ids = Counter(identity(signal, reference=True) for signal in expected)
    actual_ids = Counter(identity(signal, reference=False) for signal in actual)
    expected_ids.pop(None, None)
    actual_ids.pop(None, None)
    return (expected_ids & actual_ids).total()


def _valid_anchor(anchor, case, revision, *, assertion=False):
    if not isinstance(anchor, Mapping):
        return False
    if anchor.get("origin") == "job_context" and not assertion:
        context = case["job_context"]
        key = anchor.get("key")
        return (anchor.get("role") == "context_only" and isinstance(key, str) and key in context
                and type(anchor.get("value")) is type(context[key])
                and anchor["value"] == context[key])
    start, end = anchor.get("start"), anchor.get("end")
    feedback = case["original_feedback"]
    return (
        anchor.get("origin") == "feedback" and anchor.get("source_revision") == revision
        and (not assertion or anchor.get("role") == "preference")
        and type(start) is int and type(end) is int and 0 <= start < end <= len(feedback)
        and feedback[start:end] == anchor.get("quote")
    )


def _structured_signal(signal):
    if not isinstance(signal, Mapping) or not _nonblank(signal.get("display_label")):
        return False
    scope, condition, feature, evidence = (signal.get(key) for key in ("scope", "condition", "feature_id", "evidence"))
    if (
        not isinstance(scope, Mapping) or not isinstance(scope.get("type"), str)
        or not isinstance(signal.get("dimension"), str)
        or scope["type"] not in extraction.DIMENSION_SCOPES.get(signal["dimension"], ())
        or not _nonblank(scope.get("referent")) or not isinstance(scope.get("qualifiers"), list)
        or signal.get("polarity") not in ("positive", "negative", "uncertain")
        or signal.get("strength") not in ("strong", "mild") or (feature is not None and not _nonblank(feature))
        or signal.get("identity_status") != ("registered" if feature else "candidate")
        or signal.get("application_status") != "held_for_review"
        or not isinstance(evidence, list) or not evidence or not isinstance(evidence[0], Mapping)
        or (condition is not None and (not isinstance(condition, Mapping)
                                     or not all(_nonblank(condition.get(key)) for key in ("kind", "value", "quote"))))
    ):
        return False
    qualifiers_valid = all(
        isinstance(qualifier, Mapping) and _nonblank(qualifier.get("kind")) and _has_value(qualifier.get("value"))
        for qualifier in scope["qualifiers"]
    )
    return qualifiers_valid and feature == _feature_id(
        signal["dimension"], signal["display_label"], scope, signal["polarity"],
    )


def _case_diagnostics(case, prediction):
    actual, error, issues = [], None, []
    expected = case["expected_interpretations"]
    if not isinstance(prediction, Mapping):
        error, prediction = "InvalidPrediction", {}
    else:
        error = prediction.get("evaluation_error")
        signals = prediction.get("interpretations")
        issues = prediction.get("validation_issues", [])
        if error:
            error = error if isinstance(error, str) and error.isidentifier() else "PredictionError"
        elif (
            prediction.get("review_status") not in tuple(ACTIVE_ROUTES)
            or prediction.get("hard_constraint_action") not in tuple(ACTION_VALUES)
            or not isinstance(signals, list) or not all(map(_structured_signal, signals))
            or not isinstance(issues, list) or "validation_issues" not in prediction
        ):
            error = "InvalidPrediction"
        else:
            actual = signals
    if not isinstance(issues, list):
        issues = []
    revision = sha256(case["original_feedback"].encode()).hexdigest()
    anchors_ok = sum(
        _valid_anchor(signal["evidence"][0], case, revision, assertion=True)
        and all(_valid_anchor(anchor, case, revision) for anchor in signal["evidence"][1:])
        for signal in actual
    )
    expected_route, expected_action = case["expected_review_status"], case["expected_hard_constraint_action"]
    actual_route, actual_action = prediction.get("review_status"), prediction.get("hard_constraint_action")
    route_correct = not error and actual_route == expected_route
    action_correct = not error and actual_action == expected_action
    no_mutation = not error and prediction.get("hard_constraints_mutated") is False
    feedback_preserved = not error and prediction.get("original_feedback") == case["original_feedback"]
    resolution_shape_ok = not error and (
        (_nonblank(prediction.get("clarification_question")) if actual_route == CLARIFY
         else prediction.get("clarification_question") is None)
        and (_nonblank(prediction.get("profile_fact_candidate")) if actual_route == PROFILE_FACT
             else prediction.get("profile_fact_candidate") is None)
    )
    literal_matched = _matched(expected, actual, _literal_identity)
    canonical_matched = _matched(expected, actual, _canonical_identity)
    return {
        "case_id": case["case_id"], "expected_route": expected_route, "actual_route": actual_route,
        "expected_hard_action": expected_action, "actual_hard_action": actual_action,
        "route_correct": bool(route_correct), "action_correct": bool(action_correct),
        "resolution_shape_ok": bool(resolution_shape_ok), "hard_rule_nonmutation_confirmed": bool(no_mutation),
        "original_feedback_preserved": bool(feedback_preserved),
        "literal_exact_case_match": bool(
            route_correct and action_correct and no_mutation and feedback_preserved and resolution_shape_ok
            and _matched(expected, actual, _exact_identity) == len(expected) == len(actual)
        ),
        "expected_signals": len(expected), "emitted_signals": len(actual),
        "literal_matches": literal_matched, "registered_identity_matches": canonical_matched,
        "registered_signals": sum(signal["feature_id"] is not None for signal in actual),
        "anchors_verified_signals": anchors_ok,
        "negative_career_proposals_requiring_review": [
            index for index, signal in enumerate(actual, start=1)
            if signal["dimension"] == "career_category" and signal["polarity"] == "negative"
        ],
        "validation_issues": issues,
        **({"execution_error": error} if error else {}),
    }


def evaluate_v3(suite, prediction):
    ids = {case["case_id"] for case in suite.cases}
    if not isinstance(prediction, Mapping) or set(prediction) != ids:
        raise ValueError("prediction IDs must match the entire fixture case set")
    cases = [_case_diagnostics(case, prediction[case["case_id"]]) for case in suite.cases]
    expected = sum(case["expected_signals"] for case in cases)
    emitted = sum(case["emitted_signals"] for case in cases)
    literal = sum(case["literal_matches"] for case in cases)
    canonical = sum(case["registered_identity_matches"] for case in cases)
    clear = [case for case in cases if case["expected_route"] == CLEAR]
    false_escalations = [case["case_id"] for case in clear if case["actual_route"] in (CLARIFY, PROFILE_FACT)]
    return {
        "score_status": "provisional_automation",
        "scenario_count": len(cases),
        "route_accuracy": _ratio(sum(case["route_correct"] for case in cases), len(cases)),
        "hard_action_accuracy": _ratio(sum(case["action_correct"] for case in cases), len(cases)),
        "routes_with_required_resolution_fields": _ratio(sum(case["resolution_shape_ok"] for case in cases), len(cases)),
        "clear_case_false_escalations": _ratio(len(false_escalations), len(clear)),
        "clear_case_false_escalation_case_ids": false_escalations,
        "literal_exact_case_match": _ratio(sum(case["literal_exact_case_match"] for case in cases), len(cases)),
        "literal_signal_precision": _ratio(literal, emitted),
        "literal_signal_recall": _ratio(literal, expected),
        "registered_identity_precision": _ratio(canonical, emitted),
        "registered_identity_recall": _ratio(canonical, expected),
        "registry_coverage": _ratio(sum(case["registered_signals"] for case in cases), emitted),
        "mechanical_evidence_grounding": _ratio(sum(case["anchors_verified_signals"] for case in cases), emitted),
        "negative_career_proposals_requiring_review": sum(
            len(case["negative_career_proposals_requiring_review"]) for case in cases
        ),
        "execution_errors": dict(Counter(case["execution_error"] for case in cases if "execution_error" in case)),
        "validation_issue_count": sum(len(case["validation_issues"]) for case in cases),
        "cases": cases,
    }


def _capture_pass(suite, provider, pass_number, directory):
    recorder = _RecordingProvider(provider)
    completed = 0

    def interpret(decision, feedback, context):
        return interpret_feedback_v3(decision, feedback, context, provider=recorder, hard_rules=suite.hard_rules)

    def on_case_complete(case_id):
        nonlocal completed
        recorder.finish_case(case_id)
        completed += 1
        if completed % 10 == 0 or completed == len(suite.cases):
            print(f"Pass {pass_number}/{PASS_COUNT} processed {completed}/{len(suite.cases)} cases.", file=sys.stderr)

    started = perf_counter()
    predictions = collect_predictions(suite, interpret, on_case_complete=on_case_complete)
    filenames = {"predictions": f"pass-{pass_number}.json", "proposals": f"pass-{pass_number}.proposals.json"}
    metadata = {
        "pass_number": pass_number, "capture_files": filenames, "capture_id": uuid4().hex,
        "predictions_sha256": _save_json(directory / filenames["predictions"], predictions),
        "proposals_sha256": _save_json(directory / filenames["proposals"], recorder.proposals),
        "elapsed_seconds": round(perf_counter() - started, 3),
    }
    print(f"Pass {pass_number}/{PASS_COUNT} saved raw and validated outputs.", file=sys.stderr)
    return predictions, metadata


def _live_configuration(args, suite, started_at):
    configuration = {
        "benchmark_version": BENCHMARK_VERSION, "taxonomy_version": TAXONOMY_VERSION,
        "suite_kind": args.suite, "suite_file": str(args.scenarios), "suite_version": suite.version,
        "suite_sha256": suite.sha256, "scenario_count": len(suite.cases), "hard_rules": suite.hard_rules,
        "high_risk_routing_case_ids": HIGH_RISK_CASE_IDS[args.suite],
        "hard_rules_sha256": _fingerprint(suite.hard_rules), "started_at_utc": started_at,
        "python_version": sys.version.split()[0],
        "inputs": {
            case["case_id"]: {
                "original_feedback_sha256": sha256(case["original_feedback"].encode()).hexdigest(),
                "job_context_sha256": _fingerprint(case["job_context"]),
                "case_input_sha256": _fingerprint({
                    "decision": case["decision"], "original_feedback": case["original_feedback"],
                    "job_context": case["job_context"], "hard_rules": suite.hard_rules,
                }),
            } for case in suite.cases
        },
    }
    return configuration


def _pass_stability(suite, predictions, reports):
    if len(predictions) != PASS_COUNT:
        return None
    not_verified = {
        case["case_id"] for report in reports for case in report["cases"]
        if case.get("execution_error") or case["validation_issues"]
    }
    literal_changes, registered_changes = [], []
    for case in suite.cases:
        case_id = case["case_id"]
        if case_id in not_verified:
            continue
        literal, registered = [], []
        for pred in predictions:
            result = pred[case_id]
            route = result["review_status"], result["hard_constraint_action"]
            signal_literals, signal_registry = Counter(), Counter()
            for signal in result["interpretations"]:
                exact = _exact_identity(signal, reference=False)
                condition = signal.get("condition")
                typed_condition = (condition.get("kind"), condition.get("value")) if condition else None
                literal_key = (*exact[:6], typed_condition, exact[-1])
                registry_key = _canonical_identity(signal, reference=False)
                signal_literals[literal_key] += 1
                signal_registry[("candidate", literal_key) if registry_key is None else (
                    "registered", *registry_key[:-1], typed_condition, signal["strength"],
                )] += 1
            literal.append((route, signal_literals))
            registered.append((route, signal_registry))
        if literal[0] != literal[1]:
            literal_changes.append(case_id)
        if registered[0] != registered[1]:
            registered_changes.append(case_id)
    total = len(suite.cases)
    return {
        "score_status": "provisional_automation",
        "literal_unchanged": _ratio(total - len(not_verified) - len(literal_changes), total),
        "registered_identity_unchanged": _ratio(total - len(not_verified) - len(registered_changes), total),
        "literal_changed_case_ids": literal_changes, "registered_identity_changed_case_ids": registered_changes,
        "unverified_case_ids": sorted(not_verified),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenarios", type=Path)
    parser.add_argument("--suite", choices=SUITE_COUNTS, default="gold")
    parser.add_argument("--model")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--runs", type=int, choices=[PASS_COUNT], default=PASS_COUNT)
    parser.add_argument("--save-predictions", type=Path, help="New directory for required live captures")
    parser.add_argument("--predictions", type=Path, action="append", help="Replay a saved validated pass")
    parser.add_argument("--adjudications", type=Path, action="append", help="Reviewer verdicts for each replayed pass")
    args = parser.parse_args(argv)
    if args.adjudications and (not args.predictions or len(args.adjudications) != len(args.predictions)):
        parser.error("provide one --adjudications file per --predictions file")
    if args.predictions and (args.model or args.temperature is not None or args.save_predictions):
        parser.error("--model, --temperature and --save-predictions apply to live evaluation only")
    if args.predictions and len({path.resolve() for path in args.predictions}) != len(args.predictions):
        parser.error("each --predictions file must identify a distinct pass")
    if not args.predictions and not args.save_predictions:
        parser.error("live evaluation requires --save-predictions")

    started = perf_counter()
    started_at = datetime.now(UTC).isoformat(timespec="seconds")
    reports, all_predictions = [], []
    try:
        suite = load_v3_suite(args.scenarios, args.suite)
        configuration = _live_configuration(args, suite, started_at)
        if args.predictions:
            source = {"mode": "replay", "passes": len(args.predictions)}
            for number, path in enumerate(args.predictions, start=1):
                data, predictions = _read_json(path)
                prediction_hash = sha256(data).hexdigest()
                report = {**evaluate_v3(suite, predictions), "pass_number": number, "predictions_sha256": prediction_hash}
                if args.adjudications:
                    from .feedback_adjudication_v3 import adjudicate

                    verdict_data, verdicts = _read_json(args.adjudications[number - 1])
                    report["adjudication"] = adjudicate(
                        suite, predictions, verdicts, predictions_sha256=prediction_hash,
                        high_risk_case_ids=HIGH_RISK_CASE_IDS[args.suite],
                    )
                    report["adjudications_sha256"] = sha256(verdict_data).hexdigest()
                reports.append(report)
                all_predictions.append(predictions)
        else:
            first_provider = OpenAIFeedbackProviderV3(args.model, temperature=args.temperature)
            source = {
                "mode": "live", "requested_model": first_provider.model, "temperature_override": args.temperature,
                "prompt_version": extraction.PROMPT_VERSION, "passes": PASS_COUNT,
                "extraction_source_sha256": sha256(Path(extraction.__file__).read_bytes()).hexdigest(),
                "instructions_sha256": sha256(extraction._INSTRUCTIONS.encode()).hexdigest(),
                "proposal_schema_sha256": _fingerprint(extraction._PROPOSAL_SCHEMA),
            }
            args.save_predictions.mkdir(parents=True)
            configuration_hash = _save_json(args.save_predictions / "configuration.json", {
                **configuration, "evaluation_source": source,
            })
            for number in range(1, PASS_COUNT + 1):
                provider = (first_provider if number == 1
                            else OpenAIFeedbackProviderV3(first_provider.model, temperature=args.temperature))
                predictions, metadata = _capture_pass(suite, provider, number, args.save_predictions)
                reports.append({**evaluate_v3(suite, predictions), **metadata})
                all_predictions.append(predictions)
            configuration["capture_configuration_sha256"] = configuration_hash
    except (ValueError, OSError, FeedbackProviderError) as error:
        print(f"Benchmark could not complete. {error}", file=sys.stderr)
        return 2

    completed = len(reports) == PASS_COUNT and all(not report["execution_errors"] for report in reports)
    repeated = completed and all(not report["validation_issue_count"] for report in reports)
    adjudicated = bool(args.adjudications)
    passed = repeated and adjudicated and all(report["adjudication"]["quality_gates_passed"] for report in reports)
    result = {
        "configuration": configuration, "evaluation_source": source, "runs": reports,
        "elapsed_seconds": round(perf_counter() - started, 3), "two_complete_passes": completed,
        "repeated_pass_requirement_met": repeated, "automated_stability": _pass_stability(suite, all_predictions, reports),
        "score_status": "adjudicated" if adjudicated else "provisional_automation",
        "quality_gates_passed": passed,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return int(not passed)


if __name__ == "__main__":
    sys.exit(main())
