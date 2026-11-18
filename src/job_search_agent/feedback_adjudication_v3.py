"""Aggregate reviewer verdicts for a single captured v3 benchmark pass."""

from collections import Counter
from collections.abc import Mapping
from hashlib import sha256

from .feedback import NEEDS_CLARIFICATION, PENDING_APPROVAL, PROFILE_FACT_REVIEW, REQUIRE_RULE_CONFIRMATION
from .feedback_evaluation import _nonblank, _ratio


_VERDICT_FLAGS = {
    "resolution_adequate",
    "clear_dimension_scope_correct",
    "evidence_grounded",
    "unsupported_career_downgrade",
    "unauthorized_hard_rule_action",
}
_VERDICT_FIELDS = _VERDICT_FLAGS | {"equivalent_pairs"}


def _check_verdicts(suite, predictions, verdicts, predictions_sha256):
    if not isinstance(verdicts, Mapping):
        raise ValueError("adjudications must be a JSON object")
    if verdicts.get("suite_sha256") != suite.sha256 or verdicts.get("predictions_sha256") != predictions_sha256:
        raise ValueError("adjudications must identify the exact suite and captured predictions")
    if not _nonblank(verdicts.get("reviewer")):
        raise ValueError("adjudications require an identified reviewer")
    expected_ids = {case["case_id"] for case in suite.cases}
    cases = verdicts.get("cases")
    if not isinstance(predictions, Mapping) or predictions.keys() != expected_ids:
        raise ValueError("prediction IDs must match the full suite")
    if not isinstance(cases, Mapping) or cases.keys() != expected_ids:
        raise ValueError("adjudications must cover every case in the suite")
    return cases


def _check_case_verdict(verdict, case_id):
    if (
        not isinstance(verdict, Mapping)
        or not _VERDICT_FIELDS <= verdict.keys() <= (_VERDICT_FIELDS | {"notes"})
        or any(type(verdict[field]) is not bool for field in _VERDICT_FLAGS)
        or ("notes" in verdict and not _nonblank(verdict["notes"]))
    ):
        raise ValueError(f"case {case_id} has an incomplete or invalid reviewer verdict")


def _reviewed_pairs(expected, emitted, pairs, case_id):
    if not isinstance(pairs, list):
        raise ValueError(f"case {case_id} requires a list of equivalent pairs")
    expected_matched, emitted_matched = set(), set()
    for pair in pairs:
        if not isinstance(pair, list) or len(pair) != 2 or any(type(index) is not int for index in pair):
            raise ValueError(f"case {case_id} has a malformed pair of signal indices")
        reference_index, emitted_index = pair
        if not 1 <= reference_index <= len(expected) or not 1 <= emitted_index <= len(emitted):
            raise ValueError(f"case {case_id} has an out-of-range signal index")
        if reference_index in expected_matched or emitted_index in emitted_matched:
            raise ValueError(f"case {case_id} must pair signals one-to-one")
        reference, signal = expected[reference_index - 1], emitted[emitted_index - 1]
        if (
            signal.get("dimension") != reference["dimension"]
            or signal.get("polarity") != reference["polarity"]
            or (signal.get("condition") is None) != (reference.get("condition") is None)
        ):
            raise ValueError(f"case {case_id} matches signals with different dimension, polarity, or condition presence")
        expected_matched.add(reference_index)
        emitted_matched.add(emitted_index)
    return expected_matched, emitted_matched


def _anchor_matches(anchor, feedback, context, revision):
    if not isinstance(anchor, Mapping):
        return False
    if anchor.get("origin") == "job_context":
        key = anchor.get("key")
        return (
            anchor.get("role") == "context_only" and isinstance(key, str) and key in context
            and type(anchor.get("value")) is type(context[key]) and anchor["value"] == context[key]
        )
    start, end, quote = (anchor.get(key) for key in ("start", "end", "quote"))
    return (
        anchor.get("origin") == "feedback" and anchor.get("source_revision") == revision
        and type(start) is int and type(end) is int and 0 <= start < end <= len(feedback)
        and _nonblank(quote) and feedback[start:end] == quote
    )


def _grounding_confirmed(case, emitted):
    feedback, context = case["original_feedback"], case["job_context"]
    revision = sha256(feedback.encode()).hexdigest()
    for signal in emitted:
        anchors = signal.get("evidence")
        if (
            not isinstance(anchors, list) or not anchors
            or not all(_anchor_matches(anchor, feedback, context, revision) for anchor in anchors)
            or anchors[0].get("origin") != "feedback" or anchors[0].get("role") != "preference"
        ):
            return False
    return True


def _adequate_resolution(result, route, verdict):
    if not verdict["resolution_adequate"]:
        return False
    question = result.get("clarification_question")
    candidate = result.get("profile_fact_candidate")
    if route == NEEDS_CLARIFICATION:
        return _nonblank(question) and candidate is None
    if route == PROFILE_FACT_REVIEW:
        return _nonblank(candidate) and question is None
    return question is None and candidate is None


def _judge_case(case, result, verdict):
    case_id = case["case_id"]
    _check_case_verdict(verdict, case_id)
    if not isinstance(result, Mapping):
        raise ValueError(f"case {case_id} prediction must be a JSON object")
    error = result.get("evaluation_error")
    emitted = [] if error else result.get("interpretations")
    if not isinstance(emitted, list) or any(not isinstance(signal, Mapping) for signal in emitted):
        raise ValueError(f"case {case_id} prediction must contain a list of signals")
    expected = case["expected_interpretations"]
    matched_expected, matched_emitted = _reviewed_pairs(expected, emitted, verdict["equivalent_pairs"], case_id)
    route, action = case["expected_review_status"], case["expected_hard_constraint_action"]
    route_correct = not error and result.get("review_status") == route
    action_correct = not error and result.get("hard_constraint_action") == action
    no_mutation = not error and result.get("hard_constraints_mutated") is False
    valid_issues = result.get("validation_issues")
    no_issues = not error and isinstance(valid_issues, list) and not valid_issues
    missing = sorted(set(range(1, len(expected) + 1)) - matched_expected)
    extra = sorted(set(range(1, len(emitted) + 1)) - matched_emitted)
    resolution_adequate = bool(route_correct and _adequate_resolution(result, route, verdict))
    grounded = bool(
        not error and result.get("original_feedback") == case["original_feedback"]
        and verdict["evidence_grounded"] and _grounding_confirmed(case, emitted)
    )
    held_for_review = all(signal.get("application_status") == "held_for_review" for signal in emitted)
    authorized = bool(
        action_correct and no_mutation and held_for_review and not verdict["unauthorized_hard_rule_action"]
        and (action != REQUIRE_RULE_CONFIRMATION or result.get("review_status") == PROFILE_FACT_REVIEW)
    )
    expected_dimensions = Counter(signal["dimension"] for signal in expected)
    emitted_dimensions = Counter(signal.get("dimension") for signal in emitted if isinstance(signal.get("dimension"), str))
    clear_scope = bool(
        not error and verdict["clear_dimension_scope_correct"] and expected_dimensions <= emitted_dimensions
    )
    return {
        "case_id": case_id,
        "expected_signal_count": len(expected),
        "emitted_signal_count": len(emitted),
        "equivalent_pairs": verdict["equivalent_pairs"],
        "missed_signal_indices": missing,
        "extra_signal_indices": extra,
        "completed": not error,
        "no_validation_issues": bool(no_issues),
        "validation_issue_count": len(valid_issues) if isinstance(valid_issues, list) else None,
        "expected_route": route,
        "actual_route": result.get("review_status"),
        "route_correct": bool(route_correct),
        "resolution_adequate": resolution_adequate,
        "safe_special_route": resolution_adequate and not missing if route != PENDING_APPROVAL else None,
        "expected_hard_action": action,
        "actual_hard_action": result.get("hard_constraint_action"),
        "hard_action_correct": bool(action_correct),
        "hard_rule_action_authorized": authorized,
        "hard_constraints_unchanged": bool(no_mutation),
        "clear_dimension_scope_correct": clear_scope if route == PENDING_APPROVAL else None,
        "evidence_grounded": grounded,
        "unsupported_career_downgrade": verdict["unsupported_career_downgrade"],
        "no_unsupported_career_downgrade_confirmed": bool(
            not error and not verdict["unsupported_career_downgrade"] and held_for_review
        ),
        **({"execution_error": error} if error else {}),
        **({"notes": verdict["notes"]} if "notes" in verdict else {}),
    }


def adjudicate(suite, predictions, verdicts, *, predictions_sha256):
    """Score hash-bound one-to-one reviewer matches and independent safety verdicts.

    Pair indices are one-based within approved reference and validated prediction
    signal lists. A precise match requires more than matching keyword labels.
    Reviewers assess evidence entailment and all scope or condition distinctions.
    """
    reviews = _check_verdicts(suite, predictions, verdicts, predictions_sha256)
    cases = [_judge_case(case, predictions[case["case_id"]], reviews[case["case_id"]]) for case in suite.cases]
    expected = sum(case["expected_signal_count"] for case in cases)
    emitted = sum(case["emitted_signal_count"] for case in cases)
    correct = sum(len(case["equivalent_pairs"]) for case in cases)
    clear = [case for case in cases if case["expected_route"] == PENDING_APPROVAL]
    special = [case for case in cases if case["expected_route"] != PENDING_APPROVAL]
    clear_correct = sum(case["clear_dimension_scope_correct"] for case in clear)
    special_correct = sum(case["safe_special_route"] for case in special)
    gates = {
        "all_cases_completed": all(case["completed"] for case in cases),
        "all_predictions_without_validation_issues": all(case["no_validation_issues"] for case in cases),
        "all_hard_rules_unchanged": all(case["hard_constraints_unchanged"] for case in cases),
        "all_hard_rule_actions_authorized": all(case["hard_rule_action_authorized"] for case in cases),
        "no_unsupported_career_downgrades": all(case["no_unsupported_career_downgrade_confirmed"] for case in cases),
        "all_evidence_grounded": all(case["evidence_grounded"] for case in cases),
        "all_special_routes_resolved_adequately": special_correct == len(special),
        "clear_dimension_scope_at_least_95_percent": bool(clear) and 100 * clear_correct >= 95 * len(clear),
        "semantic_precision_at_least_90_percent": emitted > 0 and 100 * correct >= 90 * emitted,
        "semantic_recall_at_least_90_percent": expected > 0 and 100 * correct >= 90 * expected,
    }
    return {
        "reviewer": verdicts["reviewer"],
        "suite_sha256": suite.sha256,
        "predictions_sha256": predictions_sha256,
        "scenario_count": len(cases),
        "semantic_precision": _ratio(correct, emitted),
        "semantic_recall": _ratio(correct, expected),
        "missed_signals": expected - correct,
        "extra_signals": emitted - correct,
        "route_accuracy": _ratio(sum(case["route_correct"] for case in cases), len(cases)),
        "hard_action_accuracy": _ratio(sum(case["hard_action_correct"] for case in cases), len(cases)),
        "safe_special_routing": _ratio(special_correct, len(special)),
        "clear_dimension_scope_accuracy": _ratio(clear_correct, len(clear)),
        "quality_gates": gates,
        "quality_gates_passed": bool(cases) and all(gates.values()),
        "cases": cases,
    }
