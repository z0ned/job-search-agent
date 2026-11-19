from contextlib import redirect_stderr
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from job_search_agent.feedback_evaluation_v3 import _fingerprint
from job_search_agent.feedback_focused_context_trial_v3 import (
    DEFAULT_ARCHIVE,
    DEFAULT_NOVEL,
    MODEL,
    RESPONSE_SCHEMA_NAME,
    TEMPERATURE,
    _FOCUS_SCHEMA,
    _load_cases,
    _planned_requests,
    main,
)


def _load(path):
    return json.loads(path.read_bytes())


def _response(body):
    return BytesIO(json.dumps({"status": "completed", "output": [{
        "type": "message", "content": [{"type": "output_text", "text": json.dumps(body)}],
    }]}).encode())


def _mock_result(case, focus):
    role = focus["expected_roles"][0]
    detail = "What specifically appeals to you about this opportunity?" if role == "vague_reaction" else None
    signal = None
    if role == "preference":
        reference = next(row for row in case["expected_interpretations"] if row["evidence_quote"] in focus["quote"])
        signal = {key: reference[key] for key in ("dimension", "polarity", "strength")}
        signal.update(display_label=reference["feature"], condition=None, scope={
            "type": reference["scope"]["type"], "referent": reference["scope"]["value"], "qualifiers": [],
        })
    return {"role": role, "detail": detail, "signal": signal}


class FocusedContextTrialTests(TestCase):
    def setUp(self):
        self.scratch = Path(self.enterContext(TemporaryDirectory()))
        self.instructions = self.scratch / "focus.txt"
        self.instructions.write_text("Review one exact source quote.\n", encoding="utf-8")
        cases, self.rules, _ = _load_cases(DEFAULT_NOVEL, DEFAULT_ARCHIVE)
        self.cases = {row["case_id"]: row for row in cases}
        self.planned = _planned_requests(cases)

    def _run(self, output, response, archive=DEFAULT_ARCHIVE):
        args = ["--archive", str(archive), "--output", str(output), "--instructions", str(self.instructions)]
        with patch.dict("os.environ", {"OPENAI_API_KEY": "mock"}, clear=False):
            with redirect_stderr(StringIO()), patch("job_search_agent.feedback.urlopen", side_effect=response) as network:
                return main(args), network.call_count

    def test_mock_requests_use_only_source_and_one_exact_quote_and_bind_outputs(self):
        output = self.scratch / "live"
        payloads = []

        def respond(request, *, timeout):
            identity = self.planned[len(payloads)]
            case = self.cases[identity["case_id"]]
            focus = case["focus_quotes"][identity["focus_index"]]
            payload = json.loads(request.data)
            payloads.append(payload)
            self.assertEqual(json.loads(payload["input"]), {
                **{key: case[key] for key in ("decision", "original_feedback", "job_context")},
                "hard_rules": self.rules, "focus_quote": focus["quote"],
            })
            self.assertEqual(payload["model"], MODEL)
            self.assertEqual(payload["temperature"], TEMPERATURE)
            self.assertIs(payload["store"], False)
            self.assertEqual(payload["instructions"], self.instructions.read_text())
            self.assertEqual(payload["text"]["format"], {
                "type": "json_schema", "name": RESPONSE_SCHEMA_NAME, "strict": True, "schema": _FOCUS_SCHEMA,
            })
            return _response(_mock_result(case, focus))

        self.assertEqual(self._run(output, respond), (0, 22))
        report = _load(output / "report.json")
        config = _load(output / "configuration.json")
        trace = _load(output / "request-trace.json")
        self.assertEqual(report["requests_attempted"], report["requests_completed"])
        self.assertEqual(report["requests_completed"], config["expected_requests"])
        self.assertEqual(config["planned_requests"], self.planned)
        self.assertEqual(report["configuration_sha256"], sha256((output / "configuration.json").read_bytes()).hexdigest())
        self.assertEqual(report["request_trace_sha256"], sha256((output / "request-trace.json").read_bytes()).hexdigest())
        for payload, row, scheduled in zip(payloads, trace, self.planned, strict=True):
            case_id, focus_index = row["case_id"], row["focus_index"]
            directory = output / f"pass-{row['pass_number']}"
            record = _load(directory / "focused.responses.json")[case_id][focus_index]
            self.assertEqual({key: row[key] for key in scheduled}, scheduled)
            self.assertEqual(row["response_sha256"], _fingerprint(record["response"]))
            self.assertEqual(row["input_sha256"], _fingerprint(json.loads(payload["input"])))
        for number in (1, 2):
            directory = output / f"pass-{number}"
            raw = _load(directory / "focused.proposals.json")
            validated = _load(directory / "focused.json")
            self.assertEqual(len(raw["FI-041"]["signals"]), 2)
            self.assertEqual(len(validated["FI-041"]["interpretations"]), 2)
            self.assertEqual(len(raw["FC3-002"]["signals"]), 1)
            self.assertEqual(validated["FC3-004"]["review_status"], "NEEDS_CLARIFICATION")
            self.assertEqual(validated["FH3-002"]["hard_constraint_action"], "REQUIRES_SEPARATE_EXPLICIT_RULE_CONFIRMATION")
            self.assertTrue(all(not row["hard_constraints_mutated"] for row in validated.values()))

    def test_keeps_raw_inconsistent_response_and_rejects_the_partial_case_without_retries(self):
        output = self.scratch / "invalid"
        attempts = []

        def respond(request, *, timeout):
            identity = self.planned[len(attempts)]
            case = self.cases[identity["case_id"]]
            attempts.append(identity)
            result = _mock_result(case, case["focus_quotes"][identity["focus_index"]])
            if len(attempts) == 1:
                result["role"] = "context"
            return _response(result)

        self.assertEqual(self._run(output, respond), (1, 22))
        directory = output / "pass-1"
        failed, other = _load(directory / "focused.responses.json")["FI-041"]
        self.assertEqual(failed["response"]["role"], "context")
        self.assertIsNotNone(failed["response"]["signal"])
        self.assertIn("issue", failed)
        self.assertNotIn("issue", other)
        self.assertIsNone(_load(directory / "focused.proposals.json")["FI-041"])
        self.assertEqual(_load(directory / "focused.json")["FI-041"], {"evaluation_error": "InvalidFocusResult"})
        self.assertEqual(len(_load(output / "pass-2/focused.json")["FI-041"]["interpretations"]), 2)

    def test_rejects_changed_archived_inventory_before_creating_output(self):
        archive = self.scratch / "archive"
        copytree(DEFAULT_ARCHIVE, archive)
        inventory = archive / "pass-2/accounting.inventory.json"
        inventory.write_bytes(inventory.read_bytes() + b"\n")
        output = self.scratch / "invalid-archive"
        self.assertEqual(self._run(output, AssertionError("must not call network"), archive=archive), (2, 0))
        self.assertFalse(output.exists())
