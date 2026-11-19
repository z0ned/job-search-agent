"""Verify the review-only trial sends identical live inputs and captures both validations."""

from contextlib import redirect_stderr
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
from job_search_agent.feedback_review_only_trial_v3 import DEFAULT_SUITE, _load_cases, _run_case, main


def _load(path):
    return json.loads(path.read_bytes())


def _hash(path):
    return sha256(path.read_bytes()).hexdigest()


def _response(proposal):
    return BytesIO(json.dumps({"status": "completed", "output": [{
        "type": "message", "content": [{"type": "output_text", "text": json.dumps(proposal)}],
    }]}).encode())


class ReviewOnlyTrialTests(TestCase):
    def test_all_requests_share_model_prompt_schema_and_source_only_input(self):
        suite, high_risk, _ = _load_cases(DEFAULT_SUITE)
        cases = {case["case_id"]: case for case in suite.cases}
        schedule = []
        for number in (1, 2):
            for position, case_id in enumerate(cases):
                arms = ("baseline", "candidate") if (position + number) % 2 else ("candidate", "baseline")
                schedule.extend({"pass_number": number, "case_id": case_id, "arm": arm, "stage": "classifier"}
                                for arm in arms)
        wire = []
        responses = []

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
                    self.assertEqual(network.call_count, 48)
            report = _load(output / "report.json")
            configuration = _load(output / "configuration.json")
            trace = _load(output / "request-trace.json")
            self.assertEqual(report["requests_attempted"], 48)
            self.assertEqual(report["requests_completed"], 48)
            self.assertEqual(report["request_errors"], 0)
            self.assertEqual(report["configuration_sha256"], _hash(output / "configuration.json"))
            self.assertEqual(report["request_trace_sha256"], _hash(output / "request-trace.json"))
            self.assertEqual(configuration["planned_requests"], schedule)
            self.assertEqual(configuration["high_risk_case_ids"], high_risk)
            for position in range(0, len(wire), 2):
                self.assertEqual(wire[position], wire[position + 1])
            raw_arrays = {}
            outcome_arrays = {}
            for entry in report["passes"]:
                directory = output / entry["directory"]
                self.assertEqual(entry["repairs_sha256"], _hash(directory / entry["repairs_file"]))
                self.assertEqual(set(_load(directory / entry["repairs_file"])), set(cases))
                for arm, hashes in entry["arms"].items():
                    raw_file = directory / hashes["raw_proposals_file"]
                    outcome_file = directory / hashes["validated_file"]
                    self.assertEqual(hashes["raw_proposals_sha256"], _hash(raw_file))
                    self.assertEqual(hashes["validated_sha256"], _hash(outcome_file))
                    raw_arrays[entry["pass_number"], arm] = _load(raw_file)
                    outcome_arrays[entry["pass_number"], arm] = _load(outcome_file)
            for index, (planned, raw, row, payload) in enumerate(zip(schedule, responses, trace, wire, strict=True), 1):
                self.assertEqual({key: row[key] for key in planned}, planned)
                self.assertEqual(row["request_number"], index)
                self.assertEqual(row["input_sha256"], _fingerprint(json.loads(payload["input"])))
                self.assertEqual(row["response_sha256"], _fingerprint(raw))
                key = planned["pass_number"], planned["arm"]
                case_id = planned["case_id"]
                self.assertEqual(raw_arrays[key][case_id], raw)
                self.assertEqual(row["validated_sha256"], _fingerprint(outcome_arrays[key][case_id]))

    def test_same_raw_proposal_gets_candidate_only_condition_recovery(self):
        suite, _, _ = _load_cases(DEFAULT_SUITE)
        quote = "I would enjoy sorting sensor arrays provided it takes at most one shift per week"
        bound = "at most one shift per week"
        case = {"case_id": "synthetic", "decision": "interested", "job_context": {}, "original_feedback": quote + "."}
        proposal = {"clauses": [{"role": "preference", "quote": quote, "detail": None}], "signals": [{
            "clause_index": 0, "condition": None, "dimension": "role_responsibilities",
            "display_label": "Sorting sensor arrays", "polarity": "positive", "strength": "mild",
            "scope": {"type": "role_feature", "referent": "sort sensor arrays", "qualifiers": [{
                "kind": "time_share", "source": "feedback", "quote": bound, "value": bound,
            }]},
        }]}
        provider = Mock()
        provider.propose.return_value = proposal
        trace = []
        _, before, baseline_repairs = _run_case(case, suite.hard_rules, provider, {"arm": "baseline"}, trace)
        raw, after, candidate_repairs = _run_case(case, suite.hard_rules, provider, {"arm": "candidate"}, trace)
        self.assertEqual(provider.propose.call_count, 2)
        self.assertIs(raw, proposal)
        self.assertIsNone(proposal["signals"][0]["condition"])
        self.assertIsNone(before["interpretations"][0]["condition"])
        self.assertEqual(after["interpretations"][0]["condition"]["quote"], "provided it takes at most one shift per week")
        self.assertEqual(after["interpretations"][0]["scope"]["qualifiers"], [])
        self.assertEqual(before["review_status"], after["review_status"])
        self.assertEqual(before["hard_constraint_action"], after["hard_constraint_action"])
        self.assertFalse(after["hard_constraints_mutated"])
        self.assertEqual(after["interpretations"][0]["application_status"], "held_for_review")
        self.assertEqual(baseline_repairs, {})
        self.assertEqual(len(candidate_repairs["condition_recoveries"]), 1)
        self.assertEqual(trace[0]["response_sha256"], trace[1]["response_sha256"])

    def test_provider_error_is_captured_without_a_retry(self):
        suite, _, _ = _load_cases(DEFAULT_SUITE)
        provider = Mock()
        provider.propose.side_effect = FeedbackProviderError("Mock transport failure")
        trace = []
        raw, outcome, repairs = _run_case(suite.cases[0], suite.hard_rules, provider, {"arm": "candidate"}, trace)
        provider.propose.assert_called_once()
        self.assertIsNone(raw)
        self.assertEqual(outcome, {"evaluation_error": "FeedbackProviderError"})
        self.assertEqual(repairs, outcome)
        self.assertEqual(len(trace), 1)
        self.assertEqual(trace[0]["status"], "error")
        self.assertEqual(trace[0]["error_type"], "FeedbackProviderError")
        self.assertIsNone(trace[0]["validation_seconds"])
