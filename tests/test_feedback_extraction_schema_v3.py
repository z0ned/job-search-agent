"""Verify the experimental extraction constraints without the Responses API."""

from copy import deepcopy
from unittest import TestCase

from job_search_agent.feedback_extraction_schema_v3 import (
    INTENSITY_VALUES,
    TRIAL_SCHEMA,
    _build_trial_schema,
    schema_issues,
)
from job_search_agent.feedback_extraction_v3 import DIMENSION_SCOPES, QUALIFIER_KINDS, _PROPOSAL_SCHEMA


def signal(dimension, scope_type, *qualifiers):
    return {
        "clause_index": 0, "dimension": dimension, "display_label": "Test target",
        "polarity": "negative", "strength": "mild", "condition": None,
        "scope": {"type": scope_type, "referent": "Test target", "qualifiers": list(qualifiers)},
    }


def qualifier(kind, value, source="feedback"):
    return {"kind": kind, "value": value, "source": source, "quote": "very limited"}


class FeedbackExtractionSchemaV3Tests(TestCase):
    def test_signal_variants_cover_exact_dimension_scope_pairs(self):
        self.assertEqual(TRIAL_SCHEMA["type"], "object")
        self.assertNotIn("anyOf", TRIAL_SCHEMA)
        signals = TRIAL_SCHEMA["properties"]["signals"]["items"]["anyOf"]
        observed = {}
        for branch in signals:
            properties = branch["properties"]
            self.assertEqual(next(iter(properties)), "dimension")
            dimension, = properties["dimension"]["enum"]
            self.assertNotIn(dimension, observed)
            observed[dimension] = tuple(properties["scope"]["properties"]["type"]["enum"])
        self.assertEqual(observed, DIMENSION_SCOPES)
        self.assertNotIn("posting_role", observed["seniority_scope"])
        self.assertIn("posting_role", observed["role_responsibilities"])

    def test_only_intensity_has_controlled_values_and_original_feedback_source(self):
        branches = TRIAL_SCHEMA["properties"]["signals"]["items"]["anyOf"]
        for branch in branches:
            scope = branch["properties"]["scope"]["properties"]
            intensity, ordinary = scope["qualifiers"]["items"]["anyOf"]
            intensity_fields, ordinary_fields = intensity["properties"], ordinary["properties"]
            self.assertEqual(intensity_fields["kind"]["enum"], ["intensity"])
            self.assertEqual(intensity_fields["value"]["enum"], list(INTENSITY_VALUES))
            self.assertEqual(intensity_fields["source"]["enum"], ["feedback"])
            self.assertEqual(ordinary_fields["kind"]["enum"], [kind for kind in QUALIFIER_KINDS if kind != "intensity"])
            self.assertEqual(ordinary_fields["value"], {"type": "string"})
            self.assertEqual(ordinary_fields["source"]["enum"], ["feedback", "job_context"])
            for variant in (intensity, ordinary):
                self.assertEqual(variant["properties"]["quote"], {"type": "string"})
                self.assertIn("quote", variant["required"])

    def test_trial_checker_rejects_incompatible_pairs_and_non_level_intensity(self):
        proposal = {"clauses": [], "signals": [
            signal("seniority_scope", "posting_role"),
            signal("seniority_scope", "seniority_feature", qualifier("intensity", "very limited")),
            signal("role_responsibilities", "role_feature", qualifier("intensity", "near_zero", "job_context")),
            signal("role_responsibilities", "project_type", qualifier("duration", "very limited")),
            signal("seniority_scope", "seniority_feature", qualifier("intensity", "near_zero")),
        ]}
        before = deepcopy(proposal)
        self.assertEqual(schema_issues(proposal), [
            {"field": "signals", "index": 0, "message": "Incompatible dimension and scope type."},
            {"field": "signals", "index": 1, "message": "Intensity must use a controlled level."},
            {"field": "signals", "index": 2, "message": "Intensity must cite original feedback."},
        ])
        self.assertEqual(proposal, before)

    def test_experimental_schema_does_not_mutate_or_share_production_schema(self):
        production = deepcopy(_PROPOSAL_SCHEMA)
        trial = _build_trial_schema()
        trial["properties"]["clauses"]["items"]["properties"]["quote"]["type"] = "number"
        self.assertEqual(_PROPOSAL_SCHEMA, production)
        signal_fields = _PROPOSAL_SCHEMA["properties"]["signals"]["items"]["properties"]
        qualifier_fields = signal_fields["scope"]["properties"]["qualifiers"]["items"]["properties"]
        self.assertEqual(signal_fields["dimension"]["enum"], list(DIMENSION_SCOPES))
        self.assertEqual(qualifier_fields["kind"]["enum"], list(QUALIFIER_KINDS))
        self.assertEqual(qualifier_fields["value"], {"type": "string"})

    def test_all_object_schemas_require_every_field_and_disallow_extra_fields(self):
        pending = [TRIAL_SCHEMA]
        while pending:
            schema = pending.pop()
            if schema.get("type") == "object":
                self.assertIs(schema["additionalProperties"], False)
                self.assertCountEqual(schema["required"], schema["properties"])
                pending.extend(schema["properties"].values())
            pending.extend(schema.get("anyOf", []))
            if "items" in schema:
                pending.append(schema["items"])
