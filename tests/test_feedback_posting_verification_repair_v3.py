"""Test the source-grounded fallback repair without model requests."""

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase

from job_search_agent.feedback_posting_verification_repair_v3 import repair_posting_verification
from job_search_agent.feedback_v3 import interpret_feedback_v3


def _clause(role, quote, detail=None):
    return {"role": role, "quote": quote, "detail": detail}


def _verify(quote, detail=None):
    return _clause("posting_verification", quote, detail)


def _validate(feedback, clauses, signals=()):
    provider = SimpleNamespace(model="fixture-model", propose=lambda *_: {"clauses": clauses, "signals": list(signals)})
    return interpret_feedback_v3("rejected", feedback, provider=provider)


class PostingVerificationRepairV3Tests(TestCase):
    def assert_unchanged(self, result):
        updated, repair = repair_posting_verification(result)
        self.assertIs(updated, result)
        self.assertIsNone(repair)

    def test_archived_overnight_question_keeps_original_distinction_and_provenance(self):
        path = Path(__file__).resolve().parents[1] / "benchmarks/feedback/live_v3_review_only_trial/pass-1/candidate.json"
        original = json.loads(path.read_bytes())["RO3-004"]
        untouched = deepcopy(original)
        updated, repair = repair_posting_verification(original)
        question = "Could you verify whether the overnight shift is once in a while or the usual schedule?"
        self.assertEqual(updated, {**original, "clarification_question": question})
        self.assertEqual(original, untouched)
        self.assertEqual(repair, {
            "clause_index": original["clauses"][0]["index"],
            "evidence": original["clauses"][0]["evidence"],
            "before": original["clarification_question"],
            "after": question,
        })
        self.assert_unchanged(updated)

    def test_source_paraphrases_and_conflicting_invented_detail(self):
        checks = (
            ("Can you check if weekend coverage is required?", "Could you verify whether weekend coverage is required?"),
            ("Could you find out how often the team rotates coverage?",
             "Could you verify how often the team rotates coverage?"),
            ("How often do Saturday shifts come up?", "How often do Saturday shifts come up?"),
            ("Is the Saturday rotation monthly or weekly?", "Is the Saturday rotation monthly or weekly?"),
            ("I can’t tell from this job description whether the lab operates on Sundays.",
             "Could you verify whether the lab operates on Sundays?"),
        )
        for feedback, question in checks:
            with self.subTest(feedback=feedback):
                result = _validate(feedback, [_verify(feedback, "Verify that cryptocurrency compensation is offered.")])
                updated, repair = repair_posting_verification(result)
                self.assertEqual(updated["clarification_question"], question)
                self.assertEqual(repair["evidence"]["quote"], feedback)

    def test_mixed_reviews_preserve_specific_vague_question_and_independent_signal(self):
        question = "Can you clarify whether the job includes Sundays?"
        positive = "I like leading apprentices."
        proposed = {
            "clause_index": 0, "dimension": "role_responsibilities", "display_label": "Leading apprentices",
            "polarity": "positive", "strength": "mild", "condition": None,
            "scope": {"type": "role_feature", "referent": "leading apprentices", "qualifiers": []},
        }
        result = _validate(f"{positive} {question}", [_clause("preference", positive), _verify(question)], [proposed])
        self.assertEqual(result["review_status"], "PENDING_APPROVAL")
        self.assertEqual(len(result["interpretations"]), 1)
        self.assert_unchanged(result)

        vague = "Something about the commute concerns me."
        for detail in (None, "Which part of the commute concerns you?"):
            with self.subTest(detail=detail):
                result = _validate(f"{vague} {question}", [_clause("vague_reaction", vague, detail), _verify(question)])
                self.assertEqual(result["review_status"], "NEEDS_CLARIFICATION")
                self.assert_unchanged(result)

        fact = "I have an active certification."
        result = _validate(f"{fact} {question}", [_clause("profile_fact", fact), _verify(question)])
        self.assertEqual(result["review_status"], "PROFILE_FACT_REVIEW")
        self.assert_unchanged(result)

    def test_ambiguous_and_distinct_questions_preserve_fallback(self):
        generic = "Can you find out which?"
        self.assert_unchanged(_validate(generic, [_verify(generic, "Check if the contract includes paid travel.")]))
        first, second = "Can you check if weekend coverage is required?", "Is the team also expected to travel?"
        combined = f"{first} {second}"
        self.assert_unchanged(_validate(combined, [_verify(combined)]))
        self.assert_unchanged(_validate(combined, [_verify(first), _verify(second)]))
        for feedback in (
            "Can you check whether it is required?",
            f"{first} Are holidays paid?",
            f"{first} Please also check the onboarding schedule.",
        ):
            with self.subTest(feedback=feedback):
                self.assert_unchanged(_validate(feedback, [_verify(feedback)]))

    def test_malformed_evidence_or_hard_rule_action_never_changes_result(self):
        text = "Can you check whether weekend coverage is required?"
        result = _validate(text, [_verify(text)])
        for change in ({"start": True}, {"end": 1}, {"source_revision": "stale"}, {"quote": "fabricated"}):
            with self.subTest(change=change):
                altered = deepcopy(result)
                altered["clauses"][0]["evidence"].update(change)
                self.assert_unchanged(altered)

        self.assert_unchanged({**result, "hard_constraint_action": "REQUIRES_SEPARATE_EXPLICIT_RULE_CONFIRMATION"})
