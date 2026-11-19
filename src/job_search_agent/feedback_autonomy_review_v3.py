"""Flag a dropped near-zero scope bound in held seniority proposals."""

import re

from .feedback_evidence_checks_v3 import _finding, _words


_AUTONOMY_REFERENT = re.compile(r"(?:decision making )?(?:autonomy|authority)(?: (?:over|to|in|for|on) .+)?")
_NEAR_ZERO = r"(?:almost|nearly|virtually|practically)\s+no"
_NEAR_ZERO_VALUES = {"near zero", "almost no", "nearly no", "virtually no", "practically no"}


def _has_grounded_bound(qualifier, assertion, bound):
    if qualifier["kind"] != "intensity" or _words(qualifier["value"]) not in _NEAR_ZERO_VALUES:
        return False
    anchor = qualifier["evidence"]
    if anchor["origin"] != "feedback" or anchor["source_revision"] != assertion["source_revision"]:
        return False
    offset = assertion["start"]
    start, end = anchor["start"] - offset, anchor["end"] - offset
    return (0 <= start <= bound.start(1) < bound.end(1) <= end <= len(assertion["quote"])
            and assertion["quote"][start:end] == anchor["quote"])


def near_zero_autonomy_findings(clauses, signals):
    """Review exact scope omissions without changing proposals or their evidence."""
    by_index = {clause["index"]: clause for clause in clauses}
    findings = []
    for index, signal in enumerate(signals):
        scope = signal["scope"]
        if (signal["dimension"] != "seniority_scope" or scope["type"] != "seniority_feature"
                or signal["polarity"] != "negative"):
            continue
        referent = _words(scope["referent"])
        if not _AUTONOMY_REFERENT.fullmatch(referent):
            continue
        target = r"\b" + r"[\s-]+".join(map(re.escape, referent.split())) + r"\b"
        clause = by_index[signal["clause_index"]]
        assertion = clause["evidence"]
        quote = assertion["quote"]
        # The bound must modify the one occurrence of the exact machine target.
        bound = re.search(rf"\b({_NEAR_ZERO})\s+{target}", quote, re.IGNORECASE)
        if (bound is None or len(re.findall(target, quote, re.IGNORECASE)) != 1
                or any(_has_grounded_bound(item, assertion, bound) for item in scope["qualifiers"])):
            continue
        findings.append(_finding(
            "near_zero_autonomy_bound_lost", "blocking", clause["index"], index, [assertion],
            "The evidence concerns almost no autonomy or authority. The proposed scope omits that limit.",
        ))
    return findings
