"""Recover a narrowly supported applicability condition from validated evidence."""

import re


_MARKER = re.compile(r"\b(?:provided(?:[ \t]+that)?|only[ \t]+if|as[ \t]+long[ \t]+as|if)\b", re.IGNORECASE)
_DIRECT_PREFERENCE = re.compile(
    r"^(?:I|we)(?:['’]d|\s+(?:would|could|might|do))?\s+(?:not\s+)?"
    r"(?:enjoy|like|love|prefer|want|welcome|accept|avoid|consider|choose)\s+\S",
    re.IGNORECASE,
)
_AMBIGUOUS_PREFIX = re.compile(
    r"[.!?;:\r\n]|\b(?:and|or|but|although|even|when|whether|unless|because|ask\w*|"
    r"check\w*|confirm\w*|determin\w*|discover\w*|evaluat\w*|figur\w*[ \t]+out|inspect\w*|know\w*|learn\w*|"
    r"see\w*|test\w*|understand\w*|verif\w*|wonder\w*|find\w*[ \t]+out)\b",
    re.IGNORECASE,
)
_QUOTE = re.compile(r'[`"“”«»]|(?<!\w)[\'‘’]|[\'‘’](?!\w)')
_APPLICABILITY_SUBJECT = re.compile(
    r"[ \t]+(?:(?:it|they)[ \t]+(?:takes?|lasts?|requires?|runs?|occurs?|is required|are required)|"
    r"(?:I|we)[ \t]+(?:(?:had|have|need|would have|would need)[ \t]+to[ \t]+)?"
    r"(?:do|handle|perform|run|lead)[ \t]+(?:it|them))[ \t]+",
    re.IGNORECASE,
)
_COUNT = r"(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
_UNIT = r"(?:minute|hour|shift|day|workday|week|month|quarter|year|time)s?"
_UPPER_BOUND = re.compile(
    rf"(?:at most|no more than|up to|fewer than|less than)[ \t]+(?:once|twice|thrice|{_COUNT}[ \t]+{_UNIT})"
    r"(?:[ \t]+(?:(?:per|a|each|every)[ \t]+(?:shift|day|workday|week|month|quarter|year)|"
    r"daily|weekly|monthly|quarterly|yearly))?",
    re.IGNORECASE,
)
_LIMIT_KINDS = {"frequency", "duration", "time_share", "quantity"}


def _anchored(evidence, role, feedback, revision):
    if not evidence or evidence.get("origin") != "feedback" or evidence.get("role") != role:
        return False
    start, end = evidence.get("start"), evidence.get("end")
    return (
        evidence.get("source_revision") == revision
        and type(start) is int and type(end) is int and 0 <= start < end <= len(feedback)
        and feedback[start:end] == evidence.get("quote")
    )


def _complete_assertion(assertion, feedback):
    prefix, suffix = feedback[:assertion["start"]], feedback[assertion["end"]:]
    quote = assertion["quote"]
    starts_sentence = not prefix.strip() or re.search(r"[.!?]\s+$", prefix) is not None
    ends_sentence = (
        not suffix.strip()
        or (quote.endswith((".", "!")) and suffix[0].isspace())
        or re.match(r"[.!](?:\s|$)", suffix) is not None
    )
    return starts_sentence and ends_sentence and "?" not in quote


def recover_condition(condition, qualifiers, assertion, feedback, revision):
    """Relocate an exact anchored bound from scope into an explicit trailing condition.

    Accept only a direct preference followed by a single applicability phrase
    with an unambiguous reference to its subject and a terminal upper bound.
    Both the limit and the full assertion must retain their original anchors.
    """
    if (condition is not None or not _anchored(assertion, "preference", feedback, revision)
            or not _complete_assertion(assertion, feedback) or _QUOTE.search(feedback)):
        return condition, qualifiers

    quote = assertion["quote"].rstrip()
    if quote.endswith((".", "!")):
        quote = quote[:-1].rstrip()
    markers = list(_MARKER.finditer(quote))
    if len(markers) != 1:
        return condition, qualifiers
    marker, = markers
    prefix = quote[:marker.start()].rstrip()
    # A bare "if" also introduces embedded questions. Recover it only when
    # punctuation separates the applicability phrase from the preference.
    if marker.group().casefold() == "if" and not prefix.endswith(","):
        return condition, qualifiers
    antecedent = prefix.removesuffix(",").strip()
    predicate = _APPLICABILITY_SUBJECT.match(quote, marker.end())
    if (not _DIRECT_PREFERENCE.match(antecedent) or _AMBIGUOUS_PREFIX.search(antecedent)
            or predicate is None or not _UPPER_BOUND.fullmatch(quote[predicate.end():])):
        return condition, qualifiers

    start = assertion["start"] + marker.start()
    bound_start = assertion["start"] + predicate.end()
    end = assertion["start"] + len(quote)
    for index, qualifier in enumerate(qualifiers):
        evidence = qualifier.get("evidence")
        if (qualifier.get("kind") in _LIMIT_KINDS and qualifier.get("source") == "feedback"
                and _anchored(evidence, "qualifier", feedback, revision)
                and (evidence["start"], evidence["end"]) == (bound_start, end)
                and qualifier.get("value") == qualifier.get("quote") == evidence["quote"]):
            limit_index = index
            break
    else:
        return condition, qualifiers

    rest = [qualifier for index, qualifier in enumerate(qualifiers) if index != limit_index]
    if any(
        evidence.get("end", 0) > start
        for qualifier in rest if (evidence := qualifier.get("evidence")) and evidence.get("origin") == "feedback"
    ):
        return condition, qualifiers
    exact_quote = feedback[start:end]
    return {
        "kind": "other",
        "value": quote[marker.end():].strip(),
        "quote": exact_quote,
        "evidence": {"origin": "feedback", "role": "condition", "source_revision": revision,
                     "start": start, "end": end, "quote": exact_quote},
    }, rest
