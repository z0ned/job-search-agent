"""Exercise offline revalidation with hash-bound archived raw proposals."""

from contextlib import redirect_stderr
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from job_search_agent.feedback_evaluation import GoldSuite, _save_json
from job_search_agent.feedback_evaluation_v3 import _live_configuration
from job_search_agent.feedback_extraction_v3 import PROMPT_VERSION
from job_search_agent.feedback_replay_v3 import main, revalidate_pass
from job_search_agent.feedback_v3 import interpret_feedback_v3


FEEDBACK = "I do not want to work in the tobacco industry."
CASE = {
    "case_id": "FI-018", "decision": "rejected", "original_feedback": FEEDBACK,
    "job_context": {"title": "Transformation Director"},
    "expected_review_status": "PENDING_APPROVAL", "expected_hard_constraint_action": "UNCHANGED",
    "expected_interpretations": [{
        "dimension": "industry", "feature": "tobacco industry", "polarity": "negative", "strength": "strong",
        "scope": {"type": "industry", "value": "tobacco"}, "evidence_quote": FEEDBACK,
    }],
}
SUITE = GoldSuite("fixture", "a" * 64, [CASE], {})
SOURCE = {
    "mode": "live", "passes": 2, "requested_model": "snapshot", "prompt_version": PROMPT_VERSION,
    "temperature_override": 0.1,
}


def _proposal():
    return {
        "clauses": [{"role": "preference", "quote": FEEDBACK, "detail": None}],
        "signals": [{
            "clause_index": 0, "dimension": "industry", "display_label": "tobacco industry",
            "polarity": "negative", "strength": "strong",
            "scope": {"type": "industry", "referent": "tobacco", "qualifiers": []}, "condition": None,
        }],
    }


def _validated():
    provider = Mock(model=SOURCE["requested_model"], **{"propose.return_value": _proposal()})
    return {
        CASE["case_id"]: interpret_feedback_v3(
            CASE["decision"], FEEDBACK, CASE["job_context"], provider=provider, hard_rules=SUITE.hard_rules,
        ),
    }


def _archive(directory, *, raw=None):
    directory.mkdir()
    configuration = _live_configuration(SimpleNamespace(suite="gold", scenarios=Path("fixture.json")), SUITE, "fixed")
    config_hash = _save_json(directory / "configuration.json", {**configuration, "evaluation_source": SOURCE})
    proposals = {CASE["case_id"]: _proposal()} if raw is None else raw
    runs = []
    for number in (1, 2):
        files = {"predictions": f"pass-{number}.json", "proposals": f"pass-{number}.proposals.json"}
        runs.append({
            "pass_number": number, "capture_id": f"live-{number}", "capture_files": files,
            "predictions_sha256": _save_json(directory / files["predictions"], _validated()),
            "proposals_sha256": _save_json(directory / files["proposals"], proposals),
        })
    _save_json(directory / "live-report.json", {
        "configuration": {"capture_configuration_sha256": config_hash}, "evaluation_source": SOURCE, "runs": runs,
    })


class V3OfflineReplayTests(unittest.TestCase):
    def _run(self, archive, output):
        stderr = StringIO()
        with (
            patch("job_search_agent.feedback_replay_v3.load_v3_suite", return_value=SUITE),
            patch("job_search_agent.feedback_extraction_v3.OpenAIFeedbackProviderV3") as provider,
            patch("job_search_agent.feedback_v3.OpenAIFeedbackProviderV3") as validator_provider,
            redirect_stderr(stderr),
        ):
            code = main(["fixture.json", "--archive", str(archive), "--output", str(output)])
        provider.assert_not_called()
        validator_provider.assert_not_called()
        return code, stderr.getvalue()

    def test_baseline_replay_preserves_original_predictions_and_links_source_hashes(self):
        directory = Path(self.enterContext(TemporaryDirectory()))
        archive, output = directory / "live", directory / "offline"
        _archive(archive)
        original_bytes = {path.name: path.read_bytes() for path in archive.iterdir()}
        code, error = self._run(archive, output)
        self.assertEqual(code, 0, error)
        self.assertEqual(original_bytes, {path.name: path.read_bytes() for path in archive.iterdir()})
        report = json.loads((output / "report.json").read_bytes())
        self.assertEqual(report["evaluation_source"]["inference_requests"], 0)
        self.assertEqual(report["evaluation_source"]["original_evaluation_source"], SOURCE)
        self.assertFalse(report["quality_gates_passed"])
        for run in report["runs"]:
            predictions_file = run["validated_predictions_file"]
            predictions = (output / predictions_file).read_bytes()
            raw = original_bytes[run["raw_proposals_file"]]
            self.assertEqual(predictions, original_bytes[predictions_file])
            self.assertEqual(run["raw_proposals_sha256"], sha256(raw).hexdigest())
            self.assertEqual(run["predictions_sha256"], sha256(predictions).hexdigest())
            self.assertEqual(run["comparison_with_live_validated"]["changed_case_ids"], [])

    def test_archive_rejects_wrong_case_ids_and_modified_capture_bytes(self):
        directory = Path(self.enterContext(TemporaryDirectory()))
        wrong_ids = directory / "wrong-ids"
        _archive(wrong_ids, raw={"different-id": _proposal()})
        code, error = self._run(wrong_ids, directory / "wrong-ids-output")
        self.assertEqual(code, 2)
        self.assertIn("case IDs must match", error)
        self.assertFalse((directory / "wrong-ids-output").exists())
        tampered = directory / "tampered"
        _archive(tampered)
        with (tampered / "pass-2.proposals.json").open("ab") as file:
            file.write(b"\n")
        code, error = self._run(tampered, directory / "tampered-output")
        self.assertEqual(code, 2)
        self.assertIn("does not match the recorded SHA-256", error)
        self.assertFalse((directory / "tampered-output").exists())

    def test_null_and_invalid_proposals_receive_safe_per_case_errors(self):
        for proposal, name in ((None, "MissingArchivedProposal"), ({"unexpected": "private text"}, "FeedbackOutputError")):
            with self.subTest(proposal=proposal):
                self.assertEqual(revalidate_pass(SUITE, {CASE["case_id"]: proposal}, SOURCE), {
                    CASE["case_id"]: {"evaluation_error": name},
                })
        with patch("job_search_agent.feedback_v3.interpret_feedback_v3", side_effect=RuntimeError("private exception")):
            self.assertEqual(revalidate_pass(SUITE, {CASE["case_id"]: _proposal()}, SOURCE), {
                CASE["case_id"]: {"evaluation_error": "RuntimeError"},
            })


if __name__ == "__main__":
    unittest.main()
