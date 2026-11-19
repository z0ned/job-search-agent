"""Check the archived trial boundaries, recoveries, and benchmark controls."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from job_search_agent.feedback_validation_repair_trial_v3 import main


class ValidationRepairTrialTests(TestCase):
    def test_saved_proposals_produce_only_the_expected_repairs_and_findings(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "replay.json"
            with patch("job_search_agent.feedback.urlopen", side_effect=AssertionError("unexpected API request")) as request:
                self.assertEqual(main(["--output", str(path)]), 0)
                request.assert_not_called()
            report = json.loads(path.read_bytes())
        self.assertEqual(report["baseline_record_count"], 180)
        self.assertEqual(report["inference_requests"], 0)
        self.assertTrue(all(batch["baseline_reproduced"] for batch in report["batches"]))
        batches = {batch["id"]: batch["changes"] for batch in report["batches"]}
        self.assertEqual({key: set(cases) for key, cases in batches.items()}, {
            "gold/pass-1": {"FI-033", "FI-042", "FI-048"}, "gold/pass-2": {"FI-033", "FI-042", "FI-048"},
            "regression/pass-1": set(), "regression/pass-2": set(), "holdout/pass-1": set(), "holdout/pass-2": set(),
            "schema/control": {"FI-048", "FT-002"}, "schema/trial": {"FI-048"},
            "independence/control": {"FI-048"}, "independence/treatment": {"FI-048", "FT-002"},
        })
        for batch in ("gold/pass-1", "gold/pass-2"):
            recovery = batches[batch]["FI-042"]
            self.assertTrue(recovery["joined_employer_exception"])
            self.assertNotIn("review_status", recovery["fields"])
            signals = recovery["fields"]["interpretations"]
            self.assertEqual(signals["before"][0], signals["after"][0])
            self.assertEqual(signals["after"][1]["dimension"], "employer")
            self.assertEqual(recovery["fields"]["validation_issues"]["after"], [])
        for batch in ("schema/control", "independence/treatment"):
            recovery = batches[batch]["FT-002"]
            self.assertEqual(recovery["fields"]["review_status"]["after"], recovery["expected_route"])
            signal, = recovery["fields"]["interpretations"]["after"]
            self.assertEqual(len(signal["scope"]["qualifiers"]), 1)
            self.assertEqual([anchor["quote"] for anchor in signal["evidence"]][1:],
                             ["the heart of the role", "built around giving those briefings"])
