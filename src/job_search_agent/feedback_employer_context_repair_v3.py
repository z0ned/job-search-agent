"""Prepare a verbatim employer evidence span for an explicit career exception."""

from collections import Counter
from collections.abc import Mapping
import re

from .feedback import STRENGTHS, _nonblank


_POSITIVE_CAREER_PREFIX = re.compile(r"I (?:would )?(?:love|like|enjoy) (?:a|an|the) ", re.IGNORECASE)
_CAREER_TARGET = re.compile(r"[\w &'’/-]+ careers?", re.IGNORECASE)
_EMPLOYER = re.compile(r"[\w &'’/-]+")
_SIGNAL_FIELDS = {"clause_index", "dimension", "display_label", "polarity", "strength", "scope", "condition"}


def _unique_start(feedback, quote):
    start = feedback.find(quote)
    if start >= 0 and feedback.find(quote, start + 1) < 0:
        return start
    return None


def _preference_quotes(clauses, signals, feedback):
    indices = Counter(
        signal.get("clause_index") for signal in signals
        if isinstance(signal, Mapping) and type(signal.get("clause_index")) is int
    )
    quotes = Counter(
        clause.get("quote") for clause in clauses
        if isinstance(clause, Mapping) and isinstance(clause.get("quote"), str)
    )
    for signal in signals:
        if (not isinstance(signal, Mapping) or signal.keys() != _SIGNAL_FIELDS
                or signal["strength"] not in STRENGTHS or not _nonblank(signal["display_label"])):
            continue
        index = signal.get("clause_index")
        if type(index) is not int or not 0 <= index < len(clauses) or indices[index] != 1:
            continue
        clause = clauses[index]
        if (not isinstance(clause, Mapping) or clause.keys() != {"role", "quote", "detail"}
                or clause["role"] != "preference" or clause["detail"] is not None and not _nonblank(clause["detail"])):
            continue
        quote, scope = clause["quote"], signal["scope"]
        if (not _nonblank(quote) or quotes[quote] != 1
                or not isinstance(scope, Mapping) or scope.keys() != {"type", "referent", "qualifiers"}):
            continue
        start = _unique_start(feedback, quote)
        if start is not None:
            yield index, signal, quote, start


def _career_spans(candidates, feedback):
    for _, signal, quote, start in candidates:
        scope = signal["scope"]
        target = scope.get("referent")
        if (signal.get("dimension") != "career_category" or signal.get("polarity") != "positive"
                or scope.get("type") != "career_category" or signal.get("condition") is not None or scope["qualifiers"] != []
                or not isinstance(target, str) or not _CAREER_TARGET.fullmatch(target)
                or not quote.endswith(target) or not _POSITIVE_CAREER_PREFIX.fullmatch(quote[:-len(target)])):
            continue
        prefix = feedback[:start].rstrip()
        if prefix and (prefix[-1] not in ".!?" or not feedback[start - 1].isspace()):
            continue
        end = start + len(quote)
        yield target, end - len(target), end


def _employer_target(signal, quote, following):
    scope = signal["scope"]
    employer = scope.get("referent")
    qualifiers = scope.get("qualifiers")
    if (signal.get("dimension") != "employer" or signal.get("polarity") != "negative"
            or scope.get("type") != "employer" or signal.get("condition") is not None
            or not isinstance(employer, str) or not _EMPLOYER.fullmatch(employer)
            or quote.removesuffix(".") != f"just not at {employer}"
            or not isinstance(qualifiers, list) or len(qualifiers) != 1):
        return None
    if not quote.endswith(".") and following and not following.startswith("."):
        return None
    following = following.removeprefix(".") if not quote.endswith(".") else following
    if following and not following[0].isspace():
        return None
    qualifier = qualifiers[0]
    if (not isinstance(qualifier, Mapping) or qualifier.keys() != {"kind", "source", "quote", "value"}
            or qualifier.get("kind") != "career_context"
            or qualifier.get("source") != "feedback" or qualifier.get("quote") != qualifier.get("value")):
        return None
    return qualifier.get("quote")


def prepare_employer_career_context(proposal, feedback):
    """Extend only a grounded comma-linked employer exception before strict validation."""
    if not isinstance(proposal, Mapping) or proposal.keys() != {"clauses", "signals"} or not isinstance(feedback, str):
        return proposal
    clauses, signals = proposal.get("clauses"), proposal.get("signals")
    if not isinstance(clauses, list) or not isinstance(signals, list):
        return proposal

    candidates = list(_preference_quotes(clauses, signals, feedback))
    career_spans = list(_career_spans(candidates, feedback))
    repairs = {}
    for index, signal, quote, start in candidates:
        end = start + len(quote)
        target = _employer_target(signal, quote, feedback[end:])
        if not isinstance(target, str):
            continue
        for career, career_start, career_end in career_spans:
            if target != career or not re.fullmatch(r",[ \t]+", feedback[career_end:start]):
                continue
            expanded = feedback[career_start:end]
            if _unique_start(feedback, expanded) == career_start and not any(
                isinstance(other, Mapping) and other.get("quote") == expanded for other in clauses
            ):
                repairs[index] = dict(clauses[index], quote=expanded)
    if not repairs:
        return proposal
    return dict(proposal, clauses=[repairs.get(index, clause) for index, clause in enumerate(clauses)])
