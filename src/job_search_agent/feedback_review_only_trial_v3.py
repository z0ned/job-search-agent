"""Compare one-call v3 review pipelines on a fresh paired holdout."""

import argparse
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import sys
from time import perf_counter

from . import (
    feedback, feedback_autonomy_review_v3, feedback_conditions_v3, feedback_employer_context_repair_v3,
    feedback_enthusiasm_scope_v3, feedback_evidence_checks_v3, feedback_extraction_v3, feedback_intensity_repair_v3,
    feedback_replay_v3, feedback_rules_v3, feedback_taxonomy, feedback_v3, feedback_validation_repair_trial_v3,
)
from .feedback import NEEDS_CLARIFICATION, PENDING_APPROVAL, PROFILE_FACT_REVIEW, FeedbackProviderError, _model_input
from .feedback_evaluation import _read_json, _save_json
from .feedback_evaluation_v3 import _fingerprint, evaluate_v3, load_v3_suite
from .feedback_extraction_trial_v3 import KNOWN_FIXTURES, _arm_report
from .feedback_extraction_v3 import PROMPT_VERSION, OpenAIFeedbackProviderV3, _INSTRUCTIONS, _PROPOSAL_SCHEMA
from .feedback_separate_extraction_trial_v3 import MODEL, PASSES, TEMPERATURE
from .feedback_validation_repair_trial_v3 import _repaired_prediction, _revalidate


DEFAULT_SUITE = Path("benchmarks/feedback/review_only_holdout_v3.json")
CASE_IDS = {f"RO3-{number:03d}" for number in range(1, 13)}
ARMS = ("baseline", "candidate")
RESPONSE_SCHEMA_NAME = "feedback_extraction_v3"
INSTRUCTIONS_SHA256 = sha256(_INSTRUCTIONS.encode()).hexdigest()
SCHEMA_SHA256 = _fingerprint(_PROPOSAL_SCHEMA)
_SOURCE_MODULES = (
    feedback, feedback_extraction_v3, feedback_v3, feedback_rules_v3, feedback_taxonomy, feedback_conditions_v3,
    feedback_evidence_checks_v3, feedback_replay_v3, feedback_validation_repair_trial_v3,
    feedback_employer_context_repair_v3, feedback_intensity_repair_v3, feedback_autonomy_review_v3,
    feedback_enthusiasm_scope_v3,
)


def _load_cases(suite_path):
    suite = load_v3_suite(suite_path, "holdout")
    data, fixture = _read_json(suite_path)
    if sha256(data).hexdigest() != suite.sha256:
        raise ValueError("the fresh fixture changed while loading")
    ids = {case["case_id"] for case in suite.cases}
    if ids != CASE_IDS:
        raise ValueError("the fresh fixture must contain RO3-001 through RO3-012")
    gold_path = KNOWN_FIXTURES["gold"]
    gold = load_v3_suite(gold_path, "gold")
    if suite.hard_rules != gold.hard_rules:
        raise ValueError("the fresh fixture must use the approved gold benchmark hard rules")
    high_risk = fixture.get("high_risk_case_ids")
    if (not isinstance(high_risk, list) or not high_risk
            or any(not isinstance(case_id, str) or case_id not in ids for case_id in high_risk)
            or len(set(high_risk)) != len(high_risk)):
        raise ValueError("the fresh fixture must predeclare valid high-risk routing case IDs")
    fixtures = {kind: {"file": str(path), "version": source.version, "sha256": source.sha256}
                for kind, path, source in (("fresh", suite_path, suite), ("gold", gold_path, gold))}
    return suite, high_risk, fixtures


def _planned_requests(cases):
    return [{"pass_number": number, "case_id": case["case_id"], "arm": arm, "stage": "classifier"}
            for number in PASSES for index, case in enumerate(cases)
            for arm in (ARMS if (index + number) % 2 else ARMS[::-1])]


def _run_case(case, rules, provider, scheduled, trace):
    decision, original, context = (case[field] for field in ("decision", "original_feedback", "job_context"))
    source_hash = _fingerprint(_model_input(decision, original, context, rules))
    event = {
        **scheduled, "request_number": len(trace) + 1, "input_sha256": source_hash,
        "origin_input_sha256": source_hash, "instructions_sha256": INSTRUCTIONS_SHA256,
        "response_schema_sha256": SCHEMA_SHA256,
    }
    trace.append(event)
    started = perf_counter()
    try:
        raw = provider.propose(decision, original, context, rules)
    except FeedbackProviderError as error:
        event.update(status="error", error_type=type(error).__name__, validation_seconds=None)
        return None, {"evaluation_error": type(error).__name__}, {"evaluation_error": type(error).__name__}
    finally:
        event["elapsed_seconds"] = round(perf_counter() - started, 6)

    event.update(status="completed", response_sha256=_fingerprint(raw))
    candidate = scheduled["arm"] == "candidate"
    metadata = {"model": MODEL, "recover_explicit_conditions": candidate}
    started = perf_counter()
    try:
        if candidate:
            validated, repairs = _repaired_prediction(case, rules, raw, metadata)
            repairs["condition_recoveries"] = validated["condition_recoveries"]
        else:
            validated, repairs = _revalidate(case, rules, raw, metadata), {}
    except FeedbackProviderError as error:
        event.update(validation_status="error", validation_error=type(error).__name__)
        validated = repairs = {"evaluation_error": type(error).__name__}
    else:
        event.update(validation_status="completed", validated_sha256=_fingerprint(validated))
    finally:
        event["validation_seconds"] = round(perf_counter() - started, 6)
    return raw, validated, repairs


def _review_burden(predictions):
    ordinary, clarification, provenance, issues, findings, blocking = ([] for _ in range(6))
    for case_id, record in predictions.items():
        route = record.get("review_status")
        if route == PENDING_APPROVAL:
            ordinary.append(case_id)
        elif route == NEEDS_CLARIFICATION:
            clarification.append(case_id)
        elif route == PROFILE_FACT_REVIEW:
            provenance.append(case_id)
        if record.get("validation_issues"):
            issues.append(case_id)
        if evidence := record.get("evidence_findings"):
            findings.append(case_id)
            if any(item.get("severity") == "blocking" for item in evidence):
                blocking.append(case_id)
    additional = set(clarification) | set(provenance) | set(issues) | set(findings)
    return {
        "ordinary_approval_case_ids": ordinary, "clarification_case_ids": clarification,
        "profile_fact_review_case_ids": provenance, "validation_issue_case_ids": issues,
        "evidence_finding_case_ids": findings, "blocking_evidence_finding_case_ids": blocking,
        "additional_review_cases": len(additional), "additional_review_case_ids": sorted(additional),
    }


def _capture_pass(output, number, schedule, suite, provider, trace):
    by_id = {case["case_id"]: case for case in suite.cases}
    proposals, predictions = ({arm: {} for arm in ARMS} for _ in range(2))
    repair_records = {}
    trace_start = len(trace)
    for entry in schedule:
        arm, case_id = entry["arm"], entry["case_id"]
        proposals[arm][case_id], predictions[arm][case_id], repairs = _run_case(
            by_id[case_id], suite.hard_rules, provider, entry, trace,
        )
        if arm == "candidate":
            repair_records[case_id] = repairs
        print(f"Captured review-only pass {number} {arm} {case_id}.", file=sys.stderr)
    directory = output / f"pass-{number}"
    directory.mkdir()
    arms = {}
    for arm in ARMS:
        captured = [row for row in trace[trace_start:] if row["arm"] == arm]
        arms[arm] = {
            **_arm_report(directory, arm, suite.cases, proposals[arm], predictions[arm]),
            "automated_metrics": evaluate_v3(suite, predictions[arm]),
            "review_burden": _review_burden(predictions[arm]),
            "model_elapsed_seconds": round(sum(row["elapsed_seconds"] for row in captured), 6),
            "validation_elapsed_seconds": round(sum(row["validation_seconds"] or 0 for row in captured), 6),
        }
    repairs_file = "candidate.repairs.json"
    return {
        "pass_number": number, "directory": directory.name, "arms": arms, "repairs_file": repairs_file,
        "repairs_sha256": _save_json(directory / repairs_file, repair_records),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--output", type=Path, required=True, help="New directory for both paired passes")
    args = parser.parse_args(argv)
    try:
        suite, high_risk, fixtures = _load_cases(args.suite)
        provider = OpenAIFeedbackProviderV3(MODEL, temperature=TEMPERATURE)
        planned = _planned_requests(suite.cases)
        args.output.mkdir(parents=True)
        configuration_hash = _save_json(args.output / "configuration.json", {
            "mode": "review_only_end_to_end_trial", "model": MODEL, "temperature": TEMPERATURE,
            "python_version": sys.version.split()[0], "validator_prompt_version_field": PROMPT_VERSION,
            "started_at_utc": datetime.now(UTC).isoformat(timespec="seconds"), "fixtures": fixtures,
            "expected_requests": len(planned), "planned_requests": planned, "high_risk_case_ids": high_risk,
            "case_input_sha256": {case["case_id"]: _fingerprint(_model_input(
                case["decision"], case["original_feedback"], case["job_context"], suite.hard_rules,
            )) for case in suite.cases},
            "hard_rules_sha256": _fingerprint(suite.hard_rules), "instructions_sha256": INSTRUCTIONS_SHA256,
            "response_schema_name": RESPONSE_SCHEMA_NAME, "response_schema_sha256": SCHEMA_SHA256,
            "arms": {"baseline": {"recover_explicit_conditions": False}, "candidate": {
                "recover_explicit_conditions": True, "repair_grounded_employer_context": True,
                "coalesce_anchored_duplicate_intensity": True, "read_only_scope_findings": True,
            }},
            "source_sha256": {path.name: sha256(path.read_bytes()).hexdigest()
                              for path in (Path(__file__), *(Path(module.__file__) for module in _SOURCE_MODULES))},
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
        print(f"Review-only comparison could not complete. {error}", file=sys.stderr)
        return 2
    case_errors = any(arm["execution_errors"] for run in passes for arm in run["arms"].values())
    return int(bool(case_errors or request_errors or len(trace) != len(planned)))


if __name__ == "__main__":
    sys.exit(main())
