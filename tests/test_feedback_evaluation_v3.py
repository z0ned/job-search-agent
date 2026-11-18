"""Verify v3 capture, scoring diagnostics, and API-independent replay."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from job_search_agent.feedback_evaluation import GoldSuite
from job_search_agent.feedback_evaluation_v3 import evaluate_v3, main
from job_search_agent.feedback_v3 import interpret_feedback_v3


FEEDBACK = "I don't want a career in quota-carrying sales."
CASE_ID = "FI-040"
CASE = {
    "case_id": CASE_ID, "decision": "rejected", "original_feedback": FEEDBACK,
    "job_context": {"title": "Sales Director"},
    "expected_review_status": "PENDING_APPROVAL", "expected_hard_constraint_action": "UNCHANGED",
    "expected_interpretations": [{
        "dimension": "career_category", "feature": "quota-carrying sales careers",
        "polarity": "negative", "strength": "strong",
        "scope": {"type": "career_category", "value": "quota_sales"}, "evidence_quote": FEEDBACK,
    }],
}
SUITE = GoldSuite("fixture", "a" * 64, [CASE], {})


def _proposal():
    return {
        "clauses": [{"role": "preference", "quote": FEEDBACK, "detail": None}],
        "signals": [{
            "clause_index": 0, "dimension": "career_category", "display_label": "quota-bearing sales",
            "polarity": "negative", "strength": "strong",
            "scope": {"type": "career_category", "referent": "quota_carrying_sales", "qualifiers": []},
            "condition": None,
        }],
    }


def _provider(proposal=None):
    return Mock(model="snapshot", **{"propose.return_value": _proposal() if proposal is None else proposal})


def _prediction(proposal=None):
    return interpret_feedback_v3(CASE["decision"], FEEDBACK, CASE["job_context"],
                                 provider=_provider(proposal), hard_rules={})


class V3EvaluationTests(unittest.TestCase):
    def test_automated_diagnostics_separate_labels_registry_coverage_and_safety_reviews(self):
        prediction = _prediction()
        report = evaluate_v3(SUITE, {CASE_ID: prediction})
        self.assertEqual(report["score_status"], "provisional_automation")
        self.assertEqual(report["literal_signal_recall"]["correct"], 0)
        self.assertEqual(report["registered_identity_recall"]["correct"], 1)
        self.assertEqual(report["registry_coverage"]["correct"], 1)
        self.assertEqual(report["negative_career_proposals_requiring_review"], 1)
        self.assertEqual(report["mechanical_evidence_grounding"]["correct"], 1)
        altered = deepcopy(prediction)
        altered["interpretations"][0]["evidence"][0]["end"] -= 1
        report = evaluate_v3(SUITE, {CASE_ID: altered})
        self.assertEqual(report["mechanical_evidence_grounding"]["correct"], 0)

    def test_candidate_stays_outside_registered_scoring(self):
        proposal = _proposal()
        proposal["signals"][0]["display_label"] = "sales jobs with an individual quota"
        report = evaluate_v3(SUITE, {CASE_ID: _prediction(proposal)})
        self.assertEqual(report["registry_coverage"]["correct"], 0)
        self.assertEqual(report["registered_identity_recall"]["correct"], 0)
        self.assertEqual(report["negative_career_proposals_requiring_review"], 1)

    def test_incomplete_or_fabricated_saved_predictions_cannot_complete(self):
        with self.assertRaisesRegex(ValueError, "match the entire fixture"):
            evaluate_v3(SUITE, {})
        prediction = _prediction()
        prediction["interpretations"][0]["application_status"] = "learned"
        report = evaluate_v3(SUITE, {CASE_ID: prediction})
        self.assertEqual(report["execution_errors"], {"InvalidPrediction": 1})

    def test_captures_two_independent_passes_and_keeps_rejected_raw_proposal(self):
        bad = _proposal()
        bad["clauses"][0]["quote"] = "invented phrase"
        first, second = _provider(), _provider(bad)
        output = Path(self.enterContext(TemporaryDirectory())) / "capture"
        stdout, stderr = StringIO(), StringIO()
        with (
            patch("job_search_agent.feedback_evaluation_v3.load_v3_suite", return_value=SUITE),
            patch("job_search_agent.feedback_evaluation_v3.OpenAIFeedbackProviderV3", side_effect=[first, second]) as init,
            redirect_stdout(stdout), redirect_stderr(stderr),
        ):
            status = main(["fixture.json", "--model", "snapshot", "--temperature", "0.1", "--save-predictions", str(output)])
        self.assertEqual(status, 1)
        self.assertEqual(init.call_count, 2)
        for provider in (first, second):
            provider.propose.assert_called_once_with(CASE["decision"], FEEDBACK, CASE["job_context"], {})
        self.assertIn("Pass 2/2 saved", stderr.getvalue())
        report = json.loads(stdout.getvalue())
        self.assertTrue(report["two_complete_passes"])
        self.assertFalse(report["repeated_pass_requirement_met"])
        self.assertFalse(report["quality_gates_passed"])
        self.assertEqual(report["automated_stability"]["unverified_case_ids"], [CASE_ID])
        config_bytes = (output / "configuration.json").read_bytes()
        config = json.loads(config_bytes)
        self.assertEqual(report["configuration"]["capture_configuration_sha256"], sha256(config_bytes).hexdigest())
        self.assertEqual(config["evaluation_source"]["temperature_override"], 0.1)
        self.assertEqual(len(config["evaluation_source"]["proposal_schema_sha256"]), 64)
        self.assertEqual(len(config["inputs"][CASE_ID]["job_context_sha256"]), 64)
        raw_file = (output / "pass-2.proposals.json").read_bytes()
        self.assertEqual(report["runs"][1]["proposals_sha256"], sha256(raw_file).hexdigest())
        self.assertEqual(json.loads(raw_file), {CASE_ID: bad})
        validated = json.loads((output / "pass-2.json").read_bytes())[CASE_ID]
        self.assertTrue(validated["validation_issues"])
        self.assertEqual(validated["interpretations"], [])

    def test_replay_never_uses_provider_and_needs_review_for_gate_success(self):
        output = Path(self.enterContext(TemporaryDirectory()))
        args = ["fixture.json"]
        for pass_number in (1, 2):
            path = output / f"pass-{pass_number}.json"
            path.write_text(json.dumps({CASE_ID: _prediction()}), encoding="utf-8")
            args.extend(["--predictions", str(path)])
        stdout = StringIO()
        with (
            patch("job_search_agent.feedback_evaluation_v3.load_v3_suite", return_value=SUITE),
            patch("job_search_agent.feedback_evaluation_v3.OpenAIFeedbackProviderV3") as provider,
            redirect_stdout(stdout),
        ):
            status = main(args)
        provider.assert_not_called()
        self.assertEqual(status, 1)
        report = json.loads(stdout.getvalue())
        self.assertTrue(report["repeated_pass_requirement_met"])
        self.assertFalse(report["quality_gates_passed"])
        self.assertEqual(report["automated_stability"]["literal_unchanged"]["correct"], 1)

    def test_adjudicated_replay_can_pass_without_an_api_call(self):
        output = Path(self.enterContext(TemporaryDirectory()))
        args = ["fixture.json"]
        for pass_number in (1, 2):
            prediction_path = output / f"pass-{pass_number}.json"
            data = json.dumps({CASE_ID: _prediction()}).encode()
            prediction_path.write_bytes(data)
            verdict = {
                "equivalent_pairs": [[1, 1]], "resolution_adequate": True, "clear_dimension_scope_correct": True,
                "evidence_grounded": True, "unsupported_career_downgrade": False, "unauthorized_hard_rule_action": False,
            }
            verdict_path = output / f"pass-{pass_number}.adjudication.json"
            verdict_path.write_text(json.dumps({
                "suite_sha256": SUITE.sha256, "predictions_sha256": sha256(data).hexdigest(),
                "reviewer": "Reviewer", "cases": {CASE_ID: verdict},
            }), encoding="utf-8")
            args.extend(["--predictions", str(prediction_path), "--adjudications", str(verdict_path)])
        stdout = StringIO()
        with (
            patch("job_search_agent.feedback_evaluation_v3.load_v3_suite", return_value=SUITE),
            patch.dict("job_search_agent.feedback_evaluation_v3.HIGH_RISK_CASE_IDS", {"gold": (CASE_ID,)}),
            patch("job_search_agent.feedback_evaluation_v3.OpenAIFeedbackProviderV3") as provider,
            redirect_stdout(stdout),
        ):
            status = main(args)
        provider.assert_not_called()
        self.assertEqual(status, 0)
        report = json.loads(stdout.getvalue())
        self.assertEqual(report["score_status"], "adjudicated")
        self.assertTrue(report["quality_gates_passed"])
        self.assertEqual(report["runs"][0]["adjudication"]["high_risk_routing_controls"], {CASE_ID: True})


if __name__ == "__main__":
    unittest.main()
