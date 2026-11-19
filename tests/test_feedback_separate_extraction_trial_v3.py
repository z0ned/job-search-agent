"""Check the isolated split-extraction trial without making live requests."""

from contextlib import redirect_stderr
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from job_search_agent.feedback_evaluation_v3 import _fingerprint
from job_search_agent.feedback_extraction_trial_v3 import KNOWN_FIXTURES
from job_search_agent.feedback_extraction_v3 import _INSTRUCTIONS, _PROPOSAL_SCHEMA
from job_search_agent.feedback_separate_extraction_trial_v3 import (
    MODEL, NOVEL_IDS, TEMPERATURE, _INVENTORY_NAME, _INVENTORY_SCHEMA, _inventory_diagnostics, _load_cases, main,
)


def _response(proposal):
    return BytesIO(json.dumps({
        "status": "completed",
        "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(proposal)}]}],
    }).encode())


def _load(path):
    return json.loads(path.read_bytes())


class SeparateExtractionTrialTests(unittest.TestCase):
    def setUp(self):
        directory = Path(self.enterContext(TemporaryDirectory()))
        fixture = _load(KNOWN_FIXTURES["gold"])
        fixture["test_cases"] = [{**case, "case_id": case_id}
                                 for case, case_id in zip(fixture["test_cases"][:4], NOVEL_IDS, strict=True)]
        self.novel = directory / "novel.json"
        self.novel.write_text(json.dumps(fixture), encoding="utf-8")
        self.inventory = directory / "inventory.txt"
        self.inventory.write_text("Capture exact evidence.\n", encoding="utf-8")
        self.handoff = directory / "handoff.txt"
        self.handoff.write_text("Classify the verified evidence.\n", encoding="utf-8")
        self.output = directory / "output"

    def _run(self, respond):
        with (patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}),
              patch("job_search_agent.feedback.urlopen", side_effect=respond), redirect_stderr(StringIO())):
            return main(["--novel", str(self.novel), "--inventory-instructions", str(self.inventory),
                         "--handoff-instructions", str(self.handoff), "--output", str(self.output)])

    def test_two_paired_passes_use_shared_classifier_and_verified_source_only_inventory(self):
        received = []

        def respond(request, *, timeout):
            self.assertEqual(timeout, 60)
            self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
            payload = json.loads(request.data)
            received.append(payload)
            if payload["text"]["format"]["name"] == _INVENTORY_NAME:
                quote = json.loads(payload["input"])["original_feedback"]
                return _response({"statements": [
                    {"quote": quote, "role": "preference"},
                    {"quote": "not present in the source feedback", "role": "preference"},
                    {"quote": quote, "role": "context"},
                ]})
            return _response({"clauses": [], "signals": []})

        self.assertEqual(self._run(respond), 0)
        cfg = _load(self.output / "configuration.json")
        trace = _load(self.output / "request-trace.json")
        report = _load(self.output / "report.json")
        case_list, rules, _ = _load_cases(self.novel)
        cases = {case["case_id"]: case for case in case_list}
        self.assertEqual(len(received), 48)
        self.assertEqual(report["requests_attempted"], 48)
        self.assertEqual(report["requests_completed"], 48)
        self.assertEqual(report["request_errors"], 0)
        self.assertEqual(report["unattempted_requests"], [])
        self.assertEqual(report["origin_input_mismatches"], [])
        for name, key in (("configuration.json", "configuration_sha256"), ("request-trace.json", "request_trace_sha256")):
            self.assertEqual(report[key], sha256((self.output / name).read_bytes()).hexdigest())
        for payload, entry, planned in zip(received, trace, cfg["planned_requests"], strict=True):
            self.assertEqual(planned, {key: entry[key] for key in ("pass_number", "case_id", "arm", "stage")})
            source_case = cases[entry["case_id"]]
            source = {"hard_rules": rules, **{key: source_case[key] for key in ("decision", "original_feedback", "job_context")}}
            self.assertEqual(payload["model"], MODEL)
            self.assertEqual(payload["temperature"], TEMPERATURE)
            self.assertIs(payload["store"], False)
            self.assertEqual(entry["origin_input_sha256"], _fingerprint(source))
            actual = json.loads(payload["input"])
            self.assertEqual(entry["input_sha256"], _fingerprint(actual))
            self.assertEqual(entry["status"], "completed")
            schema = _PROPOSAL_SCHEMA
            instructions = _INSTRUCTIONS
            if entry["stage"] == "inventory":
                schema = _INVENTORY_SCHEMA
                instructions = self.inventory.read_text(encoding="utf-8")
            elif entry["arm"] == "split":
                quote = source["original_feedback"]
                source["evidence_inventory"] = [{"quote": quote, "role": "preference", "start": 0, "end": len(quote)}]
                instructions += "\n\n" + self.handoff.read_text(encoding="utf-8")
            self.assertEqual(payload["text"]["format"]["schema"], schema)
            self.assertEqual(payload["instructions"], instructions)
            self.assertEqual(actual, source)
        first_arms = [next(entry["arm"] for entry in trace if entry["pass_number"] == number and entry["case_id"] == "FI-041")
                      for number in (1, 2)]
        self.assertEqual(first_arms, ["baseline", "split"])
        for run in report["passes"]:
            directory = self.output / run["directory"]
            path = directory / run["inventory_file"]
            self.assertEqual(run["inventory_sha256"], sha256(path.read_bytes()).hexdigest())
            self.assertEqual(run["inventory_rejection_count"], 16)
            self.assertEqual(set(_load(path)), set(cases))
            for item in _load(path).values():
                self.assertEqual(len(item["raw"]["statements"]), 3)
                self.assertEqual(len(item["verified"]), 1)
                self.assertEqual(item["rejections"], [{"index": 1, "reason": "quote_not_unique_verbatim"},
                                                      {"index": 2, "reason": "duplicate_span"}])
                self.assertEqual(item["diagnostics"]["inventory_preferences_without_raw_signal"], [0])
            for result in run["arms"].values():
                for file_key, hash_key in (("validated_file", "validated_sha256"), ("raw_proposals_file", "raw_proposals_sha256")):
                    self.assertEqual(result[hash_key], sha256((directory / result[file_key]).read_bytes()).hexdigest())

    def test_transport_failure_skips_only_its_classifier_without_retry_or_fallback(self):
        inventory_calls = 0

        def respond(request, *, timeout):
            nonlocal inventory_calls
            payload = json.loads(request.data)
            if payload["text"]["format"]["name"] == _INVENTORY_NAME:
                inventory_calls += 1
                if inventory_calls == 1:
                    raise OSError("unstable transport")
                return _response({"statements": []})
            return _response({"clauses": [], "signals": []})

        self.assertEqual(self._run(respond), 1)
        report = _load(self.output / "report.json")
        self.assertEqual(inventory_calls, 16)
        self.assertEqual(report["requests_attempted"], 47)
        self.assertEqual(report["requests_completed"], 46)
        self.assertEqual(report["request_errors"], 1)
        self.assertEqual(report["unattempted_requests"], [
            {"arm": "split", "case_id": "FI-041", "pass_number": 1, "stage": "classifier"},
        ])
        self.assertEqual(report["passes"][0]["arms"]["split"]["execution_errors"], {"FeedbackProviderError": 1})
        self.assertEqual(_load(self.output / "pass-1" / "split.json")["FI-041"], {"evaluation_error": "FeedbackProviderError"})
        self.assertIsNone(_load(self.output / "pass-1" / "split.proposals.json")["FI-041"])
        self.assertIsNone(_load(self.output / "pass-1" / "split.inventory.json")["FI-041"]["raw"])

    def test_diagnostics_separate_dropped_inventory_changed_spans_and_unanchored_output(self):
        feedback = "I like the work but not nights. I dislike the office."
        office = "I dislike the office."
        raw = {"clauses": [{"quote": "I like the work", "role": "preference"}, {"quote": "invented"}],
               "signals": [{"clause_index": 0}, {"clause_index": 1}]}
        inventory = [
            {"quote": "I like the work but not nights.", "role": "preference", "start": 0, "end": feedback.index(" I dislike")},
            {"quote": office, "role": "preference", "start": feedback.index(office), "end": len(feedback)},
        ]
        result = _inventory_diagnostics(feedback, inventory, raw, {"interpretations": []})
        self.assertEqual(result["raw_signal_links"], {
            "0": [{"inventory_index": 0, "relationship": "inventory_contains_output"}], "1": [],
        })
        self.assertEqual(result["inventory_preferences_without_raw_signal"], [1])
        self.assertEqual(result["inventory_preferences_without_validated_signal"], [0, 1])
        self.assertEqual(result["raw_signals_without_inventory_preference"], [1])


if __name__ == "__main__":
    unittest.main()
