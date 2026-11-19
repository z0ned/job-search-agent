from contextlib import redirect_stderr
from io import BytesIO, StringIO
import json
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from job_search_agent.feedback_evaluation_v3 import _fingerprint
from job_search_agent.feedback_extraction_v3 import _PROPOSAL_SCHEMA
from job_search_agent.feedback_reaction_accounting_trial_v3 import DEFAULT_ARCHIVE, _ACCOUNTING_SCHEMA, _SCHEMA_NAME, main
from job_search_agent.feedback_separate_extraction_trial_v3 import MODEL, TEMPERATURE


def _load(path):
    return json.loads(path.read_bytes())


def _response(body):
    response = {"status": "completed", "output": [{
        "type": "message", "content": [{"type": "output_text", "text": json.dumps(body)}],
    }]}
    return BytesIO(json.dumps(response).encode())


class ReactionAccountingTrialTests(TestCase):
    def setUp(self):
        temporary = self.enterContext(TemporaryDirectory())
        self.scratch = Path(temporary)
        self.instructions = self.scratch / "accounting.txt"
        self.instructions.write_text("Keep the receipts distinct.\n", encoding="utf-8")

    def _run(self, output, response=None, archive=DEFAULT_ARCHIVE):
        args = ["--archive", str(archive), "--output", str(output), "--accounting-instructions", str(self.instructions)]
        with patch.dict("os.environ", {"OPENAI_API_KEY": "" if response is None else "mock"}, clear=False):
            with redirect_stderr(StringIO()), patch("job_search_agent.feedback.urlopen", side_effect=response) as network:
                result = main([*args, "--offline"] if response is None else args)
                if response is None:
                    self.assertEqual(network.call_count, 0)
                return result, network.call_count

    def test_offline_preserves_archived_outputs_and_flags_both_known_omissions(self):
        output = self.scratch / "offline"
        self.assertEqual(self._run(output), (0, 0))
        self.assertEqual(_load(output / "request-trace.json"), [])
        report = _load(output / "report.json")
        self.assertEqual(report["requests_attempted"], 0)
        self.assertEqual(report["requests_completed"], 0)
        for number in (1, 2):
            current = output / f"pass-{number}"
            archived = DEFAULT_ARCHIVE / current.name
            for suffix in (".json", ".proposals.json"):
                self.assertEqual((current / f"accounting{suffix}").read_bytes(), (archived / f"split{suffix}").read_bytes())
            audit = _load(current / "accounting.audit.json")
            praise, distrust = audit["FI-041"]["reactions"]
            self.assertIn("terrific AI advisor", praise["quote"])
            self.assertTrue(praise["flagged"])
            self.assertFalse(distrust["flagged"])
            self.assertEqual(audit["FS3-002"], {"reactions": [], "issues": []})
            self.assertEqual(len(audit["FS3-004"]["reactions"]), 1)
            self.assertFalse((current / "accounting.responses.json").exists())

    def test_mock_live_sends_only_classifier_requests_using_same_saved_evidence(self):
        output = self.scratch / "live"
        archived_inventory = {number: _load(DEFAULT_ARCHIVE / f"pass-{number}" / "split.inventory.json")
                              for number in (1, 2)}
        archived_raw = {number: _load(DEFAULT_ARCHIVE / f"pass-{number}" / "split.proposals.json")
                        for number in (1, 2)}
        archived_config = _load(DEFAULT_ARCHIVE / "configuration.json")
        archived_classifier_requests = [row for row in archived_config["planned_requests"]
                                        if row["arm"] == "split" and row["stage"] == "classifier"]
        payloads = []

        def respond(request, *, timeout):
            position = len(payloads)
            planned = archived_classifier_requests[position]
            payload = json.loads(request.data)
            payloads.append(payload)
            model_input = json.loads(payload["input"])
            number, case_id = planned["pass_number"], planned["case_id"]
            expected = archived_inventory[number][case_id]["verified"]
            self.assertEqual([{k: v for k, v in row.items() if k != "reaction_id"}
                              for row in model_input["evidence_inventory"]], expected)
            self.assertEqual(_fingerprint({k: v for k, v in model_input.items() if k != "evidence_inventory"}),
                             archived_config["case_input_sha256"][case_id])
            self.assertEqual(payload["model"], MODEL)
            self.assertEqual(payload["temperature"], TEMPERATURE)
            self.assertIs(payload["store"], False)
            self.assertEqual(payload["text"]["format"]["name"], _SCHEMA_NAME)
            self.assertEqual(payload["text"]["format"]["schema"], _ACCOUNTING_SCHEMA)
            self.assertTrue(payload["instructions"].endswith(self.instructions.read_text(encoding="utf-8")))
            receipts = [{"reaction_id": row["reaction_id"], "status": "needs_review", "signal_index": None,
                         "reason": "Check whether this preference is independent."}
                        for row in model_input["evidence_inventory"] if row["role"] == "preference"]
            return _response({**archived_raw[number][case_id], "reaction_dispositions": receipts})

        self.assertEqual(self._run(output, respond), (0, 16))
        report = _load(output / "report.json")
        self.assertEqual(report["requests_attempted"], 16)
        self.assertEqual(report["requests_completed"], 16)
        trace = _load(output / "request-trace.json")
        config = _load(output / "configuration.json")
        for payload, row, planned in zip(payloads, trace, config["planned_requests"], strict=True):
            number, case_id = row["pass_number"], row["case_id"]
            current = output / f"pass-{number}"
            response = _load(current / "accounting.responses.json")[case_id]
            standard = _load(current / "accounting.proposals.json")[case_id]
            self.assertEqual({key: response[key] for key in _PROPOSAL_SCHEMA["properties"]}, standard)
            self.assertEqual(row["response_sha256"], _fingerprint(response))
            self.assertEqual(row["input_sha256"], _fingerprint(json.loads(payload["input"])))
            self.assertEqual({key: row[key] for key in planned}, planned)
            self.assertEqual(row["stage"], "classifier")
        for number in (1, 2):
            current = output / f"pass-{number}"
            archived = DEFAULT_ARCHIVE / current.name
            self.assertEqual((current / "accounting.json").read_bytes(), (archived / "split.json").read_bytes())
        first = json.loads(payloads[0]["input"])["evidence_inventory"]
        repeated = json.loads(payloads[8]["input"])["evidence_inventory"]
        self.assertEqual(first, repeated)

    def test_rejects_changed_saved_inventory_before_any_capture(self):
        archive = self.scratch / "copy"
        copytree(DEFAULT_ARCHIVE, archive)
        inventory = archive / "pass-2" / "split.inventory.json"
        inventory.write_bytes(inventory.read_bytes() + b"\n")
        output = self.scratch / "invalid"
        self.assertEqual(self._run(output, archive=archive), (2, 0))
        self.assertFalse(output.exists())
