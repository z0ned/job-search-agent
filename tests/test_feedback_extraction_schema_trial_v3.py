"""Test the paired schema trial through its mocked Responses API transport."""

from contextlib import redirect_stderr
from copy import deepcopy
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from job_search_agent.feedback_evaluation_v3 import _fingerprint
from job_search_agent.feedback_extraction_followup_v3 import DEFAULT_ADDENDUM, FOLLOWUP_IDS
from job_search_agent.feedback_extraction_schema_trial_v3 import ARMS, main
from job_search_agent.feedback_extraction_schema_v3 import TRIAL_SCHEMA
from job_search_agent.feedback_extraction_trial_replay_v3 import DEFAULT_CANDIDATE
from job_search_agent.feedback_extraction_v3 import _PROPOSAL_SCHEMA


ARCHIVE = Path("benchmarks/feedback/live_v3_extraction_trial")
REPLAY = Path("benchmarks/feedback/offline_v3_extraction_evidence")
GUIDANCE = "Synthetic shared schema-review guidance.\n"


def _response(proposal):
    return BytesIO(json.dumps({
        "status": "completed",
        "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(proposal)}]}],
    }).encode())


class ExtractionSchemaTrialTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(TemporaryDirectory()))
        self.guidance = self.directory / "guidance.txt"
        self.guidance.write_text(GUIDANCE, encoding="utf-8")

    def _run(self, output, respond):
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}),
            patch("job_search_agent.feedback.urlopen", side_effect=respond),
            redirect_stderr(StringIO()),
        ):
            return main(["--archive", str(ARCHIVE), "--replay", str(REPLAY), "--output", str(output),
                         "--schema-guidance", str(self.guidance)])

    def test_transport_uses_the_same_payload_except_for_the_response_schema(self):
        output = self.directory / "capture"
        payloads = []
        control_before = deepcopy(_PROPOSAL_SCHEMA)

        def respond(request, *, timeout):
            self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
            self.assertEqual(request.get_method(), "POST")
            self.assertEqual(timeout, 60)
            payload = json.loads(request.data)
            payloads.append(payload)
            return _response({"clauses": [], "signals": []})

        self.assertEqual(self._run(output, respond), 0)
        self.assertEqual(_PROPOSAL_SCHEMA, control_before)
        self.assertEqual(len(payloads), 2 * len(FOLLOWUP_IDS))
        live_configuration = json.loads((ARCHIVE / "configuration.json").read_bytes())
        raw = json.loads((ARCHIVE / "candidate.proposals.json").read_bytes())
        prior = json.loads((REPLAY / "candidate.json").read_bytes())
        instructions = (
            DEFAULT_CANDIDATE.read_text(encoding="utf-8").rstrip() + "\n\n"
            + DEFAULT_ADDENDUM.read_text(encoding="utf-8") + "\n\n" + GUIDANCE
        )
        by_arm = {arm: {} for arm in ARMS}
        for index, case_id in enumerate(FOLLOWUP_IDS):
            first, second = payloads[2 * index:2 * index + 2]
            arms = ARMS if index % 2 == 0 else tuple(reversed(ARMS))
            by_arm[arms[0]][case_id], by_arm[arms[1]][case_id] = first, second
            self.assertEqual(by_arm["control"][case_id]["text"]["format"]["schema"], _PROPOSAL_SCHEMA)
            self.assertEqual(by_arm["trial"][case_id]["text"]["format"]["schema"], TRIAL_SCHEMA)
            comparison = deepcopy(first)
            comparison["text"]["format"]["schema"] = second["text"]["format"]["schema"]
            self.assertEqual(comparison, second)
            self.assertEqual(first["instructions"], instructions)
            self.assertEqual(first["model"], live_configuration["model"])
            self.assertEqual(first["temperature"], live_configuration["temperature"])
            self.assertIs(first["store"], False)
            self.assertEqual(first["text"]["format"]["name"], "feedback_extraction_v3")
            model_input = json.loads(first["input"])
            self.assertEqual(model_input.keys(), {
                "decision", "original_feedback", "job_context", "hard_rules", "prior_proposal", "review_findings",
            })
            self.assertEqual(model_input["hard_rules"], live_configuration["hard_rules"])
            self.assertEqual(model_input["prior_proposal"], {
                "raw": raw[case_id], "validated": {key: prior[case_id][key] for key in ("clauses", "interpretations")},
            })
            self.assertEqual(model_input["review_findings"], {
                key: prior[case_id][key] for key in ("validation_issues", "evidence_findings", "condition_recoveries")
            })

        configuration_bytes = (output / "configuration.json").read_bytes()
        configuration = json.loads(configuration_bytes)
        report = json.loads((output / "report.json").read_bytes())
        self.assertTrue(configuration["recover_explicit_conditions"])
        self.assertEqual(report["configuration_sha256"], sha256(configuration_bytes).hexdigest())
        self.assertEqual(report["requests_completed"], 2 * len(FOLLOWUP_IDS))
        for arm, result in report["arms"].items():
            self.assertEqual(result["execution_errors"], {})
            for key, sha_key in (("validated_file", "validated_sha256"), ("raw_proposals_file", "raw_proposals_sha256"),
                                 ("trace_file", "trace_sha256")):
                artifact = (output / result[key]).read_bytes()
                self.assertEqual(result[sha_key], sha256(artifact).hexdigest())
            trace = json.loads((output / result["trace_file"]).read_bytes())
            self.assertEqual([entry["case_id"] for entry in trace], list(FOLLOWUP_IDS))
            for entry in trace:
                payload = by_arm[arm][entry["case_id"]]
                self.assertEqual(entry["input_sha256"], _fingerprint(json.loads(payload["input"])))
                self.assertEqual(entry["response_schema_sha256"], _fingerprint(payload["text"]["format"]["schema"]))

    def test_captures_raw_schema_issues_and_gateway_error_without_retrying(self):
        calls = 0

        def respond(request, *, timeout):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("private connection failure")
            if calls == 2:
                return _response({"clauses": [], "signals": [{
                    "dimension": "employer", "scope": {"type": "career_category", "referent": "team", "qualifiers": []},
                }]})
            return _response({"clauses": [], "signals": []})

        output = self.directory / "capture"
        self.assertEqual(self._run(output, respond), 1)
        self.assertEqual(calls, 2 * len(FOLLOWUP_IDS))
        raw_report = (output / "report.json").read_text(encoding="utf-8")
        self.assertNotIn("private connection failure", raw_report)
        arms = json.loads(raw_report)["arms"]
        self.assertEqual(arms["control"]["execution_errors"], {"FeedbackProviderError": 1})
        self.assertEqual(arms["trial"]["cases_with_raw_schema_issues"], [FOLLOWUP_IDS[0]])
        self.assertEqual(arms["trial"]["raw_schema_issue_count"], 1)
        self.assertEqual(arms["trial"]["validation_issue_count"], 1)


if __name__ == "__main__":
    unittest.main()
