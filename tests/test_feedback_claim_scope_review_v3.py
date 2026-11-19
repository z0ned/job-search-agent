"""Verify that scope flags preserve saved claims and their review authority."""

from contextlib import redirect_stderr
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from job_search_agent.feedback_claim_scope_review_v3 import _project_case, main
from job_search_agent.feedback_evaluation import _save_json


METADATA = {
    "decision": "interested", "review_status": "PROFILE_FACT_REVIEW", "clarification_question": None,
    "profile_fact_candidate": "Has not chaired an incident review.", "eligibility_violation": None,
    "hard_constraint_action": "UNCHANGED", "hard_constraints_mutated": False,
    "validation_issues": [{"field": "signals", "index": 5, "message": "Bad scope."}], "evidence_findings": [],
}


def _judgment(index, disposition, scope_status, **fields):
    return {
        "signal_index": index, "disposition": disposition, "rationale": "Claim evidence reviewed.",
        "scope_status": scope_status, "scope_rationale": "Scope evidence reviewed.", **fields,
    }


class ClaimScopeReviewTests(unittest.TestCase):
    def setUp(self):
        self.prediction = {**METADATA, "interpretations": [{"application_status": "held_for_review"} for _ in range(5)]}
        self.judgments = [
            _judgment(3, "unresolved", "supported"),
            _judgment(1, "explanatory", "unsupported", explains_signal_index=2),
            _judgment(2, "independent", "supported"),
            _judgment(5, "independent", "unsupported"),
            _judgment(4, "independent", "unresolved"),
        ]

    def test_scope_and_claim_uncertainty_remain_visible(self):
        case = _project_case(self.prediction, self.judgments, "example")
        self.assertEqual(case["visible_signal_indices"], [2, 3, 4, 5])
        self.assertEqual(case["flagged_signal_indices"], [3, 4, 5])
        self.assertEqual(case["unflagged_signal_indices"], [2])
        self.assertEqual(case["independent_signal_indices"], [2, 4, 5])
        self.assertEqual(case["explanatory_signal_indices"], [1])
        self.assertEqual(case["unresolved_signal_indices"], [3])
        self.assertEqual(case["decisions"], sorted(self.judgments, key=lambda row: row["signal_index"]))
        self.assertEqual({field: case[field] for field in METADATA}, METADATA)

    def test_rejects_invalid_scope_and_explanatory_target(self):
        for row_index, change in (
            (0, {"scope_status": "unknown"}),
            (0, {"scope_rationale": " "}),
            (0, {"signal_index": 2}),
            (1, {"explains_signal_index": 3}),
        ):
            with self.subTest(change=change):
                decisions = deepcopy(self.judgments)
                decisions[row_index].update(change)
                with self.assertRaisesRegex(ValueError, "example"):
                    _project_case(self.prediction, decisions, "example")
        with self.assertRaisesRegex(ValueError, "one disposition"):
            _project_case(self.prediction, self.judgments[:-1], "example")

    def test_rejects_unsafe_archived_routing_or_application(self):
        for change in (
            {"review_status": "APPLIED"},
            {"hard_constraint_action": "RULES_CHANGED"},
            {"hard_constraints_mutated": True},
            {"review_status": "PENDING_APPROVAL", "profile_fact_candidate": "Unresolved fact."},
            {"interpretations": [{"application_status": "applied"}] * 5},
        ):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "example"):
                _project_case({**self.prediction, **change}, self.judgments, "example")

    def test_cli_checks_archive_hashes_and_writes_only_a_new_projection(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            archive = directory / "archive"
            archive.mkdir()
            config_hash = _save_json(archive / "configuration.json", {
                "mode": "targeted_independent_signal_trial", "known_case_ids": ["case"], "synthetic_case_ids": ["empty"],
            })
            report_arms, decision_arms = {}, {}
            for arm in ("control", "treatment"):
                capture = f"{arm}.json"
                capture_hash = _save_json(archive / capture, {
                    "case": self.prediction, "empty": {**self.prediction, "interpretations": []},
                })
                report_arms[arm] = {"validated_file": capture, "validated_sha256": capture_hash}
                decision_arms[arm] = {"validated_sha256": capture_hash, "cases": {"case": self.judgments, "empty": []}}
            _save_json(archive / "report.json", {"arms": report_arms, "configuration_sha256": config_hash})
            decisions = directory / "decisions.json"
            decisions_hash = _save_json(decisions, {"reviewer": "Example review", "arms": decision_arms})
            output = directory / "projection.json"
            args = ["--archive", str(archive), "--decisions", str(decisions), "--output", str(output)]
            with patch("job_search_agent.feedback.urlopen", side_effect=AssertionError("unexpected request")) as request:
                self.assertEqual(main(args), 0)
                request.assert_not_called()
            original_bytes = output.read_bytes()
            result = json.loads(original_bytes)
            self.assertEqual(result["mode"], "offline_manual_claim_scope_review")
            self.assertEqual(result["inference_requests"], 0)
            self.assertEqual(result["decisions_sha256"], decisions_hash)
            self.assertEqual(result["arms"]["control"]["cases"]["empty"]["visible_signal_indices"], [])
            with redirect_stderr(StringIO()):
                self.assertEqual(main(args), 2)
            self.assertEqual(output.read_bytes(), original_bytes)

            with (archive / "treatment.json").open("ab") as capture:
                capture.write(b" ")
            args[-1] = str(directory / "stale.json")
            error = StringIO()
            with redirect_stderr(error):
                self.assertEqual(main(args), 2)
            self.assertIn("recorded SHA-256", error.getvalue())
            self.assertFalse(Path(args[-1]).exists())


if __name__ == "__main__":
    unittest.main()
