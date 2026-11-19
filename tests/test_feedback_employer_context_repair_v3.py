"""Exercise the explicit career-exception repair against archived proposals."""

from copy import deepcopy
import json
from pathlib import Path
from unittest import TestCase

from job_search_agent.feedback_employer_context_repair_v3 import prepare_employer_career_context
from job_search_agent.feedback_replay_v3 import _ArchivedProposalProvider
from job_search_agent.feedback_v3 import interpret_feedback_v3


_BENCHMARK = Path(__file__).resolve().parents[1] / "benchmarks" / "feedback"


def _fixture(path, case_id):
    cases = json.loads((_BENCHMARK / path).read_bytes())["test_cases"]
    return next(case for case in cases if case["case_id"] == case_id)


def _proposal(path, case_id):
    return json.loads((_BENCHMARK / path).read_bytes())[case_id]


class EmployerContextRepairTests(TestCase):
    def test_both_archived_explicit_career_exceptions_keep_two_held_signals(self):
        case = _fixture("gold_cases_v3.json", "FI-042")
        for number in (1, 2):
            with self.subTest(pass_number=number):
                raw = _proposal(f"live_v3_gold/pass-{number}.proposals.json", "FI-042")
                unchanged = deepcopy(raw)
                feedback = case["original_feedback"]

                def validate(proposal):
                    return interpret_feedback_v3(
                        case["decision"], feedback, case["job_context"],
                        provider=_ArchivedProposalProvider("archived", proposal),
                    )

                before = validate(raw)
                self.assertEqual(len(before["interpretations"]), 1)
                self.assertEqual(len(before["validation_issues"]), 1)
                repaired = prepare_employer_career_context(raw, feedback)
                self.assertIsNot(repaired, raw)
                self.assertEqual(raw, unchanged)
                self.assertEqual(repaired["signals"], raw["signals"])
                self.assertEqual(repaired["clauses"][0], raw["clauses"][0])
                self.assertEqual(repaired["clauses"][1]["quote"],
                                 "AI product leadership career, just not at Omega Health.")
                self.assertIs(prepare_employer_career_context(repaired, feedback), repaired)

                after = validate(repaired)
                positive, negative = after["interpretations"]
                self.assertEqual(positive, before["interpretations"][0])
                self.assertEqual(negative["dimension"], "employer")
                self.assertEqual(negative["polarity"], "negative")
                self.assertEqual(negative["scope"]["referent"], "Omega Health")
                self.assertEqual(negative["application_status"], "held_for_review")
                self.assertEqual(after["validation_issues"], [])
                for field in ("review_status", "hard_constraint_action", "hard_constraints_mutated"):
                    self.assertEqual(after[field], before[field])
                for anchor in negative["evidence"]:
                    self.assertEqual(feedback[anchor["start"]:anchor["end"]], anchor["quote"])

    def test_unrelated_posting_praise_does_not_supply_career_context(self):
        case = _fixture("extraction_trial_v3_novel.json", "FT-004")
        raw = _proposal("live_v3_extraction_independence_trial/treatment.proposals.json", "FT-004")
        self.assertIs(prepare_employer_career_context(raw, case["original_feedback"]), raw)

    def test_no_repair_across_sentences_quotes_or_partial_exceptions(self):
        raw = _proposal("live_v3_gold/pass-1.proposals.json", "FI-042")
        for feedback in (
            "I would love an AI product leadership career. just not at Omega Health.",
            "A coworker said, ‘I would love an AI product leadership career, just not at Omega Health.’",
            "I would love an AI product leadership career, except when traveling, just not at Omega Health.",
            "I would love an AI product leadership career, just not at Omega Health because it is in another city.",
            "I would love an AI product leadership career, just not at Omega Health. "
            "I would love an AI product leadership career, just not at Omega Health.",
        ):
            with self.subTest(feedback=feedback):
                self.assertIs(prepare_employer_career_context(raw, feedback), raw)

    def test_requires_a_unique_grounded_career_signal_and_qualifier(self):
        feedback = _fixture("gold_cases_v3.json", "FI-042")["original_feedback"]
        original = _proposal("live_v3_gold/pass-1.proposals.json", "FI-042")
        for variant in ("bad-career", "bad-qualifier", "duplicate-signal", "duplicate-clause", "wrong-employer",
                        "unanchored-condition", "unrelated-qualifier"):
            with self.subTest(variant=variant):
                draft = deepcopy(original)
                career, employer = draft["signals"]
                qualifier = employer["scope"]["qualifiers"][0]
                if variant == "bad-career":
                    career["polarity"] = "negative"
                if variant == "bad-qualifier":
                    qualifier["value"] = "all leadership careers"
                if variant == "duplicate-signal":
                    draft["signals"].append(deepcopy(career))
                if variant == "duplicate-clause":
                    draft["clauses"].append(deepcopy(draft["clauses"][1]))
                if variant == "wrong-employer":
                    employer["scope"]["referent"] = "Other Health"
                if variant == "unanchored-condition":
                    employer["condition"] = {"kind": "other", "value": "career", "quote": "career"}
                if variant == "unrelated-qualifier":
                    employer["scope"]["qualifiers"].append({**qualifier, "kind": "technology"})
                self.assertIs(prepare_employer_career_context(draft, feedback), draft)
