"""Exercise recovery of exact applicability conditions from anchored scope limits."""

from hashlib import sha256
from unittest import TestCase

from job_search_agent.feedback_conditions_v3 import recover_condition


def anchor(feedback, quote, role, *, start=None):
    if start is None:
        start = feedback.index(quote)
    return {"origin": "feedback", "role": role, "source_revision": sha256(feedback.encode()).hexdigest(),
            "start": start, "end": start + len(quote), "quote": quote}


def qualifier(feedback, quote, kind="frequency", *, start=None):
    return {"kind": kind, "value": quote, "quote": quote, "source": "feedback",
            "evidence": anchor(feedback, quote, "qualifier", start=start)}


class ConditionRecoveryTests(TestCase):
    def recover(self, feedback, qualifiers, *, assertion=None, condition=None):
        evidence = anchor(feedback, assertion or feedback, "preference")
        return recover_condition(condition, qualifiers, evidence, feedback, evidence["source_revision"])

    def test_terminal_applicability_markers_preserve_the_complete_bound(self):
        for predicate, bound in (
            ("provided it takes", "at most one shift per week"),
            ("provided that it lasts", "at most 1.5 hours"),
            ("as long as I had to do them", "no more than twice per month"),
            ("only if I perform it", "up to two times per quarter"),
            ("if they occur", "fewer than three times a week"),
        ):
            with self.subTest(predicate=predicate):
                condition_quote = f"{predicate} {bound}"
                assertion = f"I would enjoy running equipment demonstrations, {condition_quote}"
                feedback = f"I have a follow-up. {assertion}. Let me know the schedule."
                original = [qualifier(feedback, bound)]
                recovered, scope = self.recover(feedback, original, assertion=assertion)
                self.assertEqual(scope, [])
                self.assertEqual(len(original), 1)
                self.assertEqual(recovered["kind"], "other")
                self.assertTrue(recovered["value"].endswith(bound))
                self.assertEqual(recovered["quote"], condition_quote)
                self.assertEqual(recovered["evidence"], anchor(feedback, condition_quote, "condition"))

    def test_preserves_other_qualifiers_and_existing_condition(self):
        feedback = "I'd enjoy drafting in CAD only if it takes at most two hours per week."
        scope = [qualifier(feedback, "CAD", "technology"), qualifier(feedback, "at most two hours per week")]
        recovered, remaining = self.recover(feedback, scope)
        self.assertIsNotNone(recovered)
        self.assertEqual(remaining, scope[:1])
        self.assertEqual(len(scope), 2)
        original = {"kind": "other", "value": "existing condition"}
        kept, remaining = self.recover(feedback, scope, condition=original)
        self.assertIs(kept, original)
        self.assertIs(remaining, scope)

    def test_ambiguous_unrelated_or_unmarked_language_stays_unmodified(self):
        for feedback, bound in (
            ("I dislike jobs with billing taking at most one shift a week.", "at most one shift a week"),
            ("I enjoy compiling proposals even if it takes at most one day.", "at most one day"),
            ("I like finding out if it takes at most one day.", "at most one day"),
            ("I would enjoy figuring out if it takes at most one day.", "at most one day"),
            ("I would enjoy writing a report if it takes at most one day?", "at most one day"),
            ("I like the phrase ‘if it takes at most one day’.", "at most one day"),
            ("I would enjoy making brackets only if they confirm if it takes at most one day.", "at most one day"),
            ("I would like gluing panels if the kit takes at most one day to ship.", "at most one day"),
            ("I would enjoy gluing panels if it takes at most one day and the supplier is local.", "at most one day"),
        ):
            with self.subTest(feedback=feedback):
                scope = [qualifier(feedback, bound)]
                condition, remaining = self.recover(feedback, scope)
                self.assertIsNone(condition)
                self.assertIs(remaining, scope)

    def test_partial_or_quoted_assertion_does_not_widen_the_evidence(self):
        assertion = "I would enjoy gluing panels provided it takes at most one day"
        for feedback in (f"{assertion}, except in winter.", f"Vendor note: ‘{assertion}.’"):
            with self.subTest(feedback=feedback):
                scope = [qualifier(feedback, "at most one day")]
                self.assertEqual(self.recover(feedback, scope, assertion=assertion), (None, scope))

    def test_qualifier_must_keep_the_exact_bound_and_original_revision(self):
        bound = "at most one shift per week"
        assertion = f"I would enjoy assembling chairs provided it takes {bound}."
        feedback = f"The packing limit is {bound}. {assertion}"
        exact = qualifier(feedback, bound, start=feedback.rindex(bound))
        invalid_qualifiers = (
            qualifier(feedback, bound),
            qualifier(feedback, "one shift per week", start=feedback.rindex("one shift per week")),
            dict(exact, value="at least one shift per week"),
            dict(exact, evidence=dict(exact["evidence"], source_revision="different")),
            dict(exact, kind="compensation_unit"),
            dict(exact, source="job_context"),
        )
        for bad in invalid_qualifiers:
            with self.subTest(qualifier=bad):
                self.assertEqual(self.recover(feedback, [bad], assertion=assertion), (None, [bad]))
