"""Verify the two review-only repairs using the 48 saved model replies."""

import argparse
from hashlib import sha256
from pathlib import Path
import sys

from .feedback import FeedbackProviderError, _model_input
from .feedback_evaluation import _save_json
from .feedback_evaluation_v3 import _fingerprint
from .feedback_replay_v3 import _read_archive_json
from .feedback_review_only_followup_trial_v3 import _followup_prediction
from .feedback_review_only_trial_v3 import ARMS, DEFAULT_SUITE, _load_cases
from .feedback_validation_repair_trial_v3 import _repaired_prediction, _revalidate


DEFAULT_ARCHIVE = Path("benchmarks/feedback/live_v3_review_only_trial")


def _compare(case, rules, raw, archived, arm, model):
    options = {"model": model, "recover_explicit_conditions": True}
    before, _ = _repaired_prediction(case, rules, raw, options)
    original = (before if arm == "candidate" else _revalidate(
        case, rules, raw, {**options, "recover_explicit_conditions": False},
    ))
    if original != archived:
        raise ValueError(f"the saved {arm} validation could not be reproduced")
    after, repairs = _followup_prediction(case, rules, raw, options)
    old_signals = before["interpretations"]
    new_signals = after["interpretations"]
    signature_fields = ("dimension", "polarity", "clause_index", "display_label", "condition", "application_status")
    old_keys = [tuple(signal[field] for field in signature_fields) for signal in old_signals]
    new_keys = [tuple(signal[field] for field in signature_fields) for signal in new_signals]
    if (old_keys != new_keys or any(signal["application_status"] != "held_for_review" for signal in new_signals)
            or after["hard_constraints_mutated"] is not False or any(before[field] != after[field] for field in (
                "review_status", "hard_constraint_action", "profile_fact_candidate", "eligibility_violation", "validation_issues",
            ))):
        raise ValueError("the repairs changed routes, rule actions, validation checks, or held signal identity")
    return {"repairs": repairs, "changed_fields": {
        key: {"before": before.get(key, []), "after": after.get(key, [])}
        for key in sorted(before.keys() | after.keys()) if before.get(key, []) != after.get(key, [])
    }}


def replay(archive):
    """Verify immutable capture hashes, reproduce the old records, and compare the two repairs."""
    report, report_hash = _read_archive_json(archive / "report.json")
    configuration, config_hash = _read_archive_json(archive / "configuration.json", report["configuration_sha256"])
    suite, _, _ = _load_cases(DEFAULT_SUITE)
    inputs = {case["case_id"]: _fingerprint(_model_input(
        case["decision"], case["original_feedback"], case["job_context"], suite.hard_rules,
    )) for case in suite.cases}
    if (configuration["fixtures"]["fresh"]["sha256"] != suite.sha256 or configuration["case_input_sha256"] != inputs
            or report["requests_completed"] != 48 or [p["pass_number"] for p in report["passes"]] != [1, 2]):
        raise ValueError("the replay requires both complete archived review-only passes with their original inputs")
    trace_path = archive / report["request_trace_file"]
    if sha256(trace_path.read_bytes()).hexdigest() != report["request_trace_sha256"]:
        raise ValueError("the request trace does not match the archived report")
    changes, processed = [], 0
    for run in report["passes"]:
        number = run["pass_number"]
        if run["directory"] != f"pass-{number}" or set(run["arms"]) != set(ARMS):
            raise ValueError("an archived pass has unexpected arms or file names")
        directory = archive / run["directory"]
        for arm in ARMS:
            records = run["arms"][arm]
            raw, _ = _read_archive_json(directory / f"{arm}.proposals.json", records["raw_proposals_sha256"])
            final, _ = _read_archive_json(directory / f"{arm}.json", records["validated_sha256"])
            if raw.keys() != final.keys() or raw.keys() != inputs.keys():
                raise ValueError(f"pass {number} {arm} does not cover the full archived case set")
            for case in suite.cases:
                case_id = case["case_id"]
                updated = _compare(case, suite.hard_rules, raw[case_id], final[case_id], arm, configuration["model"])
                processed += 1
                if updated["changed_fields"]:
                    changes.append({"pass_number": number, "origin_arm": arm, "case_id": case_id, **updated})
    return {"mode": "offline_review_only_followup", "inference_requests": 0, "archive_report_sha256": report_hash,
            "archive_configuration_sha256": config_hash, "reference_sha256": suite.sha256, "replayed_proposals": processed,
            "unchanged_proposals": processed - len(changes), "changed_proposals": len(changes), "changes": changes}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, required=True, help="New replay report outside the source archive")
    args = parser.parse_args(argv)
    archive, output = args.archive.resolve(), args.output.resolve()
    if output == archive or archive in output.parents:
        parser.error("--output must be a new file outside the source archive")
    try:
        _save_json(output, replay(args.archive))
    except (OSError, ValueError, KeyError, TypeError, FeedbackProviderError) as error:
        print(f"Review-only follow-up replay could not complete. {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
