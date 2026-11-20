"""Carry an anchored posting verification into the existing clarification route."""

from collections.abc import Mapping
from hashlib import sha256
import re

from .feedback import NEEDS_CLARIFICATION, UNCHANGED, FeedbackOutputError
from .feedback_v3 import _span


_GENERIC_QUESTION = "What specifically influenced your reaction to this opportunity?"
_REQUEST = r"(?:(?:can|could|would) you (?:please )?|please )(?:check|confirm|verify|clarify|find out|tell me)"
_INTERROGATIVE = r"how (?:often|many|much|long|far)|what|when|where|which"
_UNCERTAINTY = (
    r"i (?:can['’]t|cannot|couldn['’]t|can not|could not) tell from "
    r"(?:the|this) (?:listing|posting|job description|job ad)"
)
_EMBEDDED_QUESTION = re.compile(
    rf"(?:(?:{_REQUEST})|(?:{_UNCERTAINTY})) "
    rf"(?P<cue>if|whether|{_INTERROGATIVE}) (?P<target>.+?)[.!?]?",
    re.IGNORECASE,
)
_DIRECT_QUESTION = re.compile(
    rf"(?:{_REQUEST} (?:the|this|that) .+|(?:{_INTERROGATIVE}) .+|"
    r"(?:is|are|does|do|will) (?:the|this|these) .+)\?",
    re.IGNORECASE,
)
_GENERIC_FOLLOWUP = re.compile(rf"{_REQUEST}(?: (?:which|that|this|it))?[.!?]?", re.IGNORECASE)
_UNRESOLVED_TARGET = re.compile(
    r"^(?:it|this|that|they|these|those) (?:is|are|was|were|would be|will be)\b",
    re.IGNORECASE,
)
_REQUEST_START = re.compile(rf"(?:(?:can|could|would) you|please|{_UNCERTAINTY})\b", re.IGNORECASE)
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+")


def _source_question(quote):
    questions = []
    for sentence in _SENTENCE_BREAK.split(quote.strip()):
        embedded = _EMBEDDED_QUESTION.fullmatch(sentence)
        if embedded:
            cue, target = embedded.group("cue", "target")
            if len(target.split()) < 3 or _UNRESOLVED_TARGET.match(target):
                return None
            cue = "whether" if cue.lower() in {"if", "whether"} else cue.lower()
            questions.append(f"Could you verify {cue} {target.strip()}?")
        elif _DIRECT_QUESTION.fullmatch(sentence):
            questions.append(sentence)
        elif (sentence.endswith("?") or _REQUEST_START.match(sentence)) and not _GENERIC_FOLLOWUP.fullmatch(sentence):
            return None
    return questions[0] if len(questions) == 1 else None


def repair_posting_verification(result):
    """Replace only the generic fallback for a single grounded verification."""
    if (
        result.get("review_status") != NEEDS_CLARIFICATION
        or result.get("hard_constraint_action") != UNCHANGED
        or result.get("hard_constraints_mutated") is not False
        or result.get("eligibility_violation") is not None
        or result.get("profile_fact_candidate") is not None
        or result.get("clarification_question") != _GENERIC_QUESTION
        or result.get("interpretations")
        or result.get("validation_issues")
    ):
        return result, None

    clauses = result.get("clauses")
    if not isinstance(clauses, list) or any(
        not isinstance(clause, Mapping)
        or clause.get("role") in ("preference", "profile_fact", "rule_reconsideration", "vague_reaction")
        for clause in clauses
    ):
        return result, None
    verification = [clause for clause in clauses if clause.get("role") == "posting_verification"]
    if len(verification) != 1:
        return result, None
    clause = verification[0]
    source, evidence = result.get("original_feedback"), clause.get("evidence")
    if not isinstance(source, str) or not isinstance(evidence, Mapping) or type(clause.get("index")) is not int:
        return result, None
    try:
        anchor = _span(source, evidence.get("quote"), "posting_verification", sha256(source.encode()).hexdigest())
    except FeedbackOutputError:
        return result, None
    if evidence != anchor or any(type(evidence[key]) is not int for key in ("start", "end")):
        return result, None

    question = _source_question(anchor["quote"])
    if not question:
        return result, None
    return {**result, "clarification_question": question}, {
        "clause_index": clause["index"],
        "evidence": anchor,
        "before": _GENERIC_QUESTION,
        "after": question,
    }
