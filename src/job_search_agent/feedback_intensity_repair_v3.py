"""Prepare an archived proposal with redundant, anchored intensity qualifiers."""

from collections import Counter
from collections.abc import Mapping
from hashlib import sha256

from .feedback import FeedbackOutputError
from .feedback_conditions_v3 import recover_condition
from .feedback_extraction_schema_v3 import INTENSITY_VALUES
from .feedback_v3 import _clause, _condition, _qualifier


def _coalesce(signal, raw_clause, feedback, revision, context):
    if signal.keys() != {"clause_index", "dimension", "display_label", "polarity", "strength", "scope", "condition"}:
        return None
    scope = signal.get("scope")
    if not isinstance(scope, Mapping) or scope.keys() != {"type", "referent", "qualifiers"}:
        return None
    qualifiers = scope["qualifiers"]
    if not isinstance(qualifiers, list) or not all(isinstance(item, Mapping) for item in qualifiers):
        return None
    positions = [index for index, item in enumerate(qualifiers) if item.get("kind") == "intensity"]
    if len(positions) < 2:
        return None

    try:
        clause = _clause(raw_clause, feedback, revision)
        if clause["role"] != "preference":
            return None
        assertion = clause["evidence"]
        anchored = [_qualifier(item, feedback, revision, assertion, context) for item in qualifiers]
        condition = _condition(signal.get("condition"), feedback, revision, assertion)
    except FeedbackOutputError:
        return None

    kinds = Counter(item["kind"] for item in anchored)
    if any(count > 1 and kind != "intensity" for kind, count in kinds.items()):
        return None
    levels = {anchored[index]["value"].casefold() for index in positions}
    if len(levels) != 1 or not levels.issubset(INTENSITY_VALUES):
        return None

    first, *redundant = positions
    omitted = set(redundant)
    retained = [item for index, item in enumerate(anchored) if index not in omitted]
    if recover_condition(condition, anchored, assertion, feedback, revision)[0] != recover_condition(
        condition, retained, assertion, feedback, revision,
    )[0]:
        return None

    level, = levels
    prepared = [dict(item, value=level) if index == first else item
                for index, item in enumerate(qualifiers) if index not in omitted]
    primary = anchored[first]["evidence"]
    additional = []
    for index in redundant:
        evidence = anchored[index]["evidence"]
        if evidence != primary and evidence not in additional:
            additional.append(evidence)
    return dict(signal, scope=dict(scope, qualifiers=prepared)), additional


def prepare_duplicate_intensity(proposal, feedback, context):
    """Coalesce equal controlled levels and return supplemental evidence by clause index.

    Preserve the original proposal and require normal validation after preparation.
    Attach supplemental evidence only to its accepted preference signal.
    """
    if (not isinstance(proposal, Mapping) or proposal.keys() != {"clauses", "signals"}
            or not isinstance(proposal["clauses"], list) or not isinstance(proposal["signals"], list)
            or not isinstance(feedback, str)):
        return proposal, {}
    clauses, signals = proposal["clauses"], proposal["signals"]
    cited_clauses = [item.get("clause_index") if isinstance(item, Mapping) else None for item in signals]
    cited_counts = Counter(index for index in cited_clauses if type(index) is int)
    revision = sha256(feedback.encode()).hexdigest()
    replacements, additional = {}, {}
    for position, clause_index in enumerate(cited_clauses):
        if type(clause_index) is not int or not 0 <= clause_index < len(clauses) or cited_counts[clause_index] != 1:
            continue
        prepared = _coalesce(signals[position], clauses[clause_index], feedback, revision, context)
        if prepared is not None:
            replacements[position], additional[clause_index] = prepared
    if not replacements:
        return proposal, {}
    return dict(proposal, signals=[replacements.get(index, item) for index, item in enumerate(signals)]), additional
