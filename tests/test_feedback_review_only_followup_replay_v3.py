"""Protect anchored review and scope semantics with live captures and contrasts."""

from unittest import TestCase

from job_search_agent.feedback_review_only_followup_replay_v3 import DEFAULT_ARCHIVE, replay
from job_search_agent.feedback_review_only_followup_trial_v3 import _followup_prediction


_MODEL = {"model": "gpt-5.4-2026-03-05", "recover_explicit_conditions": True}


def _proposal(clauses, signals):
    return {"clauses": [{"role": role, "quote": quote, "detail": detail} for role, quote, detail in clauses],
            "signals": signals}


def _validate(feedback, proposal):
    case = {"decision": "interested", "original_feedback": feedback, "job_context": {}}
    return _followup_prediction(case, {}, proposal, _MODEL)


class ReviewOnlyFollowupReplayTests(TestCase):
    def test_all_archived_replies_reproduce_and_only_the_two_known_fields_change(self):
        report = replay(DEFAULT_ARCHIVE)
        self.assertEqual((report["inference_requests"], report["replayed_proposals"], report["unchanged_proposals"]), (0, 48, 40))
        self.assertEqual(report["changed_proposals"], 8)
        for row in report["changes"]:
            with self.subTest(case=row["case_id"], arm=row["origin_arm"], pass_number=row["pass_number"]):
                fields = row["changed_fields"]
                if row["case_id"] == "RO3-004":
                    self.assertEqual(set(fields), {"clarification_question"})
                    self.assertIn("overnight shift is once in a while or the usual schedule", fields["clarification_question"]["after"])
                else:
                    self.assertEqual(row["case_id"], "RO3-011")
                    self.assertEqual(set(fields), {"interpretations"})
                    before, after = fields["interpretations"]["before"], fields["interpretations"]["after"]
                    self.assertEqual(after[1:], before[1:])
                    qualifier = after[0]["scope"]["qualifiers"][-1]
                    self.assertEqual((qualifier["kind"], qualifier["value"], qualifier["quote"]),
                                     ("quantity", "1", "One overnight trip a quarter"))
                    self.assertEqual(after[0]["scope"]["qualifiers"][:-1], before[0]["scope"]["qualifiers"])

    def test_clarification_uses_the_posting_question_and_preserves_a_separate_preference(self):
        question = "Could you check whether badge pickup takes place online or in person?"
        verification = ("posting_verification", question, "Confirm how badge pickup works.")
        result, _ = _validate(question, _proposal([verification], []))
        self.assertEqual(result["clarification_question"], "Could you verify whether badge pickup takes place online or in person?")
        sentiment = "I like mapping the intake workflow."
        signal = {"clause_index": 0, "dimension": "role_responsibilities", "display_label": "Intake workflow mapping",
                  "polarity": "positive", "strength": "mild", "condition": None,
                  "scope": {"type": "role_feature", "referent": "mapping intake workflow", "qualifiers": []}}
        result, diagnostics = _validate(f"{sentiment} {question}", _proposal([("preference", sentiment, None), verification], [signal]))
        self.assertEqual(result["review_status"], "PENDING_APPROVAL")
        self.assertIsNone(result["clarification_question"])
        self.assertIsNone(diagnostics["posting_verification_repair"])
        self.assertEqual(len(result["interpretations"]), 1)
        self.assertEqual(result["hard_constraint_action"], "UNCHANGED")

    def test_trip_quantity_distinguishes_exact_ambiguous_and_unstated_counts(self):
        signal = {"clause_index": 0, "dimension": "work_arrangement", "display_label": "Work trips", "polarity": "positive",
                  "strength": "mild", "condition": None, "scope": {"type": "travel_frequency", "referent": "work trips",
                  "qualifiers": [{"kind": "frequency", "source": "feedback", "quote": "per month", "value": "per month"}]}}
        for text, quantity, flagged in (
            ("Two work trips per month are manageable.", "2", False),
            ("Two or three work trips per month might be manageable.", None, True),
            ("I can manage work trips per month around the existing schedule.", None, False),
        ):
            with self.subTest(text=text):
                result, _ = _validate(text, _proposal([("preference", text, None)], [signal]))
                validated, = result["interpretations"]
                amounts = [q for q in validated["scope"]["qualifiers"] if q["kind"] == "quantity"]
                self.assertEqual([q["value"] for q in amounts], [quantity] if quantity else [])
                self.assertEqual(bool(result["evidence_findings"]), flagged)
                self.assertEqual(validated["application_status"], "held_for_review")
                self.assertFalse(result["hard_constraints_mutated"])
