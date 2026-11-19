"""Check narrow evidence findings for missing near-zero autonomy bounds."""

from copy import deepcopy
from hashlib import sha256
from unittest import TestCase

from job_search_agent.feedback_autonomy_review_v3 import near_zero_autonomy_findings


_FEEDBACK = "This is too junior; I would have almost no decision-making autonomy."
_ASSERTION = "I would have almost no decision-making autonomy."


def _anchor(feedback, quote, role):
    start = feedback.index(quote)
    return {
        "origin": "feedback", "role": role, "quote": quote, "start": start, "end": start + len(quote),
        "source_revision": sha256(feedback.encode()).hexdigest(),
    }


def _case(feedback=_FEEDBACK, quote=_ASSERTION, referent="decision-making autonomy", *, qualifiers=()):
    clauses = [{"index": 2, "evidence": _anchor(feedback, quote, "preference")}]
    signals = [{"clause_index": 2, "dimension": "seniority_scope", "polarity": "negative",
                "display_label": "Avoid roles with almost no decision-making autonomy",
                "scope": {"type": "seniority_feature", "referent": referent, "qualifiers": list(qualifiers)}}]
    return clauses, signals


class NearZeroAutonomyTests(TestCase):
    def test_display_only_bound_leaves_machine_scope_unresolved(self):
        clauses, signals = _case()
        before = deepcopy((clauses, signals))
        finding, = near_zero_autonomy_findings(clauses, signals)
        self.assertEqual(finding["code"], "near_zero_autonomy_bound_lost")
        self.assertEqual(finding["severity"], "blocking")
        self.assertEqual(finding["clause_index"], 2)
        self.assertEqual(finding["signal_index"], 0)
        self.assertEqual(finding["evidence"], [clauses[0]["evidence"]])
        self.assertEqual((clauses, signals), before)

    def test_exact_bounded_authority_phrase(self):
        for bound in ("almost no", "nearly no", "virtually no", "practically no"):
            with self.subTest(bound=bound):
                quote = f"I dislike having {bound} authority over inspections."
                self.assertEqual(len(near_zero_autonomy_findings(*_case(quote, quote, "authority over inspections"))), 1)

    def test_qualified_referent_and_anchored_intensity_preserve_scope(self):
        self.assertEqual(near_zero_autonomy_findings(*_case(referent="almost no decision-making autonomy")), [])
        for value in ("near_zero", "almost no"):
            qualifier = {"kind": "intensity", "value": value, "evidence": _anchor(_FEEDBACK, "almost no", "qualifier")}
            self.assertEqual(near_zero_autonomy_findings(*_case(qualifiers=[qualifier])), [])

    def test_unrelated_anchor_or_generic_qualifier_does_not_preserve_bound(self):
        for value, quote in (("near_zero", "decision-making autonomy"), ("low", "almost no")):
            with self.subTest(value=value, quote=quote):
                qualifier = {"kind": "intensity", "value": value, "evidence": _anchor(_FEEDBACK, quote, "qualifier")}
                self.assertEqual(len(near_zero_autonomy_findings(*_case(qualifiers=[qualifier]))), 1)

    def test_scope_polarity_and_exact_local_target_are_required(self):
        for quote, referent in (
            ("I would have almost no support and would be responsible for strategy.", "strategy"),
            ("I have nearly no budget, and the authority is unclear.", "authority"),
            ("I would have no autonomy. Authority is important to me.", "authority"),
            ("I would have almost no autonomy, but I also worry about excess autonomy.", "autonomy"),
        ):
            with self.subTest(quote=quote):
                self.assertEqual(near_zero_autonomy_findings(*_case(quote, quote, referent)), [])
        for field, value in (("dimension", "role_responsibilities"), ("polarity", "positive")):
            clauses, signals = _case()
            signals[0][field] = value
            self.assertEqual(near_zero_autonomy_findings(clauses, signals), [])
