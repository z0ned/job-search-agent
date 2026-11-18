"""Experimental schema for the isolated feedback extraction trial."""

from collections.abc import Mapping
from copy import deepcopy

from .feedback import _enum, _strict_object
from .feedback_extraction_v3 import DIMENSION_SCOPES, QUALIFIER_KINDS, _PROPOSAL_SCHEMA


INTENSITY_VALUES = ("none", "near_zero", "low", "moderate", "high", "strong", "dominant")


def _build_trial_schema():
    proposal = deepcopy(_PROPOSAL_SCHEMA)
    signals = proposal["properties"]["signals"]
    signal = signals["items"]["properties"]
    scope = signal["scope"]["properties"]
    qualifier = scope["qualifiers"]["items"]["properties"]
    signal_fields = {name: field for name, field in signal.items() if name != "dimension"}
    qualifier_variants = {
        "anyOf": [
            _strict_object({
                **qualifier, "kind": _enum("intensity"), "value": _enum(*INTENSITY_VALUES),
                "source": _enum("feedback"),
            }),
            _strict_object({**qualifier, "kind": _enum(*(kind for kind in QUALIFIER_KINDS if kind != "intensity"))}),
        ],
    }
    signals["items"] = {
        "anyOf": [
            _strict_object({
                "dimension": _enum(dimension),
                **signal_fields,
                "scope": _strict_object({
                    **scope,
                    "type": _enum(*scope_types),
                    "qualifiers": {**scope["qualifiers"], "items": qualifier_variants},
                }),
            })
            for dimension, scope_types in DIMENSION_SCOPES.items()
        ],
    }
    return proposal


TRIAL_SCHEMA = _build_trial_schema()


def schema_issues(proposal):
    """Check the trial's narrowed constraints before validating evidence and routing."""
    signals = proposal.get("signals") if isinstance(proposal, Mapping) else None
    if not isinstance(signals, list):
        return [{"field": "signals", "index": None, "message": "Expected a list of signals."}]

    issues = []
    for index, signal in enumerate(signals):
        dimension = signal.get("dimension") if isinstance(signal, Mapping) else None
        scope = signal.get("scope") if isinstance(signal, Mapping) else None
        scope_type = scope.get("type") if isinstance(scope, Mapping) else None
        if not isinstance(dimension, str) or scope_type not in DIMENSION_SCOPES.get(dimension, ()):
            issues.append({"field": "signals", "index": index, "message": "Incompatible dimension and scope type."})

        qualifiers = scope.get("qualifiers") if isinstance(scope, Mapping) else None
        if not isinstance(qualifiers, list):
            continue
        for qualifier in qualifiers:
            if not isinstance(qualifier, Mapping) or qualifier.get("kind") != "intensity":
                continue
            if qualifier.get("value") not in INTENSITY_VALUES:
                issues.append({"field": "signals", "index": index, "message": "Intensity must use a controlled level."})
            if qualifier.get("source") != "feedback":
                issues.append({"field": "signals", "index": index, "message": "Intensity must cite original feedback."})
    return issues
