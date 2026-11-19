"""Flag duty emphasis inferred only from a quoted enthusiasm requirement."""

import re

from .feedback_evidence_checks_v3 import _NEGATIVE_DUTY_REACTION, _emphasizes, _finding, _words


_QUOTED_REQUIREMENT = re.compile(r"[\"'“‘](?P<requirement>must love (?P<duty>[^\"'”’\n]+))[\"'”’]", re.I)


def _duty_centrality(text, duty):
    text = re.sub(r"\bmust love\b", "", text)
    return _emphasizes(text, duty) or re.search(
        rf"\b{duty} (?:is|would be) the (?:heart|core|focus) of (?:the|this) (?:role|job|work)\b|"
        rf"\b(?:most|majority) of (?:each|the|a) (?:shift|day|week) (?:on|doing) {duty}\b|"
        rf"\b{duty} (?:takes|makes) up (?:most|the majority) of\b",
        text,
    )


def enthusiasm_scope_findings(clauses, signals):
    """Return review findings while preserving the candidate and its scope."""
    by_index = {clause["index"]: clause for clause in clauses}
    findings = []
    for index, signal in enumerate(signals):
        scope = signal["scope"]
        if (signal["dimension"], scope["type"], signal["polarity"]) != (
            "role_responsibilities", "role_feature", "negative",
        ):
            continue
        clause = by_index[signal["clause_index"]]
        evidence = clause["evidence"]
        quote = evidence["quote"]
        matches = list(_QUOTED_REQUIREMENT.finditer(quote))
        if len(matches) != 1 or not _NEGATIVE_DUTY_REACTION.search(quote):
            continue
        match = matches[0]
        duty_words = _words(match["duty"])
        if not duty_words:
            continue
        duty = re.escape(duty_words)
        referent = _words(scope["referent"])
        label = _words(signal["display_label"])
        if not re.search(rf"\b{duty}\b", referent):
            continue
        named_emphasis = _duty_centrality(label, duty) or _duty_centrality(referent, duty)
        measured = any(item["kind"] == "time_share" or (item["kind"] == "intensity" and referent == duty_words)
                       for item in scope["qualifiers"])
        rest = _words(quote[:match.start()] + " " + quote[match.end():])
        if (named_emphasis or measured) and not _duty_centrality(rest, duty):
            start = evidence["start"] + match.start("requirement")
            end = evidence["start"] + match.end("requirement")
            anchor = {**evidence, "quote": match["requirement"], "start": start, "end": end,
                      "role": "context"}
            findings.append(_finding(
                "enthusiasm_does_not_establish_workload", "blocking", clause["index"], index, [anchor, evidence],
                "The quoted enthusiasm requirement needs separate evidence for the proposed amount or centrality of the work.",
            ))
    return findings
