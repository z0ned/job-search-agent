"""Recover an explicit trip count when a held travel scope keeps only its cadence."""

import re
from hashlib import sha256

from .feedback import FeedbackOutputError
from .feedback_evidence_checks_v3 import _finding
from .feedback_v3 import _span


_NUMBER_WORDS = {word: index for index, word in enumerate((
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
))}
_NUMBER = rf"(?:[0-9]{{1,4}}(?:\.[0-9]+)?|{'|'.join(_NUMBER_WORDS)})"
_BOUND = (
    r"about|around|roughly|approximately|perhaps|maybe|at[\s-]+(?:most|least)|up\s+to|"
    r"(?:no\s+)?(?:more|less|fewer)\s+than|under|over|only|between|"
    r"as\s+(?:many|few)\s+as|(?:minimum|maximum)\s+of"
)
_COUNT = (rf"(?:(?:{_BOUND})\s+)?{_NUMBER}(?:\s*(?:[-–—/]|\bto\b|\bor\b|\band\b)\s*{_NUMBER})?"
          r"|a few|a couple of|a couple|several|some|no")
_TRIP = r"(?:(?:overnight|business|work|day|international|domestic|client|site|short)\s+){0,2}trips?"
_TRIP_COUNT = re.compile(
    rf"(?<![\w./\-–—])(?P<count>{_COUNT})\s+{_TRIP}\b",
    re.IGNORECASE,
)
_UNIT = r"day|week|month|quarter|year"
_PERIOD = rf"(?:every\s+{_NUMBER}\s+(?:{_UNIT})s|(?:a|an|per|each|every)\s+(?:{_UNIT})|daily|weekly|monthly|quarterly|yearly|annually)"
_CADENCE = re.compile(rf"\s+(?P<period>{_PERIOD})\b", re.IGNORECASE)
_CADENCE_VALUE = re.compile(rf"(?:(?:a|an|per|each|every)\s+)?(?P<unit>{_UNIT})", re.IGNORECASE)
_MULTI_PERIOD = re.compile(rf"every\s+(?P<number>{_NUMBER})\s+(?P<unit>{_UNIT})s", re.IGNORECASE)
_COMBINED = re.compile(
    rf"(?P<count>{_NUMBER}|once|twice)(?:\s+{_TRIP})?\s+(?P<period>{_PERIOD})",
    re.IGNORECASE,
)
_TRAVEL = re.compile(r"\b(?:travel|trips?)\b", re.IGNORECASE)
_CADENCE_ADVERBS = {
    "daily": "day", "weekly": "week", "monthly": "month", "quarterly": "quarter", "yearly": "year", "annually": "year",
}


def _integer(text):
    value = text.strip().casefold()
    if re.fullmatch(r"[0-9]{1,4}", value):
        return int(value)
    return _NUMBER_WORDS.get(value)


def _comparison_text(text):
    return " ".join(text.casefold().split())


def _period(text):
    value = _comparison_text(text)
    if unit := _CADENCE_ADVERBS.get(value):
        return 1, unit
    if simple := _CADENCE_VALUE.fullmatch(value):
        return 1, simple["unit"]
    if multiple := _MULTI_PERIOD.fullmatch(value):
        amount = _integer(multiple["number"])
        if amount:
            return amount, multiple["unit"]
    return None


def _combined(text):
    match = _COMBINED.fullmatch(text.strip())
    if match:
        count = {"once": 1, "twice": 2}.get(match["count"].casefold(), _integer(match["count"]))
        return count, _period(match["period"])
    return None


def _validated_anchor(feedback, revision, record, role, within=None):
    if record is None:
        return None
    try:
        anchor = _span(feedback, record.get("quote"), role, revision, within=within)
    except FeedbackOutputError:
        return None
    return anchor if anchor == record else None


def _linked_qualifier(feedback, revision, qualifier, assertion, start, end):
    if qualifier["source"] != "feedback":
        return False
    anchor = _validated_anchor(feedback, revision, qualifier.get("evidence"), "qualifier", assertion)
    return (anchor is not None and anchor["quote"] == qualifier["quote"]
            and start <= anchor["start"] < anchor["end"] <= end)


def _check_signal(feedback, revision, signal, assertion):
    """Return the new qualifier, whether review is needed, and the supporting span."""
    text = assertion["quote"]
    mentions = list(_TRIP_COUNT.finditer(text))
    measured = [(mention, cadence) for mention in mentions if (cadence := _CADENCE.match(text, mention.end()))]
    if not measured:
        return None, False, assertion

    if len(mentions) != 1:
        return None, True, assertion
    mention, cadence = measured[0]
    count, period = _integer(mention["count"]), _period(cadence["period"])
    if period is None:
        return None, True, assertion

    quote = text[mention.start():cadence.end()]
    try:
        bound = _span(feedback, quote, "qualifier", revision, within=assertion)
    except FeedbackOutputError:
        return None, True, assertion
    condition = signal.get("condition")
    if condition and (condition["evidence"]["start"] < bound["end"]
                      and bound["start"] < condition["evidence"]["end"]):
        return None, True, bound

    scope = signal["scope"]
    quantities = [item for item in scope["qualifiers"] if item["kind"] == "quantity"]
    frequencies = [item for item in scope["qualifiers"] if item["kind"] == "frequency"]
    if len(quantities) > 1 or len(frequencies) != 1:
        return None, True, bound
    frequency, = frequencies
    if not _linked_qualifier(feedback, revision, frequency, assertion, bound["start"], bound["end"]):
        return None, True, bound
    anchor = frequency["evidence"]
    full_anchor = (anchor["start"], anchor["end"]) == (bound["start"], bound["end"])
    cadence_anchor = (anchor["start"] >= assertion["start"] + cadence.start("period")
                      and _period(anchor["quote"]) == period)
    if not (full_anchor or cadence_anchor):
        return None, True, bound

    frequency_covers_count = (
        (count is not None and _combined(frequency["value"]) == (count, period))
        or (full_anchor and _comparison_text(frequency["value"]) == _comparison_text(quote))
    )
    if not frequency_covers_count and _period(frequency["value"]) != period:
        return None, True, bound
    if quantities:
        quantity, = quantities
        start = assertion["start"] + mention.start("count")
        end = assertion["start"] + mention.end("count")
        covered = (
            _linked_qualifier(feedback, revision, quantity, assertion, bound["start"], bound["end"])
            and quantity["evidence"]["start"] <= start and quantity["evidence"]["end"] >= end
            and ((count is not None and _integer(quantity["value"]) == count)
                 or _comparison_text(quantity["value"]) == _comparison_text(mention["count"]))
        )
        return None, not covered, bound
    if frequency_covers_count or _comparison_text(scope["referent"]) == _comparison_text(quote):
        return None, False, bound
    if (combined := _combined(scope["referent"])) is not None:
        return None, count is None or combined != (count, period), bound
    if count is None:
        return None, True, bound
    return {"kind": "quantity", "value": str(count), "source": "feedback", "quote": quote, "evidence": bound}, False, bound


def repair_travel_count(result):
    """Add an exact trip quantity to a held signal or flag its ambiguous scope."""
    feedback = result.get("original_feedback")
    if not isinstance(feedback, str):
        return result, []
    revision = sha256(feedback.encode()).hexdigest()
    interpretations = result["interpretations"]
    signals = list(interpretations)
    findings = list(result.get("evidence_findings", ()))
    repairs = []
    for index, signal in enumerate(interpretations):
        scope = signal["scope"]
        if (signal["application_status"] != "held_for_review" or signal["dimension"] != "work_arrangement"
                or scope["type"] != "travel_frequency" or not _TRAVEL.search(scope["referent"])):
            continue
        assertion = _validated_anchor(feedback, revision, signal["evidence"][0], "preference")
        if assertion is None:
            continue
        qualifier, needs_review, bound = _check_signal(feedback, revision, signal, assertion)
        clause_index = signal["clause_index"]
        if needs_review:
            finding = _finding(
                "travel_trip_count_needs_review", "blocking", clause_index, index,
                [assertion, bound] if assertion != bound else [assertion],
                "The feedback gives a trip count or limit. Check the count and cadence before treating this scope as settled.",
            )
            if finding not in findings:
                findings.append(finding)
        if qualifier is not None:
            evidence = qualifier["evidence"]
            signals[index] = {
                **signal, "scope": {**scope, "qualifiers": [*scope["qualifiers"], qualifier]},
                "evidence": signal["evidence"] if evidence in signal["evidence"] else [*signal["evidence"], evidence],
            }
            repairs.append({"signal_index": index, "clause_index": clause_index, "added_quantity": qualifier})
    if not repairs and findings == list(result.get("evidence_findings", ())):
        return result, []
    return {**result, "interpretations": signals, "evidence_findings": findings}, repairs
