"""Check benchmark scoring with independently controlled test predictions."""

from copy import deepcopy
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
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
        self.assertEqual(suite.sha256, "fbf6872f847d533871ad2db7d3412a324504171f057f56ae7a8f1f8f48311523")
        self.assertIsNone(suite.hard_rules["c2c_hourly_minimum_usd"])
        self.assertNotIn("frozen_phase_approval_is_held", suite.hard_rules)

    def test_holdout_uses_new_feedback_and_the_same_hard_rules(self):
        gold = load_suite(GOLD_FILE)
        holdout_path = Path("benchmarks/feedback/holdout_cases_v2.json")
        holdout = load_suite(holdout_path, expected_count=12)
        self.assertEqual(holdout.version, "2.0-holdout")
        self.assertEqual(holdout.hard_rules, gold.hard_rules)
        self.assertTrue(
            {case["original_feedback"] for case in holdout.cases}.isdisjoint(
                case["original_feedback"] for case in gold.cases
            )
        )

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

    def test_semantic_match_keeps_literal_scores_and_original_labels_separate(self):
        original = load_suite(GOLD_FILE)
        example = next(case for case in original.cases if case["case_id"] == "FI-040")
        expected = example["expected_interpretations"][0]
        alias = {**expected, "feature": "quota-bearing sales", "scope": {
            "type": "career_category", "value": "quota_carrying_sales",
        }}
        suite = GoldSuite(original.version, original.sha256, [example], original.hard_rules)
        output = prediction("PENDING_APPROVAL", alias, original_feedback=example["original_feedback"])
        report = evaluate(suite, {"FI-040": output})
        self.assertEqual(report["explicit_signal_recall"]["correct"], 0)
        self.assertFalse(report["quality_gates"]["no_unmatched_career_category_downgrades"])
        semantic = report["semantic"]
        self.assertEqual(semantic["explicit_signal_recall"]["correct"], 1)
        self.assertTrue(semantic["quality_gates"]["no_unsupported_career_category_downgrades"])
        pair = semantic["cases"][0]["correct_signals"][0]
        self.assertEqual(pair["expected"]["feature_id"], pair["actual"]["feature_id"])
        self.assertEqual(pair["expected"]["feature_label"], "quota-carrying sales careers")
        self.assertEqual(pair["actual"]["feature_label"], "quota-bearing sales")
        original_prediction = {"FI-040": {**output, "interpretations": [expected]}}
        self.assertEqual(_consistency(suite, [original_prediction, {"FI-040": output}], semantic=True)[
            "changed_case_ids"
        ], [])

    def test_scope_and_condition_mismatches_are_paired_without_inflating_credit(self):
        expected = signal(condition="only at this employer")
        different_scope = signal(
            scope={"type": "compensation_context", "value": "this_job_pay"},
            condition="only at this employer",
        )
        different_condition = signal()
        suite = GoldSuite("fixture", "", [
            case("scope", "PENDING_APPROVAL", expected),
            case("condition", "PENDING_APPROVAL", expected),
        ], {})
        output = {
            "scope": prediction("PENDING_APPROVAL", different_scope),
            "condition": prediction("PENDING_APPROVAL", different_condition),
        }
        semantic = evaluate(suite, output)["semantic"]
        self.assertEqual(semantic["explicit_signal_recall"]["correct"], 0)
        self.assertEqual(semantic["missed_signals"], 2)
        self.assertEqual(semantic["extra_signals"], 2)
        self.assertEqual(semantic["incorrectly_scoped_signals"], 1)
        self.assertEqual(semantic["incorrectly_conditioned_signals"], 1)
        self.assertIn("incorrect_scope", semantic["cases"][0]["failure_classifications"])
        self.assertIn("incorrect_condition", semantic["cases"][1]["failure_classifications"])

    def test_career_downgrade_requires_matching_dimension_and_complete_grounding(self):
        original = load_suite(GOLD_FILE)
        example = next(case for case in original.cases if case["case_id"] == "FI-040")
        expected = example["expected_interpretations"][0]
        suite = GoldSuite(original.version, original.sha256, [example], original.hard_rules)
        for changed in (
            {"dimension": "role_responsibilities"},
            {"evidence_quote": "quota-carrying sales"},
            {"scope": {"type": "career_category", "value": "sales"}},
        ):
            with self.subTest(changed=changed):
                output = prediction("PENDING_APPROVAL", {**expected, **changed},
                                    original_feedback=example["original_feedback"])
                semantic = evaluate(suite, {"FI-040": output})["semantic"]
                self.assertFalse(semantic["quality_gates"]["no_unsupported_career_category_downgrades"])
                self.assertEqual(semantic["unsupported_career_category_downgrades"], 1)

    def test_multiset_penalizes_duplicate_signals(self):
        expected = signal()
        suite = GoldSuite("fixture", "", [case("clear", "PENDING_APPROVAL", expected)], {})
        output = prediction("PENDING_APPROVAL", expected, deepcopy(expected))
        semantic = evaluate(suite, {"clear": output})["semantic"]
        self.assertEqual(semantic["explicit_signal_recall"]["accuracy"], 1)
        self.assertEqual(semantic["signal_precision"]["accuracy"], 0.5)
        self.assertEqual(semantic["cases"][0]["extra_signals"][0]["index"], 1)

    def test_replay_cannot_authorize_wrong_action_or_hide_mutation_in_extra_fields(self):
        expected = signal()
        suite = GoldSuite("fixture", "", [case("clear", "PENDING_APPROVAL", expected)], {})
        for output in (
            prediction("PENDING_APPROVAL", expected, hard_constraint_action="REPORT_EXISTING_ELIGIBILITY_VIOLATION"),
            prediction("PENDING_APPROVAL", expected, hard_constraints_mutated=0),
            prediction("PENDING_APPROVAL", {**expected, "update_hard_rule": True}),
        ):
            with self.subTest(output=output):
                semantic = evaluate(suite, {"clear": output})["semantic"]
                self.assertFalse(semantic["quality_gates"]["all_hard_rule_actions_authorized"])

    def test_live_capture_writes_provenance_and_validated_and_raw_case_outputs(self):
        original = load_suite(GOLD_FILE)
        example = next(case for case in original.cases if case["case_id"] == "FI-040")
        suite = GoldSuite(original.version, original.sha256, [example], original.hard_rules)
        valid = {
            "review_status": "PENDING_APPROVAL",
            "interpretations": [{"condition": None, **signal} for signal in example["expected_interpretations"]],
            "hard_constraint_action": "UNCHANGED",
            "clarification_question": None,
            "profile_fact_candidate": None,
        }
        invalid = {**valid, "hard_constraints_mutated": True}
        provider = Mock(model="snapshot", **{"propose.side_effect": [valid, invalid]})
        directory = Path(self.enterContext(TemporaryDirectory())) / "capture"
        stdout = StringIO()
        with (
            patch("job_search_agent.feedback_evaluation.load_suite", return_value=suite) as loader,
            patch("job_search_agent.feedback_evaluation.OpenAIFeedbackProvider", return_value=provider) as init,
            redirect_stdout(stdout),
        ):
            status = main(["holdout.json", "--expected-count", "1", "--model", "snapshot", "--temperature", "0.1",
                           "--save-predictions", str(directory)])
        self.assertEqual(status, 1)
        loader.assert_called_once_with(Path("holdout.json"), expected_count=1)
        init.assert_called_once_with(model="snapshot", temperature=0.1)
        self.assertEqual(provider.propose.call_count, 2)
        configuration = json.loads((directory / "configuration.json").read_bytes())
        self.assertEqual(configuration["suite_sha256"], suite.sha256)
        self.assertEqual(configuration["evaluation_source"]["requested_model"], "snapshot")
        self.assertEqual(configuration["evaluation_source"]["temperature_override"], 0.1)
        self.assertEqual(configuration["evaluation_source"]["passes"], 2)
        self.assertIn("prompt_version", configuration["evaluation_source"])
        self.assertEqual(len(configuration["evaluation_source"]["instructions_sha256"]), 64)
        self.assertEqual(len(configuration["evaluation_source"]["proposal_schema_sha256"]), 64)
        self.assertTrue(configuration["started_at_utc"].endswith("+00:00"))
        self.assertIn("python_version", configuration)
        self.assertFalse(json.loads((directory / "pass-1.json").read_bytes())["FI-040"]["hard_constraints_mutated"])
        self.assertEqual(json.loads((directory / "pass-2.json").read_bytes())["FI-040"],
                         {"evaluation_error": "FeedbackOutputError"})
        raw = (directory / "pass-2.proposals.json").read_bytes()
        self.assertEqual(json.loads(raw), {"FI-040": invalid})
        report = json.loads(stdout.getvalue())
        self.assertEqual(report["runs"][1]["proposals_sha256"], sha256(raw).hexdigest())

    def test_original_fixture_cli_disallows_case_count_override(self):
        with redirect_stderr(StringIO()) as stderr, self.assertRaises(SystemExit) as raised:
            main([str(GOLD_FILE), "--expected-count", "1"])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("original gold suite requires 50 scenarios", stderr.getvalue())
