"""Replay independent claim and scope judgments on archived v3 signals."""

import argparse
from operator import itemgetter
from pathlib import Path
import sys

from .feedback import (
    HARD_CONSTRAINT_ACTIONS,
    NEEDS_CLARIFICATION,
    PENDING_APPROVAL,
    PROFILE_FACT_REVIEW,
    REPORT_ELIGIBILITY_VIOLATION,
    REQUIRE_RULE_CONFIRMATION,
    REVIEW_STATUSES,
)
from .feedback_claim_review_v3 import _project_case as _project_claim_case, _replay_review
from .feedback_evaluation import _nonblank, _save_json


_DISPUTED_TARGETS_FIELD = "disputed_explanation_target_indices"
_SCOPE_REVIEW_FIELDS = {"scope_status", "scope_rationale", _DISPUTED_TARGETS_FIELD}
_SCOPE_STATUSES = ("supported", "unsupported", "unresolved")


def _check_archived_route(projected, case_id):
    route = projected["review_status"]
    action = projected["hard_constraint_action"]
    question = projected["clarification_question"]
    fact = projected["profile_fact_candidate"]
    if route not in REVIEW_STATUSES or action not in HARD_CONSTRAINT_ACTIONS:
        raise ValueError(f"{case_id} has an unknown archived review route or hard-rule action")
    if ((not _nonblank(question) if route == NEEDS_CLARIFICATION else question is not None)
            or (not _nonblank(fact) if route == PROFILE_FACT_REVIEW else fact is not None)):
        raise ValueError(f"{case_id} has inconsistent archived review routing details")
    if (action == REQUIRE_RULE_CONFIRMATION and route != PROFILE_FACT_REVIEW
            or action == REPORT_ELIGIBILITY_VIOLATION and not _nonblank(projected["eligibility_violation"])
            or route == PENDING_APPROVAL and not projected["decisions"]):
        raise ValueError(f"{case_id} has inconsistent archived review authority")


def _disputed_explanation_targets(decisions, case_id):
    visible_indices = {item["signal_index"] for item in decisions if item["disposition"] != "explanatory"}
    disputed_targets = set()
    for item in decisions:
        if _DISPUTED_TARGETS_FIELD not in item:
            continue
        targets = item[_DISPUTED_TARGETS_FIELD]
        index = item["signal_index"]
        if (item["disposition"] != "unresolved" or not isinstance(targets, list) or not targets
                or any(type(target) is not int or target == index or target not in visible_indices for target in targets)
                or len(set(targets)) != len(targets)):
            raise ValueError(f"{case_id} signal {index} has invalid disputed explanation targets")
        disputed_targets.update(targets)
    return disputed_targets


def _project_case(result, reviewed, case_id):
    if not isinstance(reviewed, list):
        raise ValueError(f"{case_id} requires one claim and scope judgment per validated signal")
    claim_decisions = []
    for item in reviewed:
        if (not isinstance(item, dict) or item.get("scope_status") not in _SCOPE_STATUSES
                or not _nonblank(item.get("scope_rationale"))):
            raise ValueError(f"{case_id} has an invalid scope judgment")
        claim_decisions.append({key: value for key, value in item.items() if key not in _SCOPE_REVIEW_FIELDS})

    projected = _project_claim_case(result, claim_decisions, case_id)
    _check_archived_route(projected, case_id)
    decisions = sorted(reviewed, key=itemgetter("signal_index"))
    disputed_targets = _disputed_explanation_targets(decisions, case_id)
    visible, flagged, unflagged = [], [], []
    for item in decisions:
        if item["disposition"] == "explanatory":
            continue
        index = item["signal_index"]
        visible.append(index)
        if item["disposition"] == "unresolved" or item["scope_status"] != "supported" or index in disputed_targets:
            flagged.append(index)
        else:
            unflagged.append(index)

    return {
        **projected, "decisions": decisions, "visible_signal_indices": visible,
        "flagged_signal_indices": flagged, "unflagged_signal_indices": unflagged,
    }


def replay_claim_scope_reviews(archive, decisions_file):
    """Validate both judgments and preserve flagged claims for review."""
    return _replay_review(
        archive, decisions_file, project_case=_project_case, mode="offline_manual_claim_scope_review",
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True, help="Archived independence trial directory")
    parser.add_argument("--decisions", type=Path, required=True, help="Manual claim and scope judgments JSON")
    parser.add_argument("--output", type=Path, required=True, help="New JSON projection file")
    args = parser.parse_args(argv)
    archive, output = args.archive.resolve(), args.output.resolve()
    if output == archive or archive in output.parents:
        parser.error("--output must be a new file outside the archive")
    try:
        _save_json(output, replay_claim_scope_reviews(archive, args.decisions))
    except (OSError, ValueError) as error:
        print(f"Offline claim and scope review could not complete. {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
