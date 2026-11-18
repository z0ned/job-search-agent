"""Identify narrow semantic issues in anchored, validated feedback records."""

import re


_DUTY_VERB = r"(?:(?:doing|handling|giving|performing|delivering|creating|writing|running)\s+)?"
_DUTY_SUFFIX = re.compile(r"\s+(?:work|duties|responsibilities|tasks|activities)$")
_EMPHASIS_PREFIX = (
    r"(?:must love|focus(?:ed|es|ing)? on|cent(?:ered|red) (?:on|around)|built around|dominated by|mostly|primarily)"
)
_EMPHASIS_SUFFIX = r"(?:heavy|focused|centric|intensive|emphasis|dominated)"
_EMPHATIC_SCOPE = re.compile(rf"\b(?:{_EMPHASIS_PREFIX}|{_EMPHASIS_SUFFIX})\b")
_EMPHATIC_QUALIFIER = re.compile(
    r"(?:strong|heavy|high|central|primary|dominant|intensive|focused)(?: emphasis| focus| intensity)?|"
    r"(?:most|majority) of .+|built around"
)
_NEGATIVE_DUTY_REACTION = re.compile(
    r"\b(?:i (?:want to (?:avoid|steer clear of)|would avoid|do not want|don['’]t want|dislike|hate)|"
    r"what i (?:want|would like) to avoid)\b",
    re.IGNORECASE,
)
_DISTRUST = re.compile(
    r"\b(?:i (?:do not|don['’]t|cannot|can['’]t) trust|i (?:distrust|have no trust in))\b",
    re.IGNORECASE,
)
_TITLE = r"(?P<title>(?:[\w'’\-]+\s+){1,8})(?:role|opening|position|job)"
_PRAISE = r"(?:terrific|excellent|great|fantastic|outstanding|wonderful|appealing|attractive|exciting)"
_POSTING_PRAISE = tuple(re.compile(rf"(?:but\s+)?{pattern}[.,!?;]*", re.IGNORECASE) for pattern in (
    rf"this (?:is|would be|looks like) (?:a |an )?{_PRAISE} {_TITLE}",
    rf"this (?:particular |specific )?{_TITLE} (?:is|would be|looks|sounds|seems) {_PRAISE}",
    rf"i (?:love|really like|would love) this (?:particular |specific )?{_TITLE}",
))
_GENERIC_TITLE_WORDS = {"particular", "specific", "current", "new", "posted", "listed", "advertised", "open"}


def _words(text):
    return " ".join(re.findall(r"[^\W_]+", text.casefold()))


def _emphasizes(text, duty):
    return re.search(
        rf"\b{_EMPHASIS_PREFIX}\s+{_DUTY_VERB}{duty}\b|"
        rf"\b{duty}\s+(?:{_EMPHASIS_SUFFIX}|"
        r"as (?:the )?(?:heart|core|focus) of (?:the|this) (?:role|job|position))\b",
        text,
    )


def _lost_duty_emphasis(signal, quote):
    scope = signal["scope"]
    if (signal["dimension"] != "role_responsibilities" or scope["type"] != "role_feature"
            or signal["polarity"] != "negative" or not _NEGATIVE_DUTY_REACTION.search(quote)):
        return False
    referent = _words(scope["referent"])
    if _EMPHATIC_SCOPE.search(referent) or any(
        qualifier["kind"] in {"intensity", "time_share"}
        and _EMPHATIC_QUALIFIER.fullmatch(_words(qualifier["value"]))
        for qualifier in scope["qualifiers"]
    ):
        return False
    duty = _DUTY_SUFFIX.sub("", referent)
    duty = re.escape(re.sub(rf"^{_DUTY_VERB}", "", duty))
    return bool(duty and _emphasizes(_words(quote), duty) and _emphasizes(_words(signal["display_label"]), duty))


def _identified_posting_praise(quote):
    for pattern in _POSTING_PRAISE:
        match = pattern.fullmatch(quote.strip())
        if match and set(_words(match["title"]).split()) - _GENERIC_TITLE_WORDS:
            return True
    return False


def _same_feedback(first, second):
    return first["origin"] == second["origin"] == "feedback" and first["source_revision"] == second["source_revision"]


def _finding(code, severity, clause_index, signal_index, evidence, message):
    return {
        "code": code, "severity": severity, "clause_index": clause_index, "signal_index": signal_index,
        "evidence": [dict(span) for span in evidence], "message": message,
    }


def evidence_findings(clauses, signals) -> list[dict]:
    """Return findings without changing validated records or creating preferences.

    A blocking finding identifies a signal whose machine scope needs review.
    A diagnostic finding identifies a possible omission for human review.
    Signal indices refer to the supplied validated list and are zero-based.
    """
    by_index = {clause["index"]: clause for clause in clauses}
    findings = []
    distrust, posting_signals = [], []
    for index, signal in enumerate(signals):
        clause = by_index[signal["clause_index"]]
        assertion = clause["evidence"]
        quote = assertion["quote"]
        if _lost_duty_emphasis(signal, quote):
            findings.append(_finding(
                "duty_emphasis_lost", "blocking", clause["index"], index, [assertion],
                "The machine scope omits the duty emphasis present in the evidence and display label.",
            ))
        if (signal["scope"]["type"] == "employer" and signal["polarity"] == "negative"
                and _DISTRUST.search(quote)):
            distrust.append(assertion)
        if (signal["dimension"] == "role_responsibilities" and signal["scope"]["type"] == "posting_role"
                and signal["polarity"] == "positive"):
            posting_signals.append(assertion)

    for clause in clauses:
        praise = clause["evidence"]
        if clause["role"] != "context" or not _identified_posting_praise(praise["quote"]):
            continue
        if any(_same_feedback(praise, signal) and praise["start"] < signal["end"] and signal["start"] < praise["end"]
               for signal in posting_signals):
            continue
        contrast = next((assertion for assertion in distrust if _same_feedback(praise, assertion)
                         and (praise["end"] <= assertion["start"] or assertion["end"] <= praise["start"])), None)
        if contrast is not None:
            findings.append(_finding(
                "posting_praise_in_context", "diagnostic", clause["index"], None, [praise, contrast],
                "The context clause praises an identified posting independently of the employer objection.",
            ))
    return findings
