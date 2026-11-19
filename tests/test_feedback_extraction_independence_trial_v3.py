"""Verify that only independence guidance differs in the paired requests."""

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
from job_search_agent.feedback_extraction_independence_trial_v3 import (
    ARMS, CONTRAST_IDS, DEFAULT_CONTRASTS, DEFAULT_GUIDANCE, main,
)
from job_search_agent.feedback_extraction_schema_v3 import TRIAL_SCHEMA
from job_search_agent.feedback_extraction_trial_replay_v3 import DEFAULT_CANDIDATE


ARCHIVE = Path("benchmarks/feedback/live_v3_extraction_trial")
REPLAY = Path("benchmarks/feedback/offline_v3_extraction_evidence")
GUIDANCE = "Synthetic independence-review guidance for the transport test.\n"


def _response():
    return BytesIO(json.dumps({
        "status": "completed",
        "output": [{"type": "message", "content": [{"type": "output_text", "text": '{"clauses": [], "signals": []}'}]}],
    }).encode())


class IndependenceTrialTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(TemporaryDirectory()))
        self.guidance = self.directory / "independence.txt"
        self.guidance.write_text(GUIDANCE, encoding="utf-8")

    def _run(self, output, respond):
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}),
            patch("job_search_agent.feedback.urlopen", side_effect=respond),
            redirect_stderr(StringIO()),
        ):
            return main(["--archive", str(ARCHIVE), "--replay", str(REPLAY), "--output", str(output),
                         "--independence-guidance", str(self.guidance)])

    def test_only_instructions_differ_and_new_cases_receive_only_original_inputs(self):
        payloads = []

        def respond(request, *, timeout):
            self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
            self.assertEqual(request.get_method(), "POST")
            self.assertEqual(timeout, 60)
            payloads.append(json.loads(request.data))
            return _response()

        output = self.directory / "capture"
        self.assertEqual(self._run(output, respond), 0)
        case_ids = (*FOLLOWUP_IDS, *CONTRAST_IDS)
        self.assertEqual(len(payloads), 2 * len(case_ids))
        live_configuration = json.loads((ARCHIVE / "configuration.json").read_bytes())
        strict_configuration = json.loads(Path(
            "benchmarks/feedback/live_v3_extraction_schema_trial/configuration.json"
        ).read_bytes())
        prior_raw = json.loads((ARCHIVE / "candidate.proposals.json").read_bytes())
        prior_validated = json.loads((REPLAY / "candidate.json").read_bytes())
        contrasts = {case["case_id"]: case for case in json.loads(DEFAULT_CONTRASTS.read_bytes())["test_cases"]}
        candidate = DEFAULT_CANDIDATE.read_text(encoding="utf-8").rstrip()
        addendum = DEFAULT_ADDENDUM.read_text(encoding="utf-8")
        schema_guidance = DEFAULT_GUIDANCE.read_text(encoding="utf-8")
        prior_control = candidate + "\n\n" + addendum + "\n\n" + schema_guidance
        direct_control = candidate + "\n\n" + schema_guidance
        self.assertEqual(sha256(prior_control.encode()).hexdigest(), strict_configuration["instructions_sha256"])
        by_arm = {arm: {} for arm in ARMS}

        for index, case_id in enumerate(case_ids):
            first, second = payloads[2 * index:2 * index + 2]
            case_order = ARMS if index % 2 == 0 else tuple(reversed(ARMS))
            by_arm[case_order[0]][case_id], by_arm[case_order[1]][case_id] = first, second
            control, treatment = by_arm["control"][case_id], by_arm["treatment"][case_id]
            self.assertEqual({**control, "instructions": treatment["instructions"]}, treatment)
            known = case_id in FOLLOWUP_IDS
            self.assertEqual(control["instructions"], prior_control if known else direct_control)
            self.assertEqual(treatment["instructions"], control["instructions"] + "\n\n" + GUIDANCE)
            self.assertEqual(control["text"]["format"], {
                "type": "json_schema", "name": "feedback_extraction_v3", "strict": True, "schema": TRIAL_SCHEMA,
            })
            self.assertEqual(control["model"], live_configuration["model"])
            self.assertEqual(control["temperature"], live_configuration["temperature"])
            self.assertIs(control["store"], False)
            model_input = json.loads(control["input"])
            input_fields = {"decision", "original_feedback", "job_context", "hard_rules"}
            self.assertEqual(model_input["hard_rules"], live_configuration["hard_rules"])
            if known:
                self.assertEqual(model_input.keys(), input_fields | {"prior_proposal", "review_findings"})
                self.assertEqual(model_input["prior_proposal"], {
                    "raw": prior_raw[case_id],
                    "validated": {key: prior_validated[case_id][key] for key in ("clauses", "interpretations")},
                })
                self.assertEqual(model_input["review_findings"], {
                    key: prior_validated[case_id][key]
                    for key in ("validation_issues", "evidence_findings", "condition_recoveries")
                })
            else:
                self.assertEqual(model_input, {"hard_rules": live_configuration["hard_rules"], **{
                    key: contrasts[case_id][key] for key in ("decision", "original_feedback", "job_context")
                }})

        configuration_bytes = (output / "configuration.json").read_bytes()
        configuration = json.loads(configuration_bytes)
        report = json.loads((output / "report.json").read_bytes())
        self.assertTrue(configuration["recover_explicit_conditions"])
        self.assertIn("python_version", configuration)
        self.assertEqual(configuration["validator_prompt_version_field"], live_configuration["validator_prompt_version_field"])
        self.assertEqual(configuration["response_schema_sha256"], strict_configuration["response_schema_sha256"]["trial"])
        self.assertEqual(configuration["synthetic_fixture"]["sha256"], sha256(DEFAULT_CONTRASTS.read_bytes()).hexdigest())
        self.assertEqual(report["configuration_sha256"], sha256(configuration_bytes).hexdigest())
        self.assertEqual(report["requests_completed"], 20)
        self.assertEqual(report["paired_input_mismatch_case_ids"], [])
        for arm, result in report["arms"].items():
            self.assertEqual(result["execution_errors"], {})
            for file_key, hash_key in (("raw_proposals_file", "raw_proposals_sha256"), ("validated_file", "validated_sha256"),
                                       ("trace_file", "trace_sha256")):
                self.assertEqual(result[hash_key], sha256((output / result[file_key]).read_bytes()).hexdigest())
            trace = json.loads((output / result["trace_file"]).read_bytes())
            self.assertEqual([entry["case_id"] for entry in trace], list(case_ids))
            for entry in trace:
                payload = by_arm[arm][entry["case_id"]]
                self.assertEqual(entry["input_sha256"], _fingerprint(json.loads(payload["input"])))
                self.assertEqual(entry["instructions_sha256"], sha256(payload["instructions"].encode()).hexdigest())
                self.assertEqual(entry["response_schema_sha256"], _fingerprint(TRIAL_SCHEMA))

    def test_transport_error_does_not_add_retry_or_drop_other_pairs(self):
        calls = 0

        def respond(request, *, timeout):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("private connection failure")
            return _response()

        output = self.directory / "capture"
        self.assertEqual(self._run(output, respond), 1)
        self.assertEqual(calls, 20)
        report_text = (output / "report.json").read_text(encoding="utf-8")
        self.assertNotIn("private connection failure", report_text)
        report = json.loads(report_text)
        self.assertEqual(report["requests_completed"], 20)
        self.assertEqual(report["arms"]["control"]["execution_errors"], {"FeedbackProviderError": 1})
        self.assertEqual(report["paired_input_mismatch_case_ids"], [])


if __name__ == "__main__":
    unittest.main()
