"""Canonical matching and case diagnostics for the feedback benchmark."""

from collections import Counter, defaultdict, deque
from dataclasses import dataclass

from .feedback_taxonomy import CanonicalSignal, canonicalize_signal


@dataclass(frozen=True)
class _Signal:
    index: int
    canonical: CanonicalSignal
    condition: str | None
    strength: str
    evidence: str | None

    @property
    def feature_key(self):
        return self.canonical.dimension, self.canonical.feature_id, self.canonical.polarity

    @property
    def scope_key(self):
        return self.canonical.dimension, self.canonical.scope_type, self.canonical.scope_id

    @property
    def key(self):
        return self.feature_key, self.scope_key, self.condition

    def describe(self):
        return {
            **self.canonical.to_dict(),
            "index": self.index,
            "conditional": self.condition is not None,
            "strength": self.strength,
        }


def _indexed(signals):
    return [
        _Signal(index, canonicalize_signal(signal), signal.get("condition"), signal["strength"],
                signal.get("evidence_quote"))
        for index, signal in enumerate(signals)
    ]


def _pair(expected, actual, key):
    available = defaultdict(deque)
    for signal in actual:
        available[key(signal)].append(signal)

    pairs, missed, matched_indices = [], [], set()
    for signal in expected:
        candidates = available[key(signal)]
        if candidates:
            match = candidates.popleft()
            matched_indices.add(match.index)
            pairs.append((signal, match))
        else:
            missed.append(signal)
    extra = [signal for signal in actual if signal.index not in matched_indices]
    return pairs, missed, extra


def _describe_pairs(pairs):
    return [{"expected": expected.describe(), "actual": actual.describe()} for expected, actual in pairs]


def _unsupported_downgrades(expected, actual, feedback):
    references = defaultdict(list)
    for signal in expected:
        if signal.canonical.dimension == signal.canonical.scope_type == "career_category":
            references[signal.key].append(signal)

    unsupported, used = [], set()
    for signal in actual:
        canonical = signal.canonical
        if canonical.polarity != "negative" or "career_category" not in (canonical.dimension, canonical.scope_type):
            continue

        # A downgrade must quote the complete frozen evidence span to establish support.
        # A clipped quote can omit qualifications, negation, or the career reference itself.
        matching_reference = next((
            reference for reference in references[signal.key]
            if reference.index not in used and reference.evidence
            and signal.evidence and signal.evidence in feedback and reference.evidence in signal.evidence
        ), None)
        if matching_reference is None:
            unsupported.append(signal.describe())
        else:
            used.add(matching_reference.index)
    return unsupported


def compare_signals(expected_raw, actual_raw, feedback):
    """Compare canonical signals as multisets, keeping model and reference labels visible."""
    expected = _indexed(expected_raw)
    actual = _indexed(actual_raw)
    matched, missed, extra = _pair(expected, actual, lambda signal: signal.key)
    wrong_scope, residual_misses, residual_extras = _pair(
        missed, extra, lambda signal: (signal.feature_key, signal.condition),
    )
    wrong_condition, _, _ = _pair(
        residual_misses, residual_extras, lambda signal: (signal.feature_key, signal.scope_key),
    )

    return {
        "correct_signals": _describe_pairs(matched),
        "missed_signals": [signal.describe() for signal in missed],
        "extra_signals": [signal.describe() for signal in extra],
        "incorrectly_scoped_signals": _describe_pairs(wrong_scope),
        "incorrectly_conditioned_signals": _describe_pairs(wrong_condition),
        "dimension_and_scope_correct": (
            Counter(signal.scope_key for signal in expected) == Counter(signal.scope_key for signal in actual)
        ),
        "unsupported_career_category_downgrades": _unsupported_downgrades(expected, actual, feedback),
    }


def consistency_signature(signals):
    """Compare semantic content and strength across independent passes."""
    return Counter((signal.key, signal.strength) for signal in _indexed(signals))
