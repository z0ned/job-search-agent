"""Exercise the held travel-count repair on saved and fresh contrasts."""

import json
from copy import deepcopy
from pathlib import Path
from unittest import TestCase

from job_search_agent.feedback_replay_v3 import _ArchivedProposalProvider
from job_search_agent.feedback_travel_count_repair_v3 import repair_travel_count
from job_search_agent.feedback_v3 import interpret_feedback_v3


_BENCHMARK = Path(__file__).resolve().parents[1] / "benchmarks" / "feedback"


def _qualifier(kind, value, quote):
    return {"kind": kind, "value": value, "quote": quote, "source": "feedback"}


def _travel(text, frequency, quote, *, other=(), condition=None):
    proposal = {
        "clauses": [{"role": "preference", "quote": text, "detail": None}],
        "signals": [{"clause_index": 0, "dimension": "work_arrangement", "display_label": "Travel preference",
                     "polarity": "positive", "strength": "mild", "condition": condition,
                     "scope": {"type": "travel_frequency", "referent": "business travel", "qualifiers": [
                         _qualifier("frequency", frequency, quote), *other,
                     ]}}],
    }
    result = interpret_feedback_v3("interested", text, provider=_ArchivedProposalProvider("fixture", proposal))
    assert not result["validation_issues"]
    return result


class TravelCountRepairTests(TestCase):
    def test_archived_quarterly_trip_keeps_count_cadence_and_weekly_objection(self):
        source = _BENCHMARK / "live_v3_review_only_trial" / "pass-1" / "baseline.json"
        before = json.loads(source.read_bytes())["RO3-011"]
        copy = deepcopy(before)
        after, records = repair_travel_count(before)
        self.assertEqual(before, copy)
        self.assertEqual(after["interpretations"][1], before["interpretations"][1])
        for key in before.keys() - {"interpretations"}:
            self.assertEqual(after[key], before[key])

        trip = after["interpretations"][0]
        qualifiers = trip["scope"]["qualifiers"]
        self.assertEqual(qualifiers[0], before["interpretations"][0]["scope"]["qualifiers"][0])
        count = qualifiers[-1]
        self.assertEqual((count["kind"], count["value"], count["quote"]),
                         ("quantity", "1", "One overnight trip a quarter"))
        anchor = count["evidence"]
        self.assertEqual(before["original_feedback"][anchor["start"]:anchor["end"]], count["quote"])
        self.assertEqual(trip["evidence"][-1], anchor)
        self.assertEqual(records, [{"signal_index": 0, "clause_index": 0, "added_quantity": count}])
        self.assertIs(repair_travel_count(after)[0], after)

    def test_different_spelled_and_numeric_counts_keep_verified_cadence(self):
        for source, frequency, evidence, quantity in (
            ("Two short client trips each month would work.", "monthly", "each month", "2"),
            ("3 business trips every two months would work.", "every two months", "every two months", "3"),
            ("I can do four international trips per year.", "yearly", "per year", "4"),
        ):
            with self.subTest(source=source):
                before = _travel(source, frequency, evidence)
                after, repairs = repair_travel_count(before)
                qualifiers = after["interpretations"][0]["scope"]["qualifiers"]
                self.assertEqual([item["value"] for item in qualifiers], [frequency, quantity])
                self.assertEqual(len(repairs), 1)
                self.assertEqual(after["review_status"], before["review_status"])

    def test_range_qualified_and_conflicting_counts_stay_visible_for_review(self):
        for source in (
            "One or two overnight trips a quarter works.",
            "2–3 business trips a quarter works.",
            "A few overnight trips a quarter might work.",
            "Up to two trips a quarter works.",
            "At-most two trips a quarter works.",
            "A maximum of two business trips a quarter works.",
            "One trip a quarter would work for me, but two trips would not.",
        ):
            with self.subTest(source=source):
                before = _travel(source, "quarterly", "a quarter")
                after, records = repair_travel_count(before)
                self.assertEqual(records, [])
                self.assertEqual(after["interpretations"], before["interpretations"])
                self.assertEqual([row["code"] for row in after["evidence_findings"]], ["travel_trip_count_needs_review"])
                self.assertIs(repair_travel_count(after)[0], after)

    def test_cadence_only_and_already_preserved_counts_remain_unchanged(self):
        uncounted = _travel("Monthly overnight travel works for me.", "monthly", "Monthly")
        count = _travel("Two business trips per month would work.", "monthly", "per month",
                        other=[_qualifier("quantity", "2", "Two business trips")])
        combined = _travel("Two business trips per month would work.", "two trips per month", "Two business trips per month")
        ranged = _travel("Two or three business trips per month would work.", "two or three business trips per month",
                         "Two or three business trips per month")
        bounded = _travel("Up to three work trips per quarter would work.", "up to three work trips per quarter",
                          "Up to three work trips per quarter")
        for before in (uncounted, count, combined, ranged, bounded):
            with self.subTest(source=before["original_feedback"]):
                after, repairs = repair_travel_count(before)
                self.assertIs(after, before)
                self.assertEqual(repairs, [])

    def test_unrelated_or_unverified_cadence_never_gains_a_count(self):
        mixed = _travel("Two trips a quarter worked before. I can travel each month now.", "monthly", "each month")
        mismatch = _travel("Two trips a quarter works.", "monthly", "a quarter")
        count_only = _travel("Two trips a quarter works.", "quarterly", "Two trips")
        missing_quantity_anchor = _travel("Two trips a quarter works.", "quarterly", "a quarter",
                                          other=[_qualifier("quantity", "2", "a quarter")])
        for before in (mixed, mismatch, count_only, missing_quantity_anchor):
            with self.subTest(source=before["original_feedback"]):
                after, records = repair_travel_count(before)
                self.assertEqual(records, [])
                self.assertEqual(after["interpretations"], before["interpretations"])
                self.assertEqual(len(after["evidence_findings"]), 1)

    def test_conditions_keep_their_existing_scope(self):
        before = _travel(
            "Two trips every month work if the client pays for lodging.", "monthly", "every month", condition={
                "kind": "other", "value": "client pays for lodging", "quote": "if the client pays for lodging",
            },
        )
        after, repairs = repair_travel_count(before)
        self.assertEqual(len(repairs), 1)
        self.assertEqual(after["interpretations"][0]["condition"], before["interpretations"][0]["condition"])
        self.assertEqual(after["hard_constraint_action"], before["hard_constraint_action"])
