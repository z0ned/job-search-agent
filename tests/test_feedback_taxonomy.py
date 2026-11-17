import json
from pathlib import Path
import unittest

from job_search_agent.feedback_taxonomy import canonicalize_signal


def signal(dimension, feature, scope_type, scope_value, polarity="negative"):
    return {
        "dimension": dimension,
        "feature": feature,
        "polarity": polarity,
        "scope": {"type": scope_type, "value": scope_value},
    }


class FeedbackTaxonomyTests(unittest.TestCase):
    def test_quota_carrying_sales_alias_preserves_display_labels(self):
        reference = canonicalize_signal(signal(
            "career_category", "quota-carrying sales careers", "career_category", "quota_sales",
        ))
        prediction = canonicalize_signal(signal(
            "career_category", "Quota-Bearing Sales", "career_category", "quota_carrying_sales",
        ))
        self.assertEqual(prediction.to_dict(), {
            "dimension": "career_category",
            "feature_id": reference.feature_id,
            "feature_label": "Quota-Bearing Sales",
            "polarity": "negative",
            "scope_type": "career_category",
            "scope_id": reference.scope_id,
            "scope_label": "quota_carrying_sales",
        })
        self.assertEqual((reference.feature_id, reference.scope_id), ("quota_carrying_sales", "quota_sales"))

    def test_similar_sales_concepts_are_distinct(self):
        generic_sales = canonicalize_signal(signal(
            "career_category", "sales careers", "career_category", "sales",
        ))
        duties = canonicalize_signal(signal(
            "role_responsibilities", "carrying a sales quota", "role_feature", "sales_quota",
        ))
        self.assertEqual(generic_sales.feature_id, "literal:sales careers")
        self.assertEqual(generic_sales.scope_id, "literal:sales")
        self.assertEqual(duties.feature_id, "sales_quota_responsibilities")
        self.assertEqual(duties.scope_id, "sales_quota")

    def test_correct_feature_does_not_repair_wrong_scope_type(self):
        canonical = canonicalize_signal(signal(
            "work_arrangement", "100% remote", "location_arrangement", "fully_remote_work",
        ))
        self.assertEqual(canonical.feature_id, "fully_remote")
        self.assertEqual(canonical.scope_type, "location_arrangement")
        self.assertEqual(canonical.scope_id, "literal:fully_remote_work")

    def test_remote_and_travel_scope_aliases_preserve_material_specifics(self):
        remote = canonicalize_signal(signal(
            "work_arrangement", "Fully Remote", "arrangement", "fully_remote_work", "positive",
        ))
        travel = canonicalize_signal(signal(
            "work_arrangement", "weekly flights", "travel_frequency", "weekly_air_travel",
        ))
        unspecified_air_travel = canonicalize_signal(signal(
            "work_arrangement", "weekly travel", "travel_frequency", "weekly_travel",
        ))
        self.assertEqual((remote.feature_id, remote.scope_id, remote.polarity),
                         ("fully_remote", "fully_remote", "positive"))
        self.assertEqual((travel.feature_id, travel.scope_id), ("weekly_air_travel", "weekly_flights"))
        self.assertEqual(unspecified_air_travel.scope_id, "literal:weekly_travel")

    def test_compensation_values_preserve_amount_sign_and_employment_type(self):
        equivalent = canonicalize_signal(signal(
            "compensation", "$110/hour C2C", "compensation_context", "c2c_110_per_hour",
        ))
        self.assertEqual((equivalent.feature_id, equivalent.scope_id), ("c2c_110_hour", "c2c_110_hour"))
        for amount in ("c2c_111_hour", "c2c_-110_hour", "c2c_110_day", "w2_110_hour"):
            with self.subTest(amount=amount):
                distinct = canonicalize_signal(signal(
                    "compensation", "$110/hour C2C", "compensation_context", amount,
                ))
                self.assertEqual(distinct.scope_id, f"literal:{amount}")

    def test_named_employer_does_not_merge_with_current_employer(self):
        named = canonicalize_signal(signal(
            "employer", "Northstar Tech employer", "employer", "Northstar Tech",
        ))
        unnamed = canonicalize_signal(signal(
            "employer", "this employer", "employer", "this_employer",
        ))
        self.assertEqual((named.feature_id, named.scope_id), ("northstar_tech", "northstar_tech"))
        self.assertEqual((unnamed.feature_id, unnamed.scope_id), ("current_job_employer", "current_job_employer"))

    def test_unknown_labels_retain_case_and_separators(self):
        first = canonicalize_signal(signal("role_responsibilities", "New Topic", "role_feature", "new_topic"))
        second = canonicalize_signal(signal("role_responsibilities", "new_topic", "role_feature", "new-topic"))
        self.assertEqual((first.feature_id, first.scope_id), ("literal:New Topic", "literal:new_topic"))
        self.assertEqual((second.feature_id, second.scope_id), ("literal:new_topic", "literal:new-topic"))

    def test_mission_alias_does_not_generalize_small_nonprofits(self):
        general = canonicalize_signal(signal(
            "growth_purpose", "helping nonprofits apply AI", "mission", "helping_nonprofits_apply_ai",
        ))
        specific = canonicalize_signal(signal(
            "growth_purpose", "helping small nonprofits apply AI", "mission", "small_nonprofit_ai_enablement",
        ))
        self.assertEqual((general.feature_id, general.scope_id),
                         ("nonprofit_ai_enablement", "nonprofit_ai_enablement"))
        self.assertEqual(specific.feature_id, "literal:helping small nonprofits apply AI")
        self.assertEqual(specific.scope_id, "literal:small_nonprofit_ai_enablement")

    def test_taxonomy_covers_all_reference_signals(self):
        fixture = Path(__file__).resolve().parents[1] / "feedback_interpretation_gold_cases_v1.json"
        suite = json.loads(fixture.read_text(encoding="utf-8"))
        for case in suite["test_cases"]:
            for expected in case["expected_interpretations"]:
                with self.subTest(case=case["case_id"], feature=expected["feature"]):
                    canonical = canonicalize_signal(expected)
                    self.assertFalse(canonical.feature_id.startswith("literal:"))
                    self.assertFalse(canonical.scope_id.startswith("literal:"))


if __name__ == "__main__":
    unittest.main()
