"""Check verifiable reaction accounting against saved and malformed outputs."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import unittest

from job_search_agent.feedback_reaction_accounting_v3 import audit_reactions, identify_reactions
from job_search_agent.feedback_v3 import _span


_ARCHIVE = Path("benchmarks/feedback/live_v3_separate_extraction_trial")


def _statement(feedback, quote, role="preference"):
    start = feedback.index(quote)
    return {"quote": quote, "role": role, "start": start, "end": start + len(quote)}


def _proposal(*quotes):
    return {"clauses": [{"quote": quote, "role": "preference", "detail": None} for quote in quotes],
            "signals": [{"clause_index": index} for index in range(len(quotes))]}


def _prediction(feedback, proposal, accepted):
    revision = sha256(feedback.encode()).hexdigest()
    return {"review_status": "PROFILE_FACT_REVIEW", "hard_constraint_action": "UNCHANGED",
            "interpretations": [{"clause_index": index,
                                 "evidence": [_span(feedback, proposal["clauses"][index]["quote"], "preference", revision)]}
                                for index in accepted],
            "validation_issues": [{"field": "signals", "index": index, "message": "Invalid signal."}
                                  for index in range(len(proposal["signals"])) if index not in accepted]}


def _receipt(statement, status, index=None, reason=None):
    return {"reaction_id": statement["reaction_id"], "status": status, "signal_index": index, "reason": reason}


class ReactionAccountingTests(unittest.TestCase):
    def setUp(self):
        self.first = "I like this opening."
        self.second = "I dislike the travel."
        self.fact = "I have not used its software."
        self.feedback = f"{self.first} {self.second} {self.fact}"
        self.statements = [_statement(self.feedback, quote) for quote in (self.first, self.second)]
        self.statements.append(_statement(self.feedback, self.fact, "profile_fact"))
        self.inventory = identify_reactions(self.feedback, self.statements)

    def test_ids_follow_source_revision_and_span_instead_of_order_or_role(self):
        reordered = identify_reactions(self.feedback, [{**self.statements[-1], "role": "context"}, *self.statements[:-1]])
        self.assertEqual([row["reaction_id"] for row in reordered],
                         [self.inventory[index]["reaction_id"] for index in (2, 0, 1)])
        revised = identify_reactions(self.feedback + " Revised.", self.statements)
        self.assertNotEqual(revised[0]["reaction_id"], self.inventory[0]["reaction_id"])
        for statements in ([{**self.statements[0], "start": False}], self.statements + self.statements[:1]):
            with self.assertRaises(ValueError):
                identify_reactions(self.feedback, statements)
        with self.assertRaises(ValueError):
            identify_reactions(f"{self.first} {self.first}", [self.statements[0]])
        with self.assertRaises(ValueError):
            audit_reactions(self.feedback, revised, {}, {})

    def test_saved_replay_exposes_both_missing_fi_041_reactions_and_preserves_neutral_case(self):
        for number in (1, 2):
            directory = _ARCHIVE / f"pass-{number}"
            inventories, proposals, predictions = [json.loads((directory / name).read_bytes()) for name in (
                "split.inventory.json", "split.proposals.json", "split.json",
            )]
            for cid in ("FI-041", "FS3-002"):
                with self.subTest(pass_number=number, case_id=cid):
                    feedback = predictions[cid]["original_feedback"]
                    inventory = identify_reactions(feedback, inventories[cid]["verified"])
                    before = deepcopy((inventory, proposals[cid], predictions[cid]))
                    audit = audit_reactions(feedback, inventory, proposals[cid], predictions[cid])
                    if cid == "FI-041":
                        flagged, = (row for row in audit["reactions"] if row["flagged"])
                        self.assertEqual(flagged["quote"], "This is a terrific AI advisor role")
                        self.assertEqual(flagged["status"], "needs_review")
                        self.assertEqual(audit["issues"], [{"code": "omitted_reaction", "reaction_id": flagged["reaction_id"]}])
                    else:
                        self.assertEqual(audit, {"reactions": [], "issues": []})
                    self.assertEqual((inventory, proposals[cid], predictions[cid]), before)

    def test_signal_uses_validated_index_and_retains_rejected_evidence(self):
        proposal = _proposal(self.first, self.second[:-1])
        prediction = _prediction(self.feedback, proposal, [1])
        receipts = [_receipt(self.inventory[index], "signal", index) for index in (0, 1)]
        first, second = audit_reactions(self.feedback, self.inventory, proposal, prediction, receipts)["reactions"]
        self.assertEqual((first["quote"], first["flagged"], first["validated_signal_index"]), (self.first, True, None))
        self.assertEqual((second["quote"], second["status"], second["flagged"], second["validated_signal_index"]),
                         (self.second, "signal", False, 0))
        self.assertEqual(audit_reactions(self.feedback, self.inventory, proposal, prediction)["issues"], [
            {"code": "signal_rejected", "reaction_id": self.inventory[0]["reaction_id"], "signal_index": 0},
        ])

    def test_explicit_context_or_review_stays_visible_and_requires_reason(self):
        proposal = _proposal()
        prediction = _prediction(self.feedback, proposal, [])
        receipts = [_receipt(self.inventory[0], "context", reason="The final classifier considered the opening clause context."),
                    _receipt(self.inventory[1], "needs_review", reason="The object of the objection needs clarification.")]
        audit = audit_reactions(self.feedback, self.inventory, proposal, prediction, receipts)
        self.assertEqual(audit["issues"], [])
        self.assertEqual([(row["status"], row["flagged"]) for row in audit["reactions"]],
                         [("context", True), ("needs_review", True)])
        receipts[0]["reason"] = " "
        receipts[1]["signal_index"] = 0
        malformed = audit_reactions(self.feedback, self.inventory, proposal, prediction, receipts)
        self.assertEqual([item["code"] for item in malformed["issues"]].count("invalid_disposition"), 2)

    def test_partial_overlap_and_multi_reaction_spans_do_not_clear_flags(self):
        partial = self.feedback[self.feedback.index("like"):self.feedback.index("dislike")]
        for quote, code in ((partial, "signal_anchor_mismatch"),
                            (f"{self.first} {self.second}", "ambiguous_signal_link")):
            with self.subTest(quote=quote):
                proposal = _proposal(quote)
                prediction = _prediction(self.feedback, proposal, [0])
                receipts = [_receipt(self.inventory[0], "signal", 0),
                            _receipt(self.inventory[1], "needs_review", reason="The reaction requires separate review.")]
                audit = audit_reactions(self.feedback, self.inventory, proposal, prediction, receipts)
                self.assertTrue(all(row["flagged"] for row in audit["reactions"]))
                self.assertEqual([item["code"] for item in audit["issues"]], [
                    code, "unaccounted_raw_signal", "unaccounted_validated_signal",
                ])

    def test_duplicate_unknown_and_non_preference_receipts_are_not_accounted(self):
        proposal = _proposal(self.first)
        prediction = _prediction(self.feedback, proposal, [0])
        receipts = [_receipt(self.inventory[0], "signal", 0), _receipt(self.inventory[0], "signal", 0),
                    _receipt(self.inventory[1], "signal", False), _receipt(self.inventory[2], "signal", 0),
                    {"reaction_id": "unknown", "status": "signal", "signal_index": 0, "reason": None}]
        audit = audit_reactions(self.feedback, self.inventory, proposal, prediction, receipts)
        self.assertTrue(all(row["flagged"] for row in audit["reactions"]))
        self.assertEqual({item["code"] for item in audit["issues"]}, {
            "duplicate_disposition", "invalid_disposition", "unknown_reaction_id", "missing_disposition",
            "non_preference_disposition", "unaccounted_raw_signal", "unaccounted_validated_signal",
        })
        empty_live = audit_reactions(self.feedback, self.inventory, proposal, prediction, [])
        self.assertTrue(all(row["flagged"] for row in empty_live["reactions"]))
        stale = deepcopy(prediction)
        stale["interpretations"][0]["evidence"][0]["source_revision"] = "old"
        stale_audit = audit_reactions(self.feedback, self.inventory, proposal, stale)
        self.assertEqual(stale_audit["issues"][0]["code"], "signal_rejected")

    def test_signal_receipt_requires_null_reason_and_a_unique_raw_index(self):
        proposal = _proposal(self.first)
        prediction = _prediction(self.feedback, proposal, [0])
        receipts = [_receipt(self.inventory[0], "signal", 0, "Retained."),
                    _receipt(self.inventory[1], "needs_review", reason="The second reaction has no linked signal.")]
        audit = audit_reactions(self.feedback, self.inventory, proposal, prediction, receipts)
        self.assertTrue(audit["reactions"][0]["flagged"])
        self.assertEqual(audit["issues"][0]["code"], "invalid_disposition")
        duplicate_links = [_receipt(item, "signal", 0) for item in self.inventory[:2]]
        audit = audit_reactions(self.feedback, self.inventory, proposal, prediction, duplicate_links)
        self.assertTrue(all(row["flagged"] for row in audit["reactions"]))
        self.assertEqual([item["code"] for item in audit["issues"]].count("ambiguous_signal_link"), 2)


if __name__ == "__main__":
    unittest.main()
