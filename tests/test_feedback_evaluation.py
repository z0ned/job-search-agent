"""Check benchmark scoring with independently controlled test predictions."""

from copy import deepcopy
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from job_search_agent.feedback import FeedbackProviderError
from job_search_agent.feedback_evaluation import (
    GOLD_FILE,
    GoldSuite,
    _consistency,
    collect_predictions,
    evaluate,
    load_suite,
    main,
)


def signal(**overrides):
    return {
        "dimension": "compensation",
        "feature": "compensation amount",
        "polarity": "negative",
        "strength": "mild",
        "scope": {"type": "compensation_context", "value": "permanent"},
        "evidence_quote": "pay is low",
        **overrides,
    }


def case(case_id, review_status, *signals, hard_action="UNCHANGED"):
    return {
        "case_id": case_id,
        "decision": "rejected",
        "original_feedback": "The pay is low.",
        "job_context": {"distance_miles": 8, "pay": {"amount": 10}},
        "expected_review_status": review_status,
        "expected_interpretations": list(signals),
        "expected_hard_constraint_action": hard_action,
        "expected_category_interest_change": False,
    }


def prediction(review_status, *signals, **overrides):
    return {
        "review_status": review_status,
        "interpretations": list(signals),
        "hard_constraint_action": "UNCHANGED",
        "hard_constraints_mutated": False,
        "original_feedback": "The pay is low.",
        **overrides,
    }


class EvaluationTests(unittest.TestCase):
    def test_loads_all_original_labels_and_freezes_input_bytes(self):
        suite = load_suite(GOLD_FILE)
        self.assertEqual(suite.version, "1.0-draft")
        self.assertEqual(len(suite.cases), 50)
        self.assertEqual(sum(len(case["expected_interpretations"]) for case in suite.cases), 57)
        self.assertEqual(len(suite.sha256), 64)
        self.assertIsNone(suite.hard_rules["c2c_hourly_minimum_usd"])
        self.assertNotIn("frozen_phase_approval_is_held", suite.hard_rules)

    def test_gold_requires_exact_count_and_unique_case_ids(self):
        directory = self.enterContext(TemporaryDirectory())
        file = Path(directory) / "fixture.json"
        source = json.loads(GOLD_FILE.read_text(encoding="utf-8"))
        source["test_cases"] = [source["test_cases"][0]] * 2
        file.write_text(json.dumps(source), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "expected 50 scenarios, found 2"):
            load_suite(file)
        with self.assertRaisesRegex(ValueError, "case 2: case_id must be a unique"):
            load_suite(file, expected_count=2)

    def test_provider_receives_original_inputs_without_expected_answers(self):
        example = case("clear", "PENDING_APPROVAL", signal())
        suite = GoldSuite("fixture", "", [example], {})
        interpreter = Mock(return_value=prediction("PENDING_APPROVAL", signal()))
        report = evaluate(suite, collect_predictions(suite, interpreter))
        interpreter.assert_called_once_with("rejected", example["original_feedback"], example["job_context"])
        self.assertEqual(report["exact_case_match"]["accuracy"], 1)
        self.assertEqual(report["explicit_signal_recall"]["accuracy"], 1)
        self.assertTrue(report["quality_gates_passed"])

    def test_scores_route_hard_action_and_evidence_independently(self):
        no_grounding = signal(evidence_quote="the fixture did not say this")
        suite = GoldSuite("fixture", "", [
            case("clear", "PENDING_APPROVAL", signal()),
            case("needs-question", "NEEDS_CLARIFICATION"),
            case("profile-review", "PROFILE_FACT_REVIEW", hard_action="REPORT_EXISTING_ELIGIBILITY_VIOLATION"),
        ], {})
        predictions = {
            "clear": prediction("PENDING_APPROVAL", no_grounding),
            "needs-question": prediction("NEEDS_CLARIFICATION"),
            "profile-review": prediction("PROFILE_FACT_REVIEW", profile_fact_candidate="Verify rule violation"),
        }
        report = evaluate(suite, predictions)
        self.assertEqual(report["route_accuracy"]["correct"], 2)
        self.assertEqual(report["ambiguity_and_profile_fact_routing"]["correct"], 0)
        self.assertEqual(report["expected_hard_action_accuracy"]["correct"], 2)
        self.assertEqual(report["unsupported_evidence_quotes"], 1)
        self.assertEqual(report["explicit_signal_recall"]["correct"], 1)
        self.assertEqual(report["clear_case_dimension_and_scope_accuracy"]["correct"], 1)
        self.assertFalse(report["quality_gates_passed"])
        self.assertNotIn(no_grounding["evidence_quote"], json.dumps(report))

    def test_counts_unsupported_downgrades_and_does_not_skip_execution_errors(self):
        suite = GoldSuite("fixture", "", [case("clear", "PENDING_APPROVAL", signal())], {})
        downgrade = signal(scope={"type": "career_category", "value": "consulting"})
        bad = {"clear": prediction("PENDING_APPROVAL", downgrade, hard_constraints_mutated=True)}
        private_detail = "Private provider error detail"
        failed = collect_predictions(suite, Mock(side_effect=FeedbackProviderError(private_detail)))
        wrong = evaluate(suite, bad)
        errors = evaluate(suite, failed)
        self.assertFalse(wrong["quality_gates"]["no_unmatched_career_category_downgrades"])
        self.assertFalse(wrong["quality_gates"]["hard_constraints_unchanged"])
        self.assertEqual(wrong["missed_signals"], 1)
        self.assertEqual(wrong["false_positive_signals"], 1)
        self.assertEqual(errors["scenario_count"], 1)
        self.assertEqual(errors["execution_errors"], {"FeedbackProviderError": 1})
        self.assertNotIn(private_detail, json.dumps(errors))
        self.assertEqual(_consistency(suite, [bad, failed])["unverified_case_ids"], ["clear"])

    def test_rejects_incomplete_prediction_passes(self):
        suite = GoldSuite("fixture", "", [case("clear", "PENDING_APPROVAL", signal())], {})
        with self.assertRaisesRegex(ValueError, "match the full gold case set"):
            evaluate(suite, {})

    def test_requires_exact_original_text_for_case_match(self):
        suite = GoldSuite("fixture", "", [case("clear", "PENDING_APPROVAL", signal())], {})
        result = prediction("PENDING_APPROVAL", signal(), original_feedback="The pay is low.\n")
        report = evaluate(suite, {"clear": result})
        self.assertEqual(report["exact_case_match"]["correct"], 0)
        self.assertFalse(report["failures"][0]["original_feedback_preserved"])
        self.assertEqual(report["evidence_grounding"]["correct"], 1)

    def test_replays_native_contract_with_a_held_conditional_signal(self):
        native = load_suite(GOLD_FILE)
        conditional = deepcopy(native.cases[-1])
        self.assertEqual(conditional["case_id"], "FI-050")
        conditional["expected_interpretations"][0]["condition"] = "if the job were amazing"
        suite = GoldSuite(native.version, native.sha256, [conditional], native.hard_rules)
        saved = {
            "FI-050": {
                "review_status": "PROFILE_FACT_REVIEW",
                "interpretations": conditional["expected_interpretations"],
                "clarification_question": None,
                "profile_fact_candidate": "Review the proposed rule change separately.",
                "hard_constraint_action": "REQUIRES_SEPARATE_EXPLICIT_RULE_CONFIRMATION",
                "hard_constraints_mutated": False,
                "original_feedback": conditional["original_feedback"],
                "model": "fixture-model",
                "prompt_version": "fixture-prompt",
            },
        }
        directory = self.enterContext(TemporaryDirectory())
        predictions = Path(directory) / "predictions.json"
        predictions.write_text(json.dumps(saved), encoding="utf-8")
        stdout = StringIO()
        with patch("job_search_agent.feedback_evaluation.load_suite", return_value=suite), redirect_stdout(stdout):
            main(["--predictions", str(predictions), "--predictions", str(predictions)])
        report = json.loads(stdout.getvalue())
        self.assertEqual(report["evaluation_source"]["mode"], "replay")
        self.assertTrue(report["repeated_pass_requirement_met"])
        self.assertEqual(report["runs"][0]["exact_case_match"]["correct"], 1)
        self.assertEqual(report["runs"][0]["profile_fact_routing"]["correct"], 1)
        self.assertEqual(report["consistency"]["changed_case_ids"], [])

    def test_consistency_ignores_signal_order_but_counts_changed_fields(self):
        other = signal(feature="benefits")
        suite = GoldSuite("fixture", "", [case("clear", "PENDING_APPROVAL", signal(), other)], {})
        first = {"clear": prediction("PENDING_APPROVAL", signal(), other)}
        reversed_order = {"clear": prediction("PENDING_APPROVAL", other, signal())}
        different = deepcopy(first)
        different["clear"]["interpretations"][0]["strength"] = "strong"
        self.assertEqual(_consistency(suite, [first, reversed_order])["changed_case_ids"], [])
        self.assertEqual(_consistency(suite, [first, different])["changed_case_ids"], ["clear"])
