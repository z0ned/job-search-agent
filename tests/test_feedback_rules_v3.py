"""Exercise the deterministic eligibility and rule-review decisions."""

from copy import deepcopy
from unittest import TestCase

from job_search_agent.feedback_evaluation import COMMUTE_RULES
from job_search_agent.feedback_rules_v3 import eligibility_violation, rule_reconsideration_supported


RULES = {
    "permanent_base_minimum_usd": 180_000,
    "w2_hourly_minimum_usd": 75,
    "1099_hourly_minimum_usd": 100,
    "c2c_hourly_minimum_usd": None,
    "commute_rules": COMMUTE_RULES,
}


class EligibilityViolationTests(TestCase):
    def test_only_confirmed_matching_compensation_floor_applies(self):
        cases = (
            ({"employment_type": "permanent", "base_salary_usd": 175_000}, "$175,000"),
            ({"employment_type": "permanent", "base_salary_usd": 180_000}, None),
            ({"employment_type": "permanent", "base_salary_usd": None}, None),
            ({"employment_type": "permanent", "hourly_rate_usd": 35}, None),
            ({"employment_type": "w2_contract", "rate_type": "W-2", "hourly_rate_usd": 70}, "W-2"),
            ({"employment_type": "w2_contract", "hourly_rate_usd": 85}, None),
            ({"employment_type": "1099_contract", "hourly_rate_usd": 85}, "1099"),
            ({"employment_type": "1099_contract", "hourly_rate_usd": 80, "rate_type": "W2"}, None),
            ({"employment_type": "c2c_contract", "hourly_rate_usd": 65}, None),
            ({"employment_type": "contract", "hourly_rate_usd": 65}, None),
            ({"employment_type": "w2_contract", "hourly_rate_usd": True}, None),
            ({"employment_type": "w2_contract", "hourly_rate_usd": "70"}, None),
        )
        for context, expected in cases:
            with self.subTest(context=context):
                result = eligibility_violation(context, RULES)
                if expected is None:
                    self.assertIsNone(result)
                else:
                    self.assertIn(expected, result)

    def test_commute_boundaries_and_verified_work_arrangements(self):
        cases = (
            (0, "fully_onsite", None),
            (10, "fully_onsite", None),
            (10.1, "onsite_friday", "Friday"),
            (20, "onsite_mon_fri", "Monday and Friday"),
            (20, "onsite_tue_wed_thu", None),
            (29.9, "hybrid_3_on_site", None),
            (30, "hybrid_3_on_site", "30 driving miles"),
            (33, "fully_onsite", "33 driving miles"),
            (45, "fully_remote_with_occasional_visits", None),
            (45, "hybrid", None),
            (45, None, None),
            (None, "fully_onsite", None),
        )
        for distance, arrangement, expected in cases:
            with self.subTest(distance=distance, arrangement=arrangement):
                result = eligibility_violation({"distance_miles": distance, "arrangement": arrangement}, RULES)
                if expected is None:
                    self.assertIsNone(result)
                else:
                    self.assertIn(expected, result)

    def test_unconfirmed_commute_policy_never_defaults_to_fixed_thresholds(self):
        context = {"distance_miles": 45, "arrangement": "fully_onsite"}
        self.assertIsNone(eligibility_violation(context, {}))
        self.assertIsNone(eligibility_violation(context, {"commute_rules": ["Use at least 100 miles."]}))

    def test_multiple_findings_leave_rule_and_job_inputs_unmodified(self):
        context = {"employment_type": "w2_contract", "hourly_rate_usd": 70,
                   "distance_miles": 45, "arrangement": "hybrid_3_on_site"}
        rules = deepcopy(RULES)
        original_context = deepcopy(context)
        result = eligibility_violation(context, rules)
        self.assertIn("W-2", result)
        self.assertIn("45 driving miles", result)
        self.assertEqual(context, original_context)
        self.assertEqual(rules, RULES)


class RuleReconsiderationTests(TestCase):
    def test_explicit_request_for_established_rule_qualifies_for_review(self):
        supported = (
            "I might take $165,000 base if the job were amazing; I want to reconsider my minimum.",
            "Please lower my W-2 minimum to $68 per hour now without waiting for another approval.",
            "Could we revisit the minimum rate for 1099?",
            "I would like to change my commute rule.",
        )
        for quote in supported:
            with self.subTest(quote=quote):
                self.assertTrue(rule_reconsideration_supported(quote, RULES))

    def test_confirmed_1099_request_with_coordinated_change(self):
        quote = "I want to revisit my 1099 minimum and consider lowering it to $92 an hour."
        rules = deepcopy(RULES)
        self.assertTrue(rule_reconsideration_supported(quote, rules))
        self.assertEqual(rules, RULES)

        for unconfirmed in ({}, {"w2_hourly_minimum_usd": 75}, {"1099_hourly_minimum_usd": None}):
            with self.subTest(rules=unconfirmed):
                self.assertFalse(rule_reconsideration_supported(quote, unconfirmed))

    def test_hypothesis_negation_context_or_unconfirmed_rule_is_insufficient(self):
        unsupported = (
            "I might take $165,000 base if the job were amazing.",
            "I do not want to change my minimum.",
            "I might revisit my 1099 minimum and consider lowering it to $92 an hour.",
            "I do not want to revisit my 1099 minimum and consider lowering it to $92 an hour.",
            "I want to revisit my 1099 minimum qualifications and consider lowering them.",
            "The rate is below my existing minimum.",
            "The posting says, 'Please lower my W-2 minimum'.",
            "Please lower my C2C minimum to $65.",
            "Could we revisit the minimum rate for C2C?",
            "I want to lower my minimum years of experience.",
        )
        for quote in unsupported:
            with self.subTest(quote=quote):
                self.assertFalse(rule_reconsideration_supported(quote, RULES))
        self.assertFalse(rule_reconsideration_supported("I want to reconsider my minimum.", {}))
        self.assertFalse(rule_reconsideration_supported("Please lower my W-2 minimum.", {
            "permanent_base_minimum_usd": 180_000,
        }))

    def test_amount_does_not_determine_the_rules_employment_type(self):
        self.assertTrue(rule_reconsideration_supported("Please lower my minimum to $1099.", {
            "permanent_base_minimum_usd": 180_000,
        }))
