"""Compare two deterministic review paths using shared one-call proposals."""

import argparse
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import sys
from time import perf_counter

from . import feedback_posting_verification_repair_v3, feedback_review_only_trial_v3, feedback_travel_count_repair_v3
from .feedback import FeedbackProviderError, _model_input
from .feedback_evaluation import _read_json, _save_json
from .feedback_evaluation_v3 import _fingerprint, evaluate_v3, load_v3_suite
from .feedback_extraction_trial_v3 import KNOWN_FIXTURES, _arm_report
from .feedback_extraction_v3 import PROMPT_VERSION, OpenAIFeedbackProviderV3
from .feedback_review_only_trial_v3 import (
    ARMS, INSTRUCTIONS_SHA256, MODEL, PASSES, RESPONSE_SCHEMA_NAME, SCHEMA_SHA256, TEMPERATURE, _SOURCE_MODULES,
    _review_burden,
)
from .feedback_validation_repair_trial_v3 import _repaired_prediction


DEFAULT_SUITE = Path("benchmarks/feedback/review_only_followup_holdout_v3.json")
CASE_IDS = {f"RF3-{number:03d}" for number in range(1, 13)}


def _load_cases(suite_path):
    suite = load_v3_suite(suite_path, "holdout")
    data, fixture = _read_json(suite_path)
    if sha256(data).hexdigest() != suite.sha256:
        raise ValueError("the follow-up fixture changed while loading")
    ids = {case["case_id"] for case in suite.cases}
    if ids != CASE_IDS:
        raise ValueError("the follow-up fixture must contain RF3-001 through RF3-012")
    gold_path = KNOWN_FIXTURES["gold"]
    gold = load_v3_suite(gold_path, "gold")
    if suite.hard_rules != gold.hard_rules:
        raise ValueError("the follow-up fixture must use the approved gold benchmark hard rules")
    high_risk = fixture.get("high_risk_case_ids")
    if (not isinstance(high_risk, list) or not high_risk
            or any(not isinstance(case_id, str) or case_id not in ids for case_id in high_risk)
            or len(set(high_risk)) != len(high_risk)):
        raise ValueError("the follow-up fixture must predeclare valid high-risk routing case IDs")
    fixtures = {kind: {"file": str(path), "version": source.version, "sha256": source.sha256}
                for kind, path, source in (("fresh", suite_path, suite), ("gold", gold_path, gold))}
    return suite, high_risk, fixtures


def _planned_requests(cases):
    return [{"pass_number": number, "case_id": case["case_id"], "stage": "classifier"}
            for number in PASSES for case in cases]


def _followup_prediction(case, rules, raw, metadata):
    """Apply the two scoped repairs after the earlier review-only candidate."""
    result, repairs = _repaired_prediction(case, rules, raw, metadata)
    result, verification = feedback_posting_verification_repair_v3.repair_posting_verification(result)
    result, travel_counts = feedback_travel_count_repair_v3.repair_travel_count(result)
    return result, {
        **repairs, "condition_recoveries": result.get("condition_recoveries", []),
        "posting_verification_repair": verification, "travel_count_repairs": travel_counts,
    }


def _run_case(case, rules, provider, scheduled, trace):
    decision, original, context = (case[field] for field in ("decision", "original_feedback", "job_context"))
    source_hash = _fingerprint(_model_input(decision, original, context, rules))
    event = {
        **scheduled, "request_number": len(trace) + 1, "input_sha256": source_hash,
        "origin_input_sha256": source_hash, "instructions_sha256": INSTRUCTIONS_SHA256,
        "response_schema_sha256": SCHEMA_SHA256, "validations": {},
    }
    trace.append(event)
    started = perf_counter()
    try:
        raw = provider.propose(decision, original, context, rules)
    except FeedbackProviderError as error:
        error_type = type(error).__name__
        event.update(status="error", error_type=error_type,
                     validations={arm: {"status": "skipped", "elapsed_seconds": None} for arm in ARMS})
        outcome = {"evaluation_error": error_type}
        return None, {arm: dict(outcome) for arm in ARMS}, outcome
    finally:
        event["elapsed_seconds"] = round(perf_counter() - started, 6)

    event.update(status="completed", response_sha256=_fingerprint(raw))
    metadata = {"model": MODEL, "recover_explicit_conditions": True}
    predictions = {}
    for arm, validator in (("baseline", _repaired_prediction), ("candidate", _followup_prediction)):
        started = perf_counter()
        try:
            outcome, repairs = validator(case, rules, raw, metadata)
        except FeedbackProviderError as error:
            error_type = type(error).__name__
            outcome = repairs = {"evaluation_error": error_type}
            validation = {"status": "error", "error_type": error_type}
        else:
            validation = {"status": "completed", "validated_sha256": _fingerprint(outcome)}
        validation["elapsed_seconds"] = round(perf_counter() - started, 6)
        event["validations"][arm] = validation
        predictions[arm] = outcome
    return raw, predictions, repairs


def _capture_pass(output, number, schedule, suite, provider, trace):
    by_id = {case["case_id"]: case for case in suite.cases}
    proposals, repair_records = {}, {}
    predictions = {arm: {} for arm in ARMS}
    trace_start = len(trace)
    for entry in schedule:
        case_id = entry["case_id"]
        proposals[case_id], outcomes, repair_records[case_id] = _run_case(
            by_id[case_id], suite.hard_rules, provider, entry, trace,
        )
        for arm, outcome in outcomes.items():
            predictions[arm][case_id] = outcome
        print(f"Captured follow-up pass {number} {case_id}.", file=sys.stderr)
    directory = output / f"pass-{number}"
    directory.mkdir()
    captured = trace[trace_start:]
    arms = {arm: {
        **_arm_report(directory, arm, suite.cases, proposals, predictions[arm]),
        "automated_metrics": evaluate_v3(suite, predictions[arm]),
        "review_burden": _review_burden(predictions[arm]),
        "validation_elapsed_seconds": round(sum(row["validations"][arm]["elapsed_seconds"] or 0 for row in captured), 6),
    } for arm in ARMS}
    repairs_file = "candidate.repairs.json"
    return {
        "pass_number": number, "directory": directory.name, "arms": arms,
        "model_elapsed_seconds": round(sum(row["elapsed_seconds"] for row in captured), 6),
        "repairs_file": repairs_file, "repairs_sha256": _save_json(directory / repairs_file, repair_records),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--output", type=Path, required=True, help="New directory for both shared-proposal passes")
    args = parser.parse_args(argv)
    try:
        suite, high_risk, fixtures = _load_cases(args.suite)
        provider = OpenAIFeedbackProviderV3(MODEL, temperature=TEMPERATURE)
        planned = _planned_requests(suite.cases)
        source_modules = (*_SOURCE_MODULES, feedback_review_only_trial_v3,
                          feedback_posting_verification_repair_v3, feedback_travel_count_repair_v3)
        args.output.mkdir(parents=True)
        configuration_hash = _save_json(args.output / "configuration.json", {
            "mode": "review_only_followup_trial", "model": MODEL, "temperature": TEMPERATURE,
            "python_version": sys.version.split()[0], "validator_prompt_version_field": PROMPT_VERSION,
            "started_at_utc": datetime.now(UTC).isoformat(timespec="seconds"), "fixtures": fixtures,
            "expected_requests": len(planned), "planned_requests": planned, "high_risk_case_ids": high_risk,
            "shared_raw_responses": True,
            "case_input_sha256": {case["case_id"]: _fingerprint(_model_input(
                case["decision"], case["original_feedback"], case["job_context"], suite.hard_rules,
            )) for case in suite.cases},
            "hard_rules_sha256": _fingerprint(suite.hard_rules), "instructions_sha256": INSTRUCTIONS_SHA256,
            "response_schema_name": RESPONSE_SCHEMA_NAME, "response_schema_sha256": SCHEMA_SHA256,
            "arms": {"baseline": {"prior_review_only_candidate": True}, "candidate": {
                "prior_review_only_candidate": True, "repair_posting_verification_question": True,
                "repair_travel_count": True,
            }},
            "source_sha256": {path.name: sha256(path.read_bytes()).hexdigest()
                              for path in (Path(__file__), *(Path(module.__file__) for module in source_modules))},
        })
        trace = []
        passes = [_capture_pass(args.output, number, [entry for entry in planned if entry["pass_number"] == number],
                                suite, provider, trace) for number in PASSES]
        request_errors = sum(row["status"] == "error" for row in trace)
        _save_json(args.output / "report.json", {
            "score_status": "automated_diagnostics_only", "configuration_sha256": configuration_hash,
            "request_trace_file": "request-trace.json",
            "request_trace_sha256": _save_json(args.output / "request-trace.json", trace),
            "requests_attempted": len(trace), "requests_completed": len(trace) - request_errors,
            "request_errors": request_errors, "passes": passes,
        })
    except (OSError, ValueError, FeedbackProviderError) as error:
        print(f"Review-only follow-up could not complete. {error}", file=sys.stderr)
        return 2
    case_errors = any(arm["execution_errors"] for run in passes for arm in run["arms"].values())
    return int(bool(case_errors or request_errors or len(trace) != len(planned)))


if __name__ == "__main__":
    sys.exit(main())
