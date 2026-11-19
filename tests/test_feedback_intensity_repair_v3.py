"""Exercise the optional preprocessing of redundant intensity for archive replay."""

from copy import deepcopy
from unittest import TestCase
from unittest.mock import Mock

from job_search_agent.feedback_intensity_repair_v3 import prepare_duplicate_intensity
from job_search_agent.feedback_v3 import interpret_feedback_v3


def qualifier(value, quote, kind="intensity"):
    return {"kind": kind, "value": value, "source": "feedback", "quote": quote}


def proposal(text, qualifiers):
    return {
        "clauses": [{"role": "preference", "quote": text, "detail": None}],
        "signals": [{
            "clause_index": 0, "dimension": "role_responsibilities", "display_label": "Incident analysis intensity",
            "polarity": "negative", "strength": "strong", "condition": None,
            "scope": {"type": "role_feature", "referent": "incident analysis", "qualifiers": qualifiers},
        }],
    }


class IntensityRepairV3Tests(TestCase):
    def setUp(self):
        self.text = "I would avoid incident analysis as the main duty or the central responsibility."
        self.primary = qualifier(" DOMINANT ", "main duty")
        self.additional = qualifier("dominant", "central responsibility")

    def validate(self, raw):
        provider = Mock(model="fixture-model")
        provider.propose.return_value = raw
        return interpret_feedback_v3("rejected", self.text, provider=provider)

    def test_coalesces_only_the_controlled_level_and_keeps_verbatim_anchors(self):
        raw = proposal(self.text, [self.primary, self.additional, self.additional])
        before = deepcopy(raw)
        self.assertEqual(self.validate(raw)["review_status"], "NEEDS_CLARIFICATION")

        prepared, supplemental = prepare_duplicate_intensity(raw, self.text, {})
        result = self.validate(prepared)

        self.assertEqual(raw, before)
        self.assertEqual(result["review_status"], "PENDING_APPROVAL")
        self.assertEqual(result["validation_issues"], [])
        signal, = result["interpretations"]
        intensity, = signal["scope"]["qualifiers"]
        self.assertEqual(intensity["value"], "dominant")
        self.assertEqual(intensity["evidence"]["quote"], "main duty")
        alternate, = supplemental[0]
        self.assertEqual(alternate["quote"], "central responsibility")
        self.assertEqual(self.text[alternate["start"]:alternate["end"]], alternate["quote"])
        self.assertEqual(alternate["source_revision"], intensity["evidence"]["source_revision"])

    def test_leaves_conflicting_uncontrolled_or_unanchored_qualifiers_for_validation(self):
        for qualifiers in (
            [self.primary, qualifier("high", "central responsibility")],
            [qualifier("central", "main duty"), qualifier("central", "central responsibility")],
            [self.primary, qualifier("dominant", "fabricated quote")],
            [self.primary, dict(self.additional, unrelated_field=True)],
            [self.primary, self.additional, qualifier("main", "main duty", kind="frequency"),
             qualifier("main", "central responsibility", kind="frequency")],
        ):
            with self.subTest(qualifiers=qualifiers):
                raw = proposal(self.text, qualifiers)
                prepared, supplemental = prepare_duplicate_intensity(raw, self.text, {})
                self.assertIs(prepared, raw)
                self.assertEqual(supplemental, {})
                self.assertEqual(self.validate(raw)["interpretations"], [])

    def test_leaves_cross_claim_anchors_and_shared_clause_indices_unaltered(self):
        preference = "I would avoid incident analysis as the main duty."
        feedback = f"{preference} Training is a central responsibility."
        cross_claim = proposal(preference, [self.primary, self.additional])
        shared_clause = proposal(self.text, [self.primary, self.additional])
        shared_clause["signals"].append(deepcopy(shared_clause["signals"][0]))
        for raw, text in ((cross_claim, feedback), (shared_clause, self.text)):
            with self.subTest(raw=raw):
                prepared, supplemental = prepare_duplicate_intensity(raw, text, {})
                self.assertIs(prepared, raw)
                self.assertEqual(supplemental, {})

    def test_keeps_distinct_qualifiers_and_does_not_invent_a_condition(self):
        prefix = "I would avoid regular incident analysis"
        feedback = f"{prefix}, provided it takes no more than two hours per day."
        cap = "no more than two hours per day"
        intensity = qualifier("strong", "avoid")
        duration = qualifier(cap, cap, kind="duration")
        moved = proposal(feedback, [intensity, duration, qualifier("strong", "hours per day")])
        prepared, supplemental = prepare_duplicate_intensity(moved, feedback, {})
        self.assertIs(prepared, moved)
        self.assertEqual(supplemental, {})

        unchanged = proposal(feedback, [intensity, duration, qualifier("strong", "regular")])
        prepared, supplemental = prepare_duplicate_intensity(unchanged, feedback, {})
        self.assertEqual(prepared["signals"][0]["scope"]["qualifiers"], [intensity, duration])
        self.assertEqual([item["quote"] for item in supplemental[0]], ["regular"])
