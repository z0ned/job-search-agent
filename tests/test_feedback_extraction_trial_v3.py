"""Check that the targeted v3 trial changes only the extraction instructions."""

from contextlib import redirect_stderr
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from job_search_agent import feedback_extraction_v3
from job_search_agent.feedback_extraction_trial_v3 import _load_trial, main


NOVEL = Path("benchmarks/feedback/extraction_trial_v3_novel.json")
CASE_ORDER = ["FI-033", "FI-048", "FH3-010", "FI-041", "FH-005", "FT-001", "FT-002", "FT-003", "FT-004", "FT-005"]
CANDIDATE = b"Synthetic candidate instructions for transport testing.\n"


def _response(payload):
    original_feedback = json.loads(payload["input"])["original_feedback"]
    raw = {"clauses": [{"role": "vague_reaction", "quote": original_feedback, "detail": "What stood out?"}],
           "signals": []}
    return BytesIO(json.dumps({
        "status": "completed",
        "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(raw)}]}],
    }).encode())


class ExtractionTrialTests(unittest.TestCase):
    def test_known_fixture_selection_novel_pairing_and_fingerprints(self):
        cases, rules, sources, pairs = _load_trial(NOVEL)
        self.assertEqual([case["case_id"] for case in cases], CASE_ORDER)
        self.assertEqual(pairs, [dict(known=known, novel=novel)
                                 for known, novel in zip(CASE_ORDER[:5], CASE_ORDER[5:], strict=True)])
        self.assertIn("commute_rules", rules)
        self.assertEqual(sources["novel"]["sha256"], sha256(NOVEL.read_bytes()).hexdigest())
        self.assertEqual({kind: source["file"] for kind, source in sources.items()}, {
            "gold": "benchmarks/feedback/gold_cases_v3.json",
            "regression": "benchmarks/feedback/holdout_cases_v2.json",
            "holdout": "benchmarks/feedback/holdout_cases_v3.json",
            "novel": str(NOVEL),
        })

    def test_both_arms_have_identical_wire_requests_except_instructions(self):
        directory = Path(self.enterContext(TemporaryDirectory()))
        candidate = directory / "candidate.txt"
        candidate.write_bytes(CANDIDATE)
        output = directory / "capture"
        payloads = []
        production_file = Path(feedback_extraction_v3.__file__)
        production_bytes = production_file.read_bytes()

        def respond(request, *, timeout):
            self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
            self.assertEqual(request.get_method(), "POST")
            self.assertEqual(timeout, 60)
            payload = json.loads(request.data)
            payloads.append(payload)
            return _response(payload)

        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}),
            patch("job_search_agent.feedback.urlopen", side_effect=respond),
            redirect_stderr(StringIO()),
        ):
            status = main(["--novel", str(NOVEL), "--candidate", str(candidate), "--output", str(output)])
        self.assertEqual(status, 0)
        self.assertEqual(production_file.read_bytes(), production_bytes)
        self.assertEqual(len(payloads), 20)
        cases, rules, _, _ = _load_trial(NOVEL)
        for index, case in enumerate(cases):
            first, second = payloads[index * 2:index * 2 + 2]
            expected_order = (feedback_extraction_v3._INSTRUCTIONS, CANDIDATE.decode())
            if index % 2:
                expected_order = tuple(reversed(expected_order))
            self.assertEqual((first["instructions"], second["instructions"]), expected_order)
            self.assertEqual({**first, "instructions": second["instructions"]}, second)
            self.assertEqual(first["model"], "gpt-5.4-2026-03-05")
            self.assertEqual(first["temperature"], 0.1)
            self.assertIs(first["store"], False)
            self.assertEqual(first["text"]["format"]["name"], "feedback_extraction_v3")
            self.assertEqual(json.loads(first["input"]), {
                "decision": case["decision"], "original_feedback": case["original_feedback"],
                "job_context": case["job_context"], "hard_rules": rules,
            })
        configuration_bytes = (output / "configuration.json").read_bytes()
        configuration = json.loads(configuration_bytes)
        report = json.loads((output / "report.json").read_bytes())
        self.assertEqual(report["configuration_sha256"], sha256(configuration_bytes).hexdigest())
        self.assertEqual(configuration["arms"]["candidate"]["instruction_sha256"], sha256(CANDIDATE).hexdigest())
        self.assertEqual(report["requests_completed"], 20)
        self.assertEqual(report["score_status"], "automated_diagnostics_only")
        for arm in report["arms"].values():
            raw_bytes = (output / arm["raw_proposals_file"]).read_bytes()
            self.assertEqual(set(json.loads(raw_bytes)), set(CASE_ORDER))
            self.assertEqual(arm["raw_proposals_sha256"], sha256(raw_bytes).hexdigest())
            prediction_bytes = (output / arm["validated_file"]).read_bytes()
            self.assertEqual(set(json.loads(prediction_bytes)), set(CASE_ORDER))
            self.assertEqual(arm["validated_sha256"], sha256(prediction_bytes).hexdigest())

    def test_provider_error_is_captured_without_retries_or_stopping_other_cases(self):
        directory = Path(self.enterContext(TemporaryDirectory()))
        candidate = directory / "candidate.txt"
        candidate.write_bytes(CANDIDATE)
        output = directory / "capture"
        calls = 0

        def respond(request, *, timeout):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("private transport detail")
            return _response(json.loads(request.data))

        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}),
            patch("job_search_agent.feedback.urlopen", side_effect=respond),
            redirect_stderr(StringIO()),
        ):
            status = main(["--novel", str(NOVEL), "--candidate", str(candidate), "--output", str(output)])
        self.assertEqual(status, 1)
        self.assertEqual(calls, 20)
        raw = json.loads((output / "baseline.proposals.json").read_bytes())
        self.assertIsNone(raw["FI-033"])
        report = (output / "report.json").read_text(encoding="utf-8")
        self.assertNotIn("private transport detail", report)
        self.assertEqual(json.loads(report)["arms"]["baseline"]["execution_errors"], {"FeedbackProviderError": 1})


if __name__ == "__main__":
    unittest.main()
