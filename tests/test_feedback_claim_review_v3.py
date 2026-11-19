"""Verify that an offline review keeps each saved signal and route traceable."""

from contextlib import redirect_stderr
from copy import deepcopy
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from job_search_agent.feedback_claim_review_v3 import main, replay_claim_reviews
from job_search_agent.feedback_evaluation import _save_json


def _decision(index, disposition, **fields):
    return {"signal_index": index, "disposition": disposition, "rationale": "Reviewed against the source.", **fields}


class ClaimReviewTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(TemporaryDirectory()))
        self.archive = self.directory / "archive"
        self.archive.mkdir()
        self.decisions_path = self.directory / "decisions.json"
        self.output = self.directory / "projection.json"
        self.metadata = {
            "decision": "interested", "review_status": "PROFILE_FACT_REVIEW", "clarification_question": None,
            "profile_fact_candidate": "Has not chaired an incident review.", "eligibility_violation": None,
            "hard_constraint_action": "UNCHANGED", "hard_constraints_mutated": False,
            "validation_issues": [{"field": "signals", "index": 3, "message": "Bad scope."}], "evidence_findings": [],
        }
        signals = [{"application_status": "held_for_review", "evidence": [f"Signal evidence {index}"]}
                   for index in range(1, 4)]
        self.predictions = {
            "target": {**self.metadata, "interpretations": signals},
            "no-signals": {**self.metadata, "interpretations": []},
        }
        config_hash = _save_json(self.archive / "configuration.json", {
            "mode": "targeted_independent_signal_trial", "known_case_ids": ["target"], "synthetic_case_ids": ["no-signals"],
        })
        self.report = {"configuration_sha256": config_hash, "arms": {}}
        self.decisions = {"reviewer": "Example review", "arms": {}}
        for arm in ("control", "treatment"):
            validated_file = f"{arm}.json"
            validated_hash = _save_json(self.archive / validated_file, self.predictions)
            self.report["arms"][arm] = {"validated_sha256": validated_hash, "validated_file": validated_file}
            self.decisions["arms"][arm] = {"validated_sha256": validated_hash, "cases": {
                "target": [_decision(3, "unresolved"), _decision(1, "explanatory", explains_signal_index=2),
                           _decision(2, "independent")],
                "no-signals": [],
            }}
        _save_json(self.archive / "report.json", self.report)

    def test_projection_preserves_every_disposition_and_archived_review(self):
        decisions_hash = _save_json(self.decisions_path, self.decisions)
        with patch("job_search_agent.feedback.urlopen", side_effect=AssertionError("unexpected request")) as request:
            self.assertEqual(main(["--archive", str(self.archive), "--decisions", str(self.decisions_path),
                                   "--output", str(self.output)]), 0)
            request.assert_not_called()
        result = json.loads(self.output.read_bytes())
        self.assertEqual(result["inference_requests"], 0)
        self.assertEqual(result["decisions_sha256"], decisions_hash)
        for arm, projected in result["arms"].items():
            self.assertEqual(projected["validated_sha256"], self.report["arms"][arm]["validated_sha256"])
            self.assertEqual(sha256((self.archive / projected["validated_file"]).read_bytes()).hexdigest(),
                             projected["validated_sha256"])
            self.assertEqual(json.loads((self.archive / projected["validated_file"]).read_bytes()), self.predictions)
            case = projected["cases"]["target"]
            self.assertEqual(case["independent_signal_indices"], [2])
            self.assertEqual(case["explanatory_signal_indices"], [1])
            self.assertEqual(case["unresolved_signal_indices"], [3])
            self.assertEqual(case["decisions"], sorted(self.decisions["arms"][arm]["cases"]["target"],
                                                       key=lambda row: row["signal_index"]))
            self.assertEqual({field: case[field] for field in self.metadata}, self.metadata)
            self.assertEqual(projected["cases"]["no-signals"]["decisions"], [])

    def test_rejects_missing_duplicate_invalid_or_unlinked_dispositions(self):
        for invalid in (
            [],
            [_decision(1, "independent"), _decision(1, "independent"), _decision(3, "independent")],
            [_decision(True, "independent"), _decision(2, "independent"), _decision(3, "independent")],
            [_decision(1, "unknown"), _decision(2, "independent"), _decision(3, "unresolved")],
            [_decision(1, "independent", explains_signal_index=2), _decision(2, "independent"), _decision(3, "unresolved")],
            [_decision(1, "explanatory", explains_signal_index=1), _decision(2, "independent"), _decision(3, "unresolved")],
            [_decision(1, "explanatory", explains_signal_index=3), _decision(2, "independent"), _decision(3, "unresolved")],
            [_decision(1, "explanatory", explains_signal_index=2),
             _decision(2, "explanatory", explains_signal_index=1), _decision(3, "independent")],
        ):
            with self.subTest(invalid=invalid):
                decisions = deepcopy(self.decisions)
                decisions["arms"]["control"]["cases"]["target"] = invalid
                path = self.directory / "invalid.json"
                _save_json(path, decisions)
                try:
                    with self.assertRaisesRegex(ValueError, "target"):
                        replay_claim_reviews(self.archive, path)
                finally:
                    path.unlink()

    def test_rejects_stale_bytes_without_creating_projection(self):
        _save_json(self.decisions_path, self.decisions)
        with (self.archive / "treatment.json").open("ab") as capture:
            capture.write(b" ")
        errors = StringIO()
        with redirect_stderr(errors):
            self.assertEqual(main(["--archive", str(self.archive), "--decisions", str(self.decisions_path),
                                   "--output", str(self.output)]), 2)
        self.assertIn("recorded SHA-256", errors.getvalue())
        self.assertFalse(self.output.exists())

    def test_rejects_decisions_bound_to_different_capture(self):
        self.decisions["arms"]["treatment"]["validated_sha256"] = "0" * 64
        _save_json(self.decisions_path, self.decisions)
        with self.assertRaisesRegex(ValueError, "decisions do not match"):
            replay_claim_reviews(self.archive, self.decisions_path)


if __name__ == "__main__":
    unittest.main()
