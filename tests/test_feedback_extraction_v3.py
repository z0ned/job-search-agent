"""Verify the v3 prompt and strict Responses API request with a mocked transport."""

import io
import json
import unittest
from unittest.mock import patch

from job_search_agent.feedback import DIMENSION_SCOPES as V2_DIMENSION_SCOPES
from job_search_agent.feedback import OpenAIFeedbackProvider
from job_search_agent.feedback_extraction_v3 import (
    CLAUSE_ROLES,
    CONDITION_KINDS,
    DIMENSION_SCOPES,
    QUALIFIER_KINDS,
    OpenAIFeedbackProviderV3,
    _INSTRUCTIONS,
    _PROPOSAL_SCHEMA,
)


def completed_response(proposal):
    body = {
        "status": "completed",
        "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(proposal)}]}],
    }
    return io.BytesIO(json.dumps(body).encode())


class FeedbackExtractionV3Tests(unittest.TestCase):
    def test_provider_uses_strict_v3_schema_and_returns_raw_proposal(self):
        provider = OpenAIFeedbackProviderV3(model="test-model", api_key="test-key", temperature=0.1)
        feedback = "I enjoy planning inventory audits."
        context = {"description": "Replace the user's statement."}
        hard_rules = {"permanent_base_minimum_usd": 180000}
        raw = {
            "clauses": [{"role": "preference", "quote": feedback, "detail": None}],
            "signals": [{
                "clause_index": 0,
                "dimension": "role_responsibilities",
                "display_label": "Planning inventory audits",
                "polarity": "positive",
                "strength": "mild",
                "scope": {"type": "role_feature", "referent": "inventory audit planning", "qualifiers": []},
                "condition": None,
            }],
        }
        with patch("job_search_agent.feedback.urlopen", return_value=completed_response(raw)) as urlopen:
            self.assertEqual(provider.propose("interested", feedback, context, hard_rules), raw)

        urlopen.assert_called_once()
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(urlopen.call_args.kwargs, {"timeout": 60})
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(payload["temperature"], 0.1)
        self.assertIs(payload["store"], False)
        self.assertEqual(payload["instructions"], _INSTRUCTIONS)
        self.assertNotIn(context["description"], payload["instructions"])
        self.assertEqual(json.loads(payload["input"]), {
            "decision": "interested", "original_feedback": feedback, "job_context": context,
            "hard_rules": hard_rules,
        })
        self.assertEqual(payload["text"]["format"], {
            "type": "json_schema", "strict": True, "name": "feedback_extraction_v3", "schema": _PROPOSAL_SCHEMA,
        })

    def test_schema_requires_exact_fields_on_all_objects(self):
        root = _PROPOSAL_SCHEMA["properties"]
        self.assertEqual(set(root), {"clauses", "signals"})
        clause = root["clauses"]["items"]
        signal = root["signals"]["items"]
        scope = signal["properties"]["scope"]
        qualifier = scope["properties"]["qualifiers"]["items"]
        condition, nullable = signal["properties"]["condition"]["anyOf"]
        self.assertEqual(nullable, {"type": "null"})
        for schema, fields in (
            (_PROPOSAL_SCHEMA, {"clauses", "signals"}),
            (clause, {"role", "quote", "detail"}),
            (signal, {"clause_index", "dimension", "display_label", "polarity", "strength", "scope", "condition"}),
            (scope, {"type", "referent", "qualifiers"}),
            (qualifier, {"kind", "value", "source", "quote"}),
            (condition, {"kind", "value", "quote"}),
        ):
            self.assertIs(schema["additionalProperties"], False)
            self.assertEqual(set(schema["required"]), fields)
            self.assertEqual(set(schema["properties"]), fields)
        self.assertEqual(clause["properties"]["role"]["enum"], list(CLAUSE_ROLES))
        self.assertEqual(qualifier["properties"]["kind"]["enum"], list(QUALIFIER_KINDS))
        self.assertEqual(condition["properties"]["kind"]["enum"], list(CONDITION_KINDS))

    def test_v3_scope_types_distinguish_projects_roles_and_profile_facts(self):
        expected_scopes = dict(V2_DIMENSION_SCOPES)
        del expected_scopes["qualifications_fit"]
        expected_scopes["role_responsibilities"] = ("role_feature", "project_type", "posting_role")
        self.assertEqual(DIMENSION_SCOPES, expected_scopes)
        self.assertEqual(V2_DIMENSION_SCOPES["role_responsibilities"], ("role_feature",))
        self.assertIn("qualifications_fit", V2_DIMENSION_SCOPES)

    def test_v2_provider_keeps_its_format_and_optional_temperature(self):
        provider = OpenAIFeedbackProvider(model="test-model", api_key="test-key")
        raw = {"review_status": "NEEDS_CLARIFICATION"}
        with patch("job_search_agent.feedback.urlopen", return_value=completed_response(raw)) as urlopen:
            self.assertEqual(provider.propose("rejected", "Unclear.", {}, {}), raw)

        payload = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual(payload["text"]["format"]["name"], "feedback_interpretation")
        self.assertIn("interpretations", payload["text"]["format"]["schema"]["properties"])
        self.assertNotIn("temperature", payload)


if __name__ == "__main__":
    unittest.main()
