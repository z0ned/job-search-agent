"""Check the reviewer-backed v3 benchmark gates against local fixtures."""

from copy import deepcopy
from hashlib import sha256
import unittest

from job_search_agent.feedback_adjudication_v3 import _same_condition_form, adjudicate
from job_search_agent.feedback_evaluation import GoldSuite


SUITE_HASH = "a" * 64
PREDICTIONS_HASH = "b" * 64
FEEDBACK = "I don’t want a career in quota-carrying sales."


def _case(case_id="clear", *, route="PENDING_APPROVAL", action="UNCHANGED", signal=True):
    return {
        "case_id": case_id,
        "decision": "rejected",
        "original_feedback": FEEDBACK,
        "job_context": {"employment_type": "permanent"},
        "expected_review_status": route,
        "expected_hard_constraint_action": action,
        "expected_interpretations": [{
            "dimension": "career_category", "feature": "quota-carrying sales",
            "polarity": "negative", "strength": "strong",
            "scope": {"type": "career_category", "value": "quota_sales"},
            "evidence_quote": FEEDBACK,
        }] if signal else [],
    }


def _prediction(case, **overrides):
    route = case["expected_review_status"]
    return {
        "review_status": route,
        "hard_constraint_action": case["expected_hard_constraint_action"],
        "clarification_question": "Which type of sales concerns you?" if route == "NEEDS_CLARIFICATION" else None,
        "profile_fact_candidate": "Review the rule request separately." if route == "PROFILE_FACT_REVIEW" else None,
        "original_feedback": FEEDBACK,
        "hard_constraints_mutated": False,
        "validation_issues": [],
        "interpretations": [{
            "dimension": "career_category", "display_label": "Sales roles with a quota", "feature_id": None,
            "identity_status": "candidate", "polarity": "negative", "strength": "strong",
            "scope": {"type": "career_category", "referent": "quota-carrying sales", "qualifiers": []},
            "condition": None, "application_status": "held_for_review",
            "evidence": [{
                "origin": "feedback", "role": "preference", "start": 0, "end": len(FEEDBACK),
                "source_revision": sha256(FEEDBACK.encode()).hexdigest(), "quote": FEEDBACK,
            }],
        } for _ in case["expected_interpretations"]],
        **overrides,
    }


def _verdict(*, pairs=None, **overrides):
    return {
        "equivalent_pairs": [[1, 1]] if pairs is None else pairs,
        "resolution_adequate": True,
        "clear_dimension_scope_correct": True,
        "evidence_grounded": True,
        "unsupported_career_downgrade": False,
        "unauthorized_hard_rule_action": False,
        **overrides,
    }


def _document(**cases):
    return {"suite_sha256": SUITE_HASH, "predictions_sha256": PREDICTIONS_HASH, "reviewer": "Reviewer", "cases": cases}


def _score(cases, predictions, verdicts, *, high_risk_case_ids=()):
    suite = GoldSuite("fixture", SUITE_HASH, cases, {})
    return adjudicate(suite, predictions, verdicts, predictions_sha256=PREDICTIONS_HASH,
                      high_risk_case_ids=high_risk_case_ids)


class AdjudicationTests(unittest.TestCase):
    def test_legacy_workload_condition_can_be_preserved_as_a_typed_scope_limit(self):
        reference = {"condition": "processing orders takes up most of each day"}
        qualifier = {"kind": "time_share", "value": "most of each day",
                     "source": "feedback", "quote": "most of each day"}
        signal = {"condition": None, "scope": {"qualifiers": [qualifier]}}
        self.assertTrue(_same_condition_form(reference, signal))
        self.assertFalse(_same_condition_form(reference, {"condition": None, "scope": {"qualifiers": []}}))
        self.assertFalse(_same_condition_form({"condition": "the employer supplies equipment"}, signal))

    def test_credits_reviewed_equivalence_for_supported_held_candidate(self):
        case = _case()
        report = _score([case], {"clear": _prediction(case)}, _document(clear=_verdict()))
        self.assertTrue(report["quality_gates_passed"])
        self.assertEqual(report["semantic_precision"]["accuracy"], 1.0)
        self.assertEqual(report["semantic_recall"]["accuracy"], 1.0)
        self.assertEqual(report["cases"][0]["equivalent_pairs"], [[1, 1]])

    def test_rejects_unbound_incomplete_and_invalid_verdicts(self):
        case = _case()
        docs = (
            {**_document(clear=_verdict()), "predictions_sha256": "old"},
            {**_document(clear=_verdict()), "suite_sha256": "old"},
            {**_document(clear=_verdict()), "reviewer": " "},
            _document(),
            _document(clear=_verdict(evidence_grounded=1)),
        )
        for verdicts in docs:
            with self.subTest(doc=verdicts), self.assertRaises(ValueError):
                _score([case], {"clear": _prediction(case)}, verdicts)

    def test_rejects_materially_different_or_non_unique_signal_pairings(self):
        case = _case()
        prediction = _prediction(case)
        prediction["interpretations"].append(deepcopy(prediction["interpretations"][0]))
        prediction["interpretations"][1]["polarity"] = "positive"
        for pairs in ([[1, 2]], [[True, 1]], [[1, 1], [1, 1]], [[1, 0]]):
            with self.subTest(pairs=pairs), self.assertRaises(ValueError):
                _score([case], {"clear": prediction}, _document(clear=_verdict(pairs=pairs)))

    def test_hard_action_grounding_and_unsupported_downgrade_fail_independently(self):
        case = _case()
        prediction = _prediction(case, hard_constraint_action="REPORT_EXISTING_ELIGIBILITY_VIOLATION")
        prediction["interpretations"][0]["evidence"][0]["end"] -= 1
        report = _score([case], {"clear": prediction}, _document(clear=_verdict(unsupported_career_downgrade=True)))
        self.assertTrue(report["quality_gates"]["all_hard_rules_unchanged"])
        self.assertFalse(report["quality_gates"]["all_hard_rule_actions_authorized"])
        self.assertFalse(report["quality_gates"]["no_unsupported_career_downgrades"])
        self.assertFalse(report["quality_gates"]["all_evidence_grounded"])
        self.assertEqual(report["route_accuracy"]["accuracy"], 1.0)

    def test_error_rejection_and_missing_validation_results_fail_closed(self):
        case = _case()
        outputs = (
            {"evaluation_error": "FeedbackProviderError"},
            _prediction(case, validation_issues=[{"field": "signals", "index": 1, "message": "rejected"}]),
            _prediction(case, validation_issues=None),
        )
        for output in outputs:
            with self.subTest(output=output):
                report = _score([case], {"clear": output}, _document(clear=_verdict(pairs=[])))
                self.assertFalse(report["quality_gates"]["all_predictions_without_validation_issues"])
                self.assertFalse(report["quality_gates_passed"])

    def test_special_route_requires_adequate_resolution_and_preserved_preferences(self):
        case = _case("special", route="NEEDS_CLARIFICATION")
        prediction = _prediction(case)
        for verdict in (_verdict(resolution_adequate=False), _verdict(pairs=[])):
            report = _score([case], {"special": prediction}, _document(special=verdict))
            self.assertEqual(report["route_accuracy"]["correct"], 1)
            self.assertFalse(report["quality_gates"]["all_special_routes_resolved_adequately"])
        report = _score([case], {"special": prediction}, _document(special=_verdict()))
        self.assertTrue(report["quality_gates"]["all_special_routes_resolved_adequately"])

    def test_exact_thresholds_and_case_alignment(self):
        cases = [_case(f"clear{i}") for i in range(20)]
        predictions = {case["case_id"]: _prediction(case) for case in cases}
        reviews = {case["case_id"]: _verdict() for case in cases}
        reviews["clear0"] = _verdict(pairs=[], clear_dimension_scope_correct=False)
        report = _score(cases, predictions, _document(**reviews))
        self.assertTrue(report["quality_gates_passed"])
        self.assertEqual(report["semantic_recall"]["accuracy"], 0.95)
        self.assertEqual(report["clear_dimension_scope_accuracy"]["accuracy"], 0.95)

        reviews["clear1"] = _verdict(pairs=[])
        report = _score(cases, predictions, _document(**reviews))
        self.assertFalse(report["quality_gates"]["clear_dimension_scope_at_least_95_percent"])
        self.assertEqual(report["clear_dimension_scope_accuracy"]["correct"], 18)
        self.assertTrue(report["quality_gates"]["semantic_recall_at_least_90_percent"])
        self.assertTrue(report["quality_gates"]["semantic_precision_at_least_90_percent"])

    def test_designated_clear_controls_fail_on_false_escalation(self):
        case = _case()
        output = _prediction(case, review_status="NEEDS_CLARIFICATION", clarification_question="Is that right?")
        document = _document(clear=_verdict())
        report = _score([case], {"clear": output}, document, high_risk_case_ids=("clear",))
        self.assertFalse(report["quality_gates"]["all_designated_high_risk_routes_correct"])
        self.assertEqual(report["high_risk_routing_controls"], {"clear": False})
        self.assertEqual(report["clear_case_false_escalation_case_ids"], ["clear"])
        with self.assertRaisesRegex(ValueError, "must be present"):
            _score([case], {"clear": output}, document, high_risk_case_ids=("missing",))


if __name__ == "__main__":
    unittest.main()
