"""Exercise hash-checked, API-independent extraction-trial replay."""

from contextlib import redirect_stderr
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from job_search_agent import feedback_v3
from job_search_agent.feedback_evaluation import GoldSuite, _save_json
from job_search_agent.feedback_extraction_trial_replay_v3 import main
from job_search_agent.feedback_extraction_trial_v3 import ARMS, _configuration, _request_order
from job_search_agent.feedback_extraction_v3 import PROMPT_VERSION
from job_search_agent.feedback_replay_v3 import revalidate_pass


FEEDBACK = "I like working fully remotely."
CASE = {
    "case_id": "FT-001", "decision": "interested", "original_feedback": FEEDBACK, "job_context": {},
    "expected_review_status": "PENDING_APPROVAL", "expected_hard_constraint_action": "UNCHANGED",
    "expected_interpretations": [{
        "dimension": "work_arrangement", "feature": "fully remote", "polarity": "positive", "strength": "mild",
        "scope": {"type": "arrangement", "value": "fully_remote"}, "evidence_quote": FEEDBACK,
    }],
}
SOURCE = {"requested_model": "snapshot", "prompt_version": PROMPT_VERSION}
SUITE = GoldSuite("synthetic", "1" * 64, [CASE], {})
FIXTURES = {"novel": {"file": "fixture.json", "version": SUITE.version, "sha256": SUITE.sha256}}
RAW = {CASE["case_id"]: {
    "clauses": [{"role": "preference", "quote": FEEDBACK, "detail": None}],
    "signals": [{
        "clause_index": 0, "dimension": "work_arrangement", "display_label": "fully remote",
        "polarity": "positive", "strength": "mild", "condition": None,
        "scope": {"type": "arrangement", "referent": "fully_remote", "qualifiers": []},
    }],
}}


def _make_archive(archive, candidate, *, raw=RAW, changed_source="feedback_v3.py"):
    archive.mkdir()
    order = _request_order(SUITE.cases)
    config = _configuration(
        SimpleNamespace(temperature=0.1, candidate=candidate),
        SUITE.cases, SUITE.hard_rules, FIXTURES, [], candidate.read_bytes(), SOURCE["requested_model"], order,
    )
    config["source_sha256"][changed_source] = "b" * 64
    report = {
        "configuration_sha256": _save_json(archive / "configuration.json", config),
        "request_log": [{**entry, "elapsed_seconds": 0.0} for entry in order],
        "requests_completed": len(order), "arms": {},
    }
    original = revalidate_pass(SUITE, RAW, SOURCE)
    for arm in ARMS:
        validated_file, raw_file = f"{arm}.json", f"{arm}.proposals.json"
        report["arms"][arm] = {
            "raw_proposals_file": raw_file, "raw_proposals_sha256": _save_json(archive / raw_file, raw),
            "validated_file": validated_file, "validated_sha256": _save_json(archive / validated_file, original),
        }
    _save_json(archive / "report.json", report)


class ExtractionTrialReplayTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(TemporaryDirectory()))
        self.candidate = self.directory / "instructions.txt"
        self.candidate.write_text("Synthetic candidate instructions\n", encoding="utf-8")

    def _run(self, archive, output, *, recovery=True):
        stderr = StringIO()
        args = ["--archive", str(archive), "--candidate", str(self.candidate), "--output", str(output)]
        if not recovery:
            args.append("--no-recover-explicit-conditions")
        with (
            patch("job_search_agent.feedback_extraction_trial_replay_v3._load_trial",
                  return_value=(SUITE.cases, SUITE.hard_rules, FIXTURES, [])),
            patch("job_search_agent.feedback.urlopen") as transport,
            redirect_stderr(stderr),
        ):
            code = main(args)
        transport.assert_not_called()
        return code, stderr.getvalue()

    def test_disabled_recovery_reproduces_both_original_arms_byte_for_byte(self):
        archive, output = self.directory / "live", self.directory / "offline"
        _make_archive(archive, self.candidate)
        original = {file.name: file.read_bytes() for file in archive.iterdir()}
        code, error = self._run(archive, output, recovery=False)
        self.assertEqual(code, 0, error)
        self.assertEqual(original, {file.name: file.read_bytes() for file in archive.iterdir()})
        replay = json.loads((output / "report.json").read_bytes())
        configuration = json.loads((output / "configuration.json").read_bytes())
        self.assertEqual(replay["inference_requests"], 0)
        self.assertEqual(replay["revalidated_cases"], 2)
        self.assertTrue(replay["byte_exact_archive_match"])
        self.assertFalse(configuration["recover_explicit_conditions"])
        self.assertEqual(configuration["archive_configuration_sha256"], sha256(original["configuration.json"]).hexdigest())
        self.assertIn("feedback_conditions_v3.py", configuration["replay_source_sha256"])
        self.assertIn("feedback_evidence_checks_v3.py", configuration["replay_source_sha256"])
        self.assertIn("feedback_replay_v3.py", configuration["replay_source_sha256"])
        for arm in ARMS:
            self.assertEqual((output / f"{arm}.json").read_bytes(), original[f"{arm}.json"])
            self.assertEqual(replay["arms"][arm]["raw_proposals_sha256"], sha256(original[f"{arm}.proposals.json"]).hexdigest())

    def test_enabled_recovery_is_passed_to_the_same_offline_validator(self):
        archive, output = self.directory / "live", self.directory / "offline"
        _make_archive(archive, self.candidate)
        with patch("job_search_agent.feedback_v3.interpret_feedback_v3", wraps=feedback_v3.interpret_feedback_v3) as validate:
            code, error = self._run(archive, output)
        self.assertEqual(code, 0, error)
        self.assertEqual(validate.call_count, 2)
        self.assertTrue(all(call.kwargs["recover_explicit_conditions"] for call in validate.call_args_list))
        result = json.loads((output / "baseline.json").read_bytes())[CASE["case_id"]]
        self.assertIn("condition_recoveries", result)
        report = json.loads((output / "report.json").read_bytes())
        self.assertFalse(report["byte_exact_archive_match"])
        self.assertEqual(report["arms"]["baseline"]["comparison_with_live_validated"]["changed_fields"]["condition_recoveries"], [])

    def test_rejects_tampering_mismatched_case_ids_and_nonvalidator_drift(self):
        fixtures = (
            ("bad-cases", {"wrong-case": RAW[CASE["case_id"]]}, "feedback_v3.py", "complete set of trial case IDs"),
            ("source-drift", RAW, "feedback_rules_v3.py", "outside the permitted validator repair"),
            ("bytes-drift", RAW, "feedback_v3.py", "does not match the recorded SHA-256"),
        )
        for name, raw, changed_source, message in fixtures:
            with self.subTest(name=name):
                archive, output = self.directory / name, self.directory / f"{name}-replay"
                _make_archive(archive, self.candidate, raw=raw, changed_source=changed_source)
                if name == "bytes-drift":
                    with (archive / "candidate.proposals.json").open("ab") as file:
                        file.write(b"\n")
                code, error = self._run(archive, output)
                self.assertEqual(code, 2)
                self.assertIn(message, error)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
