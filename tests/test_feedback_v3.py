"""Exercise v3 validation and routing with controlled model proposals."""

from copy import deepcopy
from unittest import TestCase
from unittest.mock import Mock

from job_search_agent.feedback import FeedbackOutputError
from job_search_agent.feedback_evaluation import COMMUTE_RULES
from job_search_agent.feedback_v3 import interpret_feedback_v3


def clause(role, quote, detail=None):
    return {"role": role, "quote": quote, "detail": detail}


def qualifier(kind, value, quote, source="feedback"):
    return {"kind": kind, "value": value, "source": source, "quote": quote}


def signal(index, dimension, scope_type, label, referent, *, polarity="positive", qualifiers=(), condition=None):
    return {
        "clause_index": index,
        "dimension": dimension,
        "display_label": label,
        "polarity": polarity,
        "strength": "mild",
        "scope": {"type": scope_type, "referent": referent, "qualifiers": list(qualifiers)},
        "condition": condition,
    }


class FeedbackV3Tests(TestCase):
    def interpret(self, text, clauses, signals, *, context=None, rules=None):
        provider = Mock(model="fixture-model")
        provider.propose.return_value = {"clauses": clauses, "signals": signals}
        result = interpret_feedback_v3("rejected", text, context, provider=provider, hard_rules=rules)
        provider.propose.assert_called_once_with("rejected", text, context or {}, rules or {})
        self.assertIs(result["hard_constraints_mutated"], False)
        return result

    def test_established_salary_floor_does_not_create_preference(self):
        text = "This could be fun, but $175,000 base is below my established minimum."
        duplicate = signal(
            1, "compensation", "compensation_context", "Below minimum", "quoted base",
            polarity="negative",
        )
        result = self.interpret(
            text,
            [clause("context", "This could be fun"), clause("preference", "$175,000 base is below my established minimum.")],
            [duplicate],
            context={"employment_type": "permanent", "base_salary_usd": 175000},
            rules={"permanent_base_minimum_usd": 180000},
        )
        self.assertEqual(result["interpretations"], [])
        self.assertEqual(result["review_status"], "PROFILE_FACT_REVIEW")
        self.assertEqual(result["hard_constraint_action"], "REPORT_EXISTING_ELIGIBILITY_VIOLATION")
        self.assertEqual(len(result["validation_issues"]), 1)

    def test_weekly_flights_retain_both_travel_qualifiers(self):
        text = "Flying every week would wear me out, though occasional trips are okay."
        result = self.interpret(
            text, [clause("preference", "Flying every week would wear me out"),
                   clause("preference", "occasional trips are okay")],
            [signal(
                0, "work_arrangement", "travel_frequency", "Weekly air travel", "weekly_flights",
                polarity="negative", qualifiers=[
                    qualifier("travel_mode", "air", "Flying"), qualifier("frequency", "weekly", "every week"),
                ],
            ), signal(
                1, "work_arrangement", "travel_frequency", "Occasional business travel", "occasional",
                qualifiers=[qualifier("frequency", "occasional", "occasional")],
            )],
        )
        weekly, occasional = result["interpretations"]
        self.assertEqual(weekly["feature_id"], "work_arrangement.weekly_air_travel")
        self.assertEqual([(q["kind"], q["value"]) for q in weekly["scope"]["qualifiers"]],
                         [("travel_mode", "air"), ("frequency", "weekly")])
        self.assertEqual(occasional["scope"]["qualifiers"][0]["value"], "occasional")
        self.assertEqual(result["validation_issues"], [])

    def test_conditional_rate_keeps_amount_context_and_anchored_condition(self):
        text = "I would pass on $115 an hour for this C2C contract if the client makes me supply the lab kit."
        result = self.interpret(
            text, [clause("preference", text)], [signal(
                0, "compensation", "compensation_context", "Quoted rate", "this C2C rate", polarity="negative",
                qualifiers=[
                    qualifier("amount", "115", "$115"), qualifier("currency", "USD", "$115"),
                    qualifier("compensation_unit", "hour", "an hour"),
                    qualifier("employment_type", "C2C", "employment_type", "job_context"),
                ], condition={
                    "kind": "equipment_required", "value": "client requires candidate to supply the lab kit",
                    "quote": "if the client makes me supply the lab kit",
                },
            )],
            context={"employment_type": "c2c_contract", "hourly_rate_usd": 115},
        )
        proposal, = result["interpretations"]
        self.assertEqual(proposal["feature_id"], "compensation.quoted_rate")
        evidence = proposal["condition"]["evidence"]
        self.assertEqual(text[evidence["start"]:evidence["end"]], "if the client makes me supply the lab kit")
        self.assertEqual(proposal["scope"]["qualifiers"][0]["value"], "115")
        self.assertEqual(result["hard_constraint_action"], "UNCHANGED")

    def test_condition_cannot_be_duplicated_as_independent_preference(self):
        text = "I would enjoy leading workshops if I could deliver them by video."
        condition = "if I could deliver them by video"
        result = self.interpret(
            text, [clause("preference", text), clause("preference", condition)],
            [signal(1, "work_arrangement", "arrangement", "Video workshops", "video"),
             signal(
                 0, "role_responsibilities", "role_feature", "Leading workshops", "workshop leadership",
                 condition={"kind": "delivery_mode_available", "value": "video", "quote": condition},
             )],
        )
        proposal, = result["interpretations"]
        self.assertEqual(proposal["display_label"], "Leading workshops")
        self.assertEqual(len(result["validation_issues"]), 1)

    def test_posting_question_does_not_block_independent_preference(self):
        text = "I like accessibility testing. I need to ask what the posting means by always on."
        result = self.interpret(
            text, [clause("preference", "I like accessibility testing"),
                   clause("posting_verification", "I need to ask what the posting means by always on.")],
            [signal(0, "role_responsibilities", "role_feature", "Accessibility testing", "accessibility testing")],
        )
        self.assertEqual(result["review_status"], "PENDING_APPROVAL")
        proposal, = result["interpretations"]
        self.assertIsNone(proposal["feature_id"])
        self.assertEqual(proposal["identity_status"], "candidate")
        self.assertEqual(proposal["application_status"], "held_for_review")

    def test_positive_preference_survives_profile_review_and_clarification(self):
        positive = "I like data loss investigations."
        cases = (
            ("profile_fact", "I have never run a recovery exercise.", None, "PROFILE_FACT_REVIEW"),
            ("vague_reaction", "Something about this job feels wrong.", "What feels wrong?", "NEEDS_CLARIFICATION"),
        )
        for role, other, detail, route in cases:
            with self.subTest(role=role):
                result = self.interpret(
                    positive + " " + other, [clause("preference", positive), clause(role, other, detail)],
                    [signal(0, "role_responsibilities", "role_feature", "Data loss investigations", "data loss")],
                )
                self.assertEqual(result["review_status"], route)
                self.assertEqual(len(result["interpretations"]), 1)

    def test_commute_rule_uses_verified_context(self):
        text = "I would have to be onsite Mondays and Fridays, and it is 20 miles away."
        result = self.interpret(
            text, [clause("job_fact", text)], [],
            context={"distance_miles": 20, "arrangement": "onsite_mon_fri"},
            rules={"commute_rules": COMMUTE_RULES},
        )
        self.assertEqual(result["review_status"], "PROFILE_FACT_REVIEW")
        self.assertEqual(result["hard_constraint_action"], "REPORT_EXISTING_ELIGIBILITY_VIOLATION")

    def test_invalid_clause_does_not_lose_valid_signal_or_break_its_index(self):
        text = "I like client workshops."
        result = self.interpret(
            text, [clause("preference", "a fabricated quote"), clause("preference", text)],
            [signal(1, "role_responsibilities", "role_feature", "Client workshops", "client workshops")],
        )
        record, = result["clauses"]
        proposed, = result["interpretations"]
        self.assertEqual(record["index"], proposed["clause_index"])
        self.assertEqual(len(result["validation_issues"]), 1)

    def test_wrong_posting_qualifier_is_rejected(self):
        text = "I like hybrid here."
        result = self.interpret(
            text, [clause("preference", text)],
            [signal(
                0, "work_arrangement", "location_arrangement", "Hybrid nearby", "hybrid",
                qualifiers=[qualifier("distance", "6", "distance_miles", "job_context")],
            )],
            context={"distance_miles": 60},
        )
        self.assertEqual(result["interpretations"], [])
        self.assertEqual(result["review_status"], "NEEDS_CLARIFICATION")
        self.assertEqual(len(result["validation_issues"]), 1)

    def test_project_type_does_not_migrate_to_career_registry(self):
        text = "I am not interested in another core-banking replacement transformation."
        result = self.interpret(
            text, [clause("preference", text)],
            [signal(0, "role_responsibilities", "project_type", "Core-banking replacement projects",
                    "core_banking_replacement", polarity="negative")],
        )
        proposal, = result["interpretations"]
        self.assertEqual(proposal["feature_id"], "role.core_banking_replacement_project")
        self.assertIsNone(proposal["career_evidence_review"])

    def test_negative_career_signal_has_no_application_path(self):
        text = "I do not want a career in quota-carrying sales."
        result = self.interpret(
            text, [clause("preference", text)],
            [signal(0, "career_category", "career_category", "Quota-carrying sales careers",
                    "quota_carrying_sales", polarity="negative")],
        )
        proposal, = result["interpretations"]
        self.assertEqual(proposal["career_evidence_review"], "explicit_scope_cue")
        self.assertEqual(proposal["application_status"], "held_for_review")

    def test_rule_mutation_fields_outside_proposal_contract_are_rejected(self):
        provider = Mock(model="malformed")
        provider.propose.return_value = {"clauses": [], "signals": [], "update_rule": True}
        rules = {"w2_hourly_minimum_usd": 75}
        original = deepcopy(rules)
        with self.assertRaises(FeedbackOutputError):
            interpret_feedback_v3("interested", "Please change the minimum.", provider=provider, hard_rules=rules)
        self.assertEqual(rules, original)

    def test_rule_reconsideration_retains_separate_tentative_exception(self):
        exception = "I might take $165,000 base if the job were amazing"
        request = "I want to reconsider my minimum."
        result = self.interpret(
            f"{exception}. {request}",
            [clause("context", exception), clause("rule_reconsideration", request)],
            [],
            rules={"permanent_base_minimum_usd": 180000},
        )
        self.assertEqual(result["review_status"], "PROFILE_FACT_REVIEW")
        self.assertEqual(result["hard_constraint_action"], "REQUIRES_SEPARATE_EXPLICIT_RULE_CONFIRMATION")
        self.assertIn(exception, result["profile_fact_candidate"])
        self.assertEqual(result["interpretations"], [])
