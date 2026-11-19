"""Distinguish a hiring preference for enthusiasm from evidence about duties."""

from copy import deepcopy
from hashlib import sha256
from unittest import TestCase

from job_search_agent.feedback_enthusiasm_scope_v3 import enthusiasm_scope_findings


def _case(quote, label, *, referent="calibration", qualifiers=()):
    feedback = f"I read the posting. {quote}"
    evidence = {"origin": "feedback", "role": "preference", "quote": quote, "start": feedback.index(quote),
                "end": len(feedback), "source_revision": sha256(feedback.encode()).hexdigest()}
    return ([{"index": 0, "evidence": evidence}], [{
        "clause_index": 0, "dimension": "role_responsibilities", "polarity": "negative", "display_label": label,
        "scope": {"type": "role_feature", "referent": referent, "qualifiers": list(qualifiers)},
    }], feedback)


class EnthusiasmScopeTests(TestCase):
    def test_workload_inference_is_flagged_without_removing_the_signal(self):
        quote = "The posting says ‘must love calibration’. That is something I want to avoid."
        for label, qualifiers in (
            ("Avoid calibration-heavy work", []),
            ("Avoid calibration", [{"kind": "intensity", "value": "strong"}]),
            ("Avoid calibration", [{"kind": "time_share", "value": "most of each day"}]),
        ):
            with self.subTest(label=label, qualifiers=qualifiers):
                clauses, signals, feedback = _case(quote, label, qualifiers=qualifiers)
                before = deepcopy((clauses, signals))
                finding, = enthusiasm_scope_findings(clauses, signals)
                self.assertEqual(finding["code"], "enthusiasm_does_not_establish_workload")
                self.assertEqual(finding["severity"], "blocking")
                self.assertEqual(finding["signal_index"], 0)
                anchor = finding["evidence"][0]
                self.assertEqual(feedback[anchor["start"]:anchor["end"]], "must love calibration")
                self.assertEqual(before, (clauses, signals))

    def test_direct_same_duty_centrality_or_narrow_objection_is_supported(self):
        start = "The posting says ‘must love calibration’."
        ending = " That is something I want to avoid."
        for quote, label, referent in (
            (start + " Calibration is the heart of the role." + ending, "Calibration-heavy work", "calibration"),
            (start + " I would spend most of each shift doing calibration." + ending,
             "Calibration-heavy work", "calibration"),
            (start + ending, "Aversion to the must love calibration requirement", "calibration enthusiasm requirement"),
            ("The posting says ‘must love inspections’." + ending, "Calibration-heavy work", "calibration"),
            (start + " I have requested details.", "Calibration-heavy work", "calibration"),
        ):
            with self.subTest(quote=quote, label=label):
                clauses, signals, _ = _case(quote, label, referent=referent)
                self.assertEqual(enthusiasm_scope_findings(clauses, signals), [])

    def test_centrality_of_a_different_duty_does_not_satisfy_review(self):
        quote = ("The posting says ‘must love calibration’. Inspections are the heart of the role. "
                 "I want to avoid that calibration requirement.")
        clauses, signals, _ = _case(quote, "Calibration-heavy work")
        self.assertEqual(len(enthusiasm_scope_findings(clauses, signals)), 1)
