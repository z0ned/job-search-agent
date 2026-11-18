"""Exercise evidence-review capture without making an API request."""

from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import json

from job_search_agent.feedback_extraction_followup_v3 import FOLLOWUP_IDS, main
from job_search_agent.feedback_extraction_trial_replay_v3 import main as replay


ARCHIVE = "benchmarks/feedback/live_v3_extraction_trial"


class EvidenceFollowupTests(TestCase):
    def test_sends_only_original_inputs_and_prior_proposal_with_diagnostics(self):
        payloads = []

        def response(request, *, timeout):
            payloads.append(json.loads(request.data))
            return StringIO(json.dumps({
                "status": "completed", "output": [{"type": "message", "content": [
                    {"type": "output_text", "text": '{"clauses":[], "signals":[]}'},
                ]}],
            }))

        with (
            TemporaryDirectory() as tmp,
            redirect_stderr(StringIO()),
            patch.dict("os.environ", {"OPENAI_API_KEY": "test-only-key"}),
            patch("job_search_agent.feedback.urlopen", side_effect=response),
        ):
            offline, followup = Path(tmp) / "offline", Path(tmp) / "followup"
            self.assertEqual(replay(["--archive", ARCHIVE, "--output", str(offline)]), 0)
            self.assertEqual(payloads, [])
            self.assertEqual(main(["--archive", ARCHIVE, "--replay", str(offline), "--output", str(followup)]), 0)
            report = json.loads((followup / "report.json").read_bytes())
            proposals = json.loads((followup / "followup.proposals.json").read_bytes())

        self.assertEqual(report["requests_completed"], len(FOLLOWUP_IDS))
        self.assertEqual(len(payloads), len(FOLLOWUP_IDS))
        self.assertEqual(set(proposals), set(FOLLOWUP_IDS))
        for payload in payloads:
            self.assertEqual(payload["model"], "gpt-5.4-2026-03-05")
            self.assertEqual(payload["temperature"], 0.1)
            self.assertIs(payload["store"], False)
            self.assertEqual(payload["text"]["format"]["name"], "feedback_extraction_v3")
            supplied = json.loads(payload["input"])
            self.assertEqual(set(supplied), {
                "decision", "original_feedback", "job_context", "hard_rules", "prior_proposal", "review_findings",
            })
            self.assertEqual(set(supplied["prior_proposal"]), {"raw", "validated"})
            self.assertEqual(set(supplied["review_findings"]), {
                "validation_issues", "evidence_findings", "condition_recoveries",
            })
