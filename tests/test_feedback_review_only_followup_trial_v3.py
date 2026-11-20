"""Verify the sealed follow-up evaluates both paths from each source-only request."""

from contextlib import redirect_stderr
from copy import deepcopy
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

from job_search_agent.feedback import FeedbackProviderError
from job_search_agent.feedback_evaluation_v3 import _fingerprint
from job_search_agent.feedback_extraction_v3 import _INSTRUCTIONS, _PROPOSAL_SCHEMA
from job_search_agent.feedback_review_only_followup_trial_v3 import DEFAULT_SUITE, _load_cases, _run_case, main
from job_search_agent.feedback_review_only_trial_v3 import DEFAULT_SUITE as ARCHIVED_SUITE
from job_search_agent.feedback_review_only_trial_v3 import _load_cases as _load_archived_cases


def _load(path):
    return json.loads(path.read_bytes())


def _hash(path):
    return sha256(path.read_bytes()).hexdigest()


def _response(proposal):
    return BytesIO(json.dumps({"status": "completed", "output": [{
        "type": "message", "content": [{"type": "output_text", "text": json.dumps(proposal)}],
    }]}).encode())


class ReviewOnlyFollowupTests(TestCase):
    def test_two_passes_capture_one_source_only_response_for_both_paths(self):
        suite, high_risk, _ = _load_cases(DEFAULT_SUITE)
        cases = {case["case_id"]: case for case in suite.cases}
        schedule = [{"pass_number": number, "case_id": case_id, "stage": "classifier"}
                    for number in (1, 2) for case_id in cases]
        wire, responses = [], []

        def respond(request, *, timeout):
            self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
            case = cases[schedule[len(wire)]["case_id"]]
            payload = json.loads(request.data)
            self.assertEqual(json.loads(payload["input"]), {
                **{key: case[key] for key in ("decision", "original_feedback", "job_context")},
                "hard_rules": suite.hard_rules,
            })
            self.assertEqual(payload["model"], "gpt-5.4-2026-03-05")
            self.assertEqual(payload["temperature"], 0.1)
            self.assertIs(payload["store"], False)
            self.assertEqual(payload["instructions"], _INSTRUCTIONS)
            self.assertEqual(payload["text"]["format"], {
                "type": "json_schema", "name": "feedback_extraction_v3", "strict": True, "schema": _PROPOSAL_SCHEMA,
            })
            wire.append(payload)
            proposal = {"signals": [], "clauses": [{
                "role": "context", "quote": case["original_feedback"], "detail": f"Mock response {len(wire)}",
            }]}
            responses.append(proposal)
            return _response(proposal)

        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "capture"
            with patch.dict("os.environ", {"OPENAI_API_KEY": "unused"}), redirect_stderr(StringIO()):
                with patch("job_search_agent.feedback.urlopen", side_effect=respond) as network:
                    self.assertEqual(main(["--output", str(output)]), 0)
                    self.assertEqual(network.call_count, 24)
            report = _load(output / "report.json")
            configuration = _load(output / "configuration.json")
            trace = _load(output / "request-trace.json")
            self.assertEqual(report["requests_attempted"], len(schedule))
            self.assertEqual(report["requests_completed"], len(schedule))
            self.assertEqual(report["request_errors"], 0)
            self.assertEqual(report["configuration_sha256"], _hash(output / "configuration.json"))
            self.assertEqual(report["request_trace_sha256"], _hash(output / "request-trace.json"))
            self.assertEqual(configuration["planned_requests"], schedule)
            self.assertEqual(configuration["high_risk_case_ids"], high_risk)
            self.assertIs(configuration["shared_raw_responses"], True)
            raw_arrays, outcome_arrays = {}, {}
            for entry in report["passes"]:
                directory = output / entry["directory"]
                number = entry["pass_number"]
                self.assertEqual(entry["repairs_sha256"], _hash(directory / entry["repairs_file"]))
                self.assertEqual(set(_load(directory / entry["repairs_file"])), set(cases))
                self.assertEqual((directory / "baseline.proposals.json").read_bytes(),
                                 (directory / "candidate.proposals.json").read_bytes())
                for arm, hashes in entry["arms"].items():
                    raw_file = directory / hashes["raw_proposals_file"]
                    outcome_file = directory / hashes["validated_file"]
                    self.assertEqual(hashes["raw_proposals_sha256"], _hash(raw_file))
                    self.assertEqual(hashes["validated_sha256"], _hash(outcome_file))
                    raw_arrays[number, arm] = _load(raw_file)
                    outcome_arrays[number, arm] = _load(outcome_file)
            for index, (planned, raw, row, payload) in enumerate(zip(schedule, responses, trace, wire, strict=True), 1):
                self.assertEqual({key: row[key] for key in planned}, planned)
                self.assertEqual(row["request_number"], index)
                self.assertEqual(row["input_sha256"], _fingerprint(json.loads(payload["input"])))
                self.assertEqual(row["response_sha256"], _fingerprint(raw))
                number, case_id = planned["pass_number"], planned["case_id"]
                for arm in ("baseline", "candidate"):
                    self.assertEqual(raw_arrays[number, arm][case_id], raw)
                    self.assertEqual(row["validations"][arm]["validated_sha256"],
                                     _fingerprint(outcome_arrays[number, arm][case_id]))

    def test_two_repairs_change_only_candidate_on_saved_responses(self):
        suite, _, _ = _load_archived_cases(ARCHIVED_SUITE)
        cases = {case["case_id"]: case for case in suite.cases}
        path = Path("benchmarks/feedback/live_v3_review_only_trial/pass-1/candidate.proposals.json")
        proposals = _load(path)
        trace = []
        for case_id in ("RO3-004", "RO3-011"):
            with self.subTest(case_id=case_id):
                proposal = proposals[case_id]
                before = deepcopy(proposal)
                provider = Mock()
                provider.propose.return_value = proposal
                raw, outcomes, repairs = _run_case(cases[case_id], suite.hard_rules, provider, {"case_id": case_id}, trace)
                provider.propose.assert_called_once()
                self.assertIs(raw, proposal)
                self.assertEqual(raw, before)
                baseline, candidate = outcomes["baseline"], outcomes["candidate"]
                self.assertEqual(baseline["review_status"], candidate["review_status"])
                self.assertEqual(baseline["hard_constraint_action"], candidate["hard_constraint_action"])
                self.assertFalse(candidate["hard_constraints_mutated"])
                self.assertTrue(all(signal["application_status"] == "held_for_review"
                                    for signal in candidate["interpretations"]))
                self.assertEqual(trace[-1]["response_sha256"], _fingerprint(proposal))
                self.assertEqual(trace[-1]["validations"]["candidate"]["validated_sha256"], _fingerprint(candidate))
                if case_id == "RO3-004":
                    self.assertIsNotNone(repairs["posting_verification_repair"])
                    self.assertNotEqual(baseline["clarification_question"], candidate["clarification_question"])
                    self.assertIn("overnight", candidate["clarification_question"].casefold())
                    self.assertEqual(baseline["interpretations"], candidate["interpretations"])
                else:
                    self.assertTrue(repairs["travel_count_repairs"])
                    self.assertNotEqual(baseline["interpretations"][0]["scope"], candidate["interpretations"][0]["scope"])
                    self.assertEqual(baseline["interpretations"][1], candidate["interpretations"][1])

    def test_provider_failure_is_shared_without_retrying(self):
        suite, _, _ = _load_archived_cases(ARCHIVED_SUITE)
        provider = Mock()
        provider.propose.side_effect = FeedbackProviderError("Mock transport failure")
        trace = []
        raw, outcomes, repairs = _run_case(suite.cases[0], suite.hard_rules, provider, {}, trace)
        provider.propose.assert_called_once()
        self.assertIsNone(raw)
        self.assertEqual(repairs, {"evaluation_error": "FeedbackProviderError"})
        self.assertEqual(outcomes, {arm: repairs for arm in ("baseline", "candidate")})
        self.assertEqual(len(trace), 1)
        self.assertEqual(trace[0]["status"], "error")
        self.assertEqual(trace[0]["error_type"], "FeedbackProviderError")
        self.assertEqual(trace[0]["validations"], {arm: {"status": "skipped", "elapsed_seconds": None}
                                                  for arm in ("baseline", "candidate")})
