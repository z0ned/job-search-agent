"""Replay manual claim dispositions on archived v3 validated signals."""

import argparse
from pathlib import Path
import sys

from .feedback_evaluation import _nonblank, _save_json
from .feedback_extraction_independence_trial_v3 import ARMS
from .feedback_replay_v3 import _read_archive_json


_DISPOSITIONS = ("independent", "explanatory", "unresolved")
_DECISION_FIELDS = {"signal_index", "disposition", "rationale"}
_REVIEW_FIELDS = (
    "decision", "review_status", "clarification_question", "profile_fact_candidate", "eligibility_violation",
    "hard_constraint_action", "hard_constraints_mutated", "validation_issues", "evidence_findings",
)


def _project_case(result, reviewed, case_id):
    if (not isinstance(result, dict) or result.get("evaluation_error") or not _nonblank(result.get("review_status"))
            or not _nonblank(result.get("hard_constraint_action")) or result.get("hard_constraints_mutated") is not False
            or not set(_REVIEW_FIELDS) <= result.keys()):
        raise ValueError(f"{case_id} lacks a complete archived review record")
    signals = result.get("interpretations")
    if not isinstance(signals, list) or any(
        not isinstance(signal, dict) or signal.get("application_status") != "held_for_review" for signal in signals
    ):
        raise ValueError(f"{case_id} must contain only archived signals held for review")
    if not isinstance(reviewed, list) or len(reviewed) != len(signals):
        raise ValueError(f"{case_id} requires one disposition per validated signal")

    by_index = {}
    for item in reviewed:
        if not isinstance(item, dict):
            raise ValueError(f"{case_id} has an invalid disposition record")
        index, disposition = item.get("signal_index"), item.get("disposition")
        fields = _DECISION_FIELDS | {"explains_signal_index"} if disposition == "explanatory" else _DECISION_FIELDS
        if (item.keys() != fields or type(index) is not int or not 1 <= index <= len(signals) or index in by_index
                or disposition not in _DISPOSITIONS or not _nonblank(item.get("rationale"))):
            raise ValueError(f"{case_id} has an invalid or repeated signal disposition")
        by_index[index] = item

    projected = {f"{disposition}_signal_indices": [] for disposition in _DISPOSITIONS}
    decisions = []
    for index in range(1, len(signals) + 1):
        item = by_index[index]
        disposition = item["disposition"]
        if disposition == "explanatory":
            target = item["explains_signal_index"]
            if type(target) is not int or target not in by_index or by_index[target]["disposition"] != "independent":
                raise ValueError(f"{case_id} explanatory signal {index} must link to an independent signal")
        projected[f"{disposition}_signal_indices"].append(index)
        decisions.append(item)
    return {**projected, "decisions": decisions, **{field: result[field] for field in _REVIEW_FIELDS}}


def replay_claim_reviews(archive, decisions_file):
    """Validate decisions against their original capture and return an index projection."""
    report, report_hash = _read_archive_json(archive / "report.json")
    configuration_hash = report.get("configuration_sha256")
    if not _nonblank(configuration_hash):
        raise ValueError("archive report lacks its configuration SHA-256")
    configuration, _ = _read_archive_json(archive / "configuration.json", configuration_hash)
    known, synthetic = configuration.get("known_case_ids"), configuration.get("synthetic_case_ids")
    if (configuration.get("mode") != "targeted_independent_signal_trial"
            or not all(isinstance(ids, list) and ids and all(_nonblank(case_id) for case_id in ids)
                       for ids in (known, synthetic))):
        raise ValueError("archive configuration lacks the independence trial case IDs")
    case_ids = set(known + synthetic)
    if len(case_ids) != len(known) + len(synthetic):
        raise ValueError("archive configuration contains repeated case IDs")

    decisions, decisions_hash = _read_archive_json(decisions_file)
    reviewed_arms, archived_arms, reviewer = decisions.get("arms"), report.get("arms"), decisions.get("reviewer")
    if decisions.keys() != {"arms", "reviewer"} or not _nonblank(reviewer):
        raise ValueError("decisions must identify the reviewer and reviewed arms")
    if any(not isinstance(arms, dict) or arms.keys() != set(ARMS) for arms in (reviewed_arms, archived_arms)):
        raise ValueError("archive and decisions must cover both independence trial arms")

    projected = {}
    for arm in ARMS:
        archived, reviewed = archived_arms[arm], reviewed_arms[arm]
        validated_file = f"{arm}.json"
        if (not isinstance(archived, dict) or archived.get("validated_file") != validated_file
                or not _nonblank(archived.get("validated_sha256"))):
            raise ValueError(f"{arm} archive lacks its validated capture metadata")
        validated_hash = archived["validated_sha256"]
        if (not isinstance(reviewed, dict) or reviewed.keys() != {"validated_sha256", "cases"}
                or reviewed["validated_sha256"] != validated_hash):
            raise ValueError(f"{arm} decisions do not match the archived validated SHA-256")
        predictions, _ = _read_archive_json(archive / validated_file, validated_hash)
        cases = reviewed["cases"]
        if not isinstance(cases, dict) or predictions.keys() != case_ids or cases.keys() != case_ids:
            raise ValueError(f"{arm} capture and decisions must cover every archived case")
        projected[arm] = {
            "validated_file": validated_file, "validated_sha256": validated_hash,
            "cases": {case_id: _project_case(result, cases[case_id], case_id) for case_id, result in predictions.items()},
        }

    return {
        "mode": "offline_manual_claim_review", "inference_requests": 0, "reviewer": reviewer,
        "archive_report_sha256": report_hash, "archive_configuration_sha256": configuration_hash,
        "decisions_sha256": decisions_hash, "arms": projected,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True, help="Archived independence trial directory")
    parser.add_argument("--decisions", type=Path, required=True, help="Manual claim disposition JSON")
    parser.add_argument("--output", type=Path, required=True, help="New JSON projection file")
    args = parser.parse_args(argv)
    archive, output = args.archive.resolve(), args.output.resolve()
    if output == archive or archive in output.parents:
        parser.error("--output must be a new file outside the archive")
    try:
        projection = replay_claim_reviews(archive, args.decisions)
        _save_json(output, projection)
    except (OSError, ValueError) as error:
        print(f"Offline claim review could not complete. {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
