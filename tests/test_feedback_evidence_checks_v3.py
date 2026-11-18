"""Contrast anchored evidence findings with closely related valid records."""

from copy import deepcopy
from hashlib import sha256
from unittest import TestCase

from job_search_agent.feedback_evidence_checks_v3 import evidence_findings


def clause(index, feedback, quote, role):
    start = feedback.index(quote)
    return {
        "index": index, "role": role, "detail": None,
        "evidence": {
            "origin": "feedback", "role": role, "quote": quote,
            "start": start, "end": start + len(quote), "source_revision": sha256(feedback.encode()).hexdigest(),
        },
    }


def signal(index, dimension, scope_type, polarity, label, referent, *, qualifiers=()):
    return {
        "clause_index": index, "dimension": dimension, "polarity": polarity, "display_label": label,
        "scope": {"type": scope_type, "referent": referent, "qualifiers": list(qualifiers)},
    }


class ScopeEvidenceTests(TestCase):
    def test_generic_scope_loses_corroborated_emphasis(self):
        quote = "The posting says 'must love sales'; that's exactly what I want to avoid."
        clauses = [clause(4, quote, quote, "preference")]
        signals = [signal(4, "role_responsibilities", "role_feature", "negative", "Avoid sales-focused work", "sales")]
        before = deepcopy((clauses, signals))

        finding, = evidence_findings(clauses, signals)

        self.assertEqual(finding["code"], "duty_emphasis_lost")
        self.assertEqual(finding["severity"], "blocking")
        self.assertEqual(finding["clause_index"], 4)
        self.assertEqual(finding["signal_index"], 0)
        self.assertEqual(finding["evidence"], [clauses[0]["evidence"]])
        self.assertEqual((clauses, signals), before)

    def test_typed_emphasis_or_qualified_referent_preserves_scope(self):
        quote = ("The posting describes safety briefings as 'the heart of the role'. "
                 "I want to steer clear of jobs built around giving those briefings.")
        clauses = [clause(0, quote, quote, "preference")]
        common = (0, "role_responsibilities", "role_feature", "negative", "Jobs centered on giving safety briefings")
        broad = signal(*common, "giving safety briefings")
        self.assertEqual(evidence_findings(clauses, [broad])[0]["code"], "duty_emphasis_lost")

        scoped = signal(*common, "jobs built around giving safety briefings")
        typed = signal(*common, "giving safety briefings", qualifiers=[{"kind": "intensity", "value": "built around"}])
        unrelated = signal(*common, "giving safety briefings", qualifiers=[{"kind": "intensity", "value": "mild"}])
        self.assertEqual(evidence_findings(clauses, [scoped, typed]), [])
        self.assertEqual(evidence_findings(clauses, [unrelated])[0]["code"], "duty_emphasis_lost")

    def test_comparison_or_posting_copy_alone_does_not_ground_a_scope_finding(self):
        proposed = signal(0, "role_responsibilities", "role_feature", "negative", "Avoid sales-focused work", "sales")
        for quote in (
            "The posting says 'must love sales'.",
            "I like research more than sales-focused work.",
            "I want to avoid sales.",
        ):
            with self.subTest(quote=quote):
                self.assertEqual(evidence_findings([clause(0, quote, quote, "preference")], [proposed]), [])


class ContextEvidenceTests(TestCase):
    def test_distinct_posting_praise_is_diagnostic_with_anchored_employer_contrast(self):
        employer = "I do not trust the employer."
        examples = (
            ("This is a terrific AI advisor role,", " but ", "employer"),
            ("This particular Collection Analyst opening would be terrific.", " ", "culture_environment"),
        )
        for praise, separator, dimension in examples:
            with self.subTest(praise=praise):
                feedback = praise + separator + employer
                clauses = [clause(3, feedback, praise, "context"), clause(9, feedback, employer, "preference")]
                negative = signal(9, dimension, "employer", "negative", "Distrust of this employer", "current employer")
                finding, = evidence_findings(clauses, [negative])
                self.assertEqual(finding["code"], "posting_praise_in_context")
                self.assertEqual(finding["severity"], "diagnostic")
                self.assertEqual(finding["clause_index"], 3)
                self.assertIsNone(finding["signal_index"])
                self.assertEqual(finding["evidence"], [record["evidence"] for record in clauses])

    def test_context_note_does_not_duplicate_an_existing_posting_signal(self):
        praise = "This Safety Coordinator role looks terrific."
        employer = "I have no trust in the hiring organization."
        feedback = f"{praise} {employer}"
        clauses = [clause(0, feedback, praise, "context"), clause(1, feedback, praise, "preference"),
                   clause(2, feedback, employer, "preference")]
        signals = [signal(1, "role_responsibilities", "posting_role", "positive", "This Safety Coordinator role",
                          "this role"),
                   signal(2, "employer", "employer", "negative", "Employer distrust", "current employer")]
        self.assertEqual(evidence_findings(clauses, signals), [])

    def test_vague_conditional_comparative_or_attributed_praise_is_not_flagged(self):
        employer = "I have no trust in the hiring organization."
        negative = signal(1, "employer", "employer", "negative", "Employer distrust", "current employer")
        for context in (
            "This looks promising.",
            "This is a terrific role.",
            "This Portfolio Analyst position would be terrific if it were remote.",
            "This Portfolio Analyst position looks better than the previous posting.",
            "The recruiter says this is a terrific Portfolio Analyst position.",
        ):
            with self.subTest(context=context):
                feedback = f"{context} {employer}"
                clauses = [clause(0, feedback, context, "context"), clause(1, feedback, employer, "preference")]
                self.assertEqual(evidence_findings(clauses, [negative]), [])
