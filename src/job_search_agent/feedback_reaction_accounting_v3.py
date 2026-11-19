"""Audit the handoff from saved reaction quotes to final preference proposals."""

from collections import Counter, defaultdict
from collections.abc import Mapping
from hashlib import sha256

from .feedback import FeedbackOutputError, _nonblank
from .feedback_extraction_v3 import CLAUSE_ROLES
from .feedback_v3 import _span


_STATEMENT_FIELDS = {"quote", "role", "start", "end"}
_RECEIPT_FIELDS = {"reaction_id", "status", "signal_index", "reason"}


def identify_reactions(feedback_text, statements):
    """Add a revision-bound ID to each uniquely located verified quote."""
    if not isinstance(feedback_text, str) or not isinstance(statements, list):
        raise ValueError("Expected original feedback text and an array of verified statements.")
    revision = sha256(feedback_text.encode()).hexdigest()
    identified = []
    used = set()
    for statement in statements:
        if (not isinstance(statement, Mapping) or statement.keys() != _STATEMENT_FIELDS
                or statement["role"] not in CLAUSE_ROLES):
            raise ValueError("Invalid verified statement fields.")
        try:
            span = _span(feedback_text, statement["quote"], statement["role"], revision)
        except FeedbackOutputError as error:
            raise ValueError("Verified statement must retain its unique verbatim source quote.") from error
        offsets = statement["start"], statement["end"]
        if (any(type(offset) is not int for offset in offsets)
                or offsets != (span["start"], span["end"]) or offsets in used):
            raise ValueError("Verified statement has changed or duplicated source offsets.")
        used.add(offsets)
        identity = f"{revision}:{span['start']}:{span['end']}"
        reaction_id = "r-" + sha256(identity.encode()).hexdigest()[:20]
        identified.append({**statement, "reaction_id": reaction_id})
    return identified


def _array(record, field):
    values = record.get(field) if isinstance(record, Mapping) else None
    return values if isinstance(values, list) else []


def _raw_links(feedback_text, revision, reactions, proposal):
    clauses = _array(proposal, "clauses")
    raw_signals = _array(proposal, "signals")
    spans = {}
    for index, clause in enumerate(clauses):
        if not isinstance(clause, Mapping) or clause.get("role") != "preference":
            continue
        try:
            spans[index] = _span(feedback_text, clause.get("quote"), "preference", revision)
        except FeedbackOutputError:
            continue
    source_clauses = [signal.get("clause_index") if isinstance(signal, Mapping) else None for signal in raw_signals]
    links = {}
    for index, clause_index in enumerate(source_clauses):
        span = spans.get(clause_index) if type(clause_index) is int else None
        links[index] = [rid for rid, reaction in reactions.items() if span is not None and (
            span["start"] <= reaction["start"] < reaction["end"] <= span["end"]
            or reaction["start"] <= span["start"] < span["end"] <= reaction["end"]
        )]
    return links, source_clauses, spans


def _accepted_links(source_clauses, raw_spans, prediction):
    by_clause = defaultdict(list)
    for index, signal in enumerate(_array(prediction, "interpretations")):
        clause_index = signal.get("clause_index") if isinstance(signal, Mapping) else None
        evidence = _array(signal, "evidence")
        if type(clause_index) is int and clause_index in raw_spans and evidence and evidence[0] == raw_spans[clause_index]:
            by_clause[clause_index].append(index)
    uses = Counter(index for index in source_clauses if type(index) is int)
    rejected = {issue["index"] for issue in _array(prediction, "validation_issues")
                if isinstance(issue, Mapping) and issue.get("field") == "signals" and type(issue.get("index")) is int}
    return {raw_index: by_clause[clause][0] for raw_index, clause in enumerate(source_clauses)
            if type(clause) is int and uses[clause] == 1 and len(by_clause[clause]) == 1 and raw_index not in rejected}


def _valid_receipt(row):
    status, index, reason = row["status"], row["signal_index"], row["reason"]
    if status == "signal":
        return type(index) is int and reason is None
    return status in ("context", "needs_review") and index is None and _nonblank(reason)


def _receipts(dispositions, inventory, reactions, issues):
    if not isinstance(dispositions, list):
        issues.append({"code": "invalid_dispositions"})
        return {}
    known = {item["reaction_id"] for item in inventory}
    by_reaction = defaultdict(list)
    for index, row in enumerate(dispositions):
        rid = row.get("reaction_id") if isinstance(row, Mapping) else None
        if not isinstance(rid, str) or rid not in known:
            issues.append({"code": "unknown_reaction_id", "disposition_index": index, "reaction_id": rid})
        elif rid not in reactions:
            issues.append({"code": "non_preference_disposition", "disposition_index": index, "reaction_id": rid})
        else:
            by_reaction[rid].append(row)
    receipts = {}
    for rid, rows in by_reaction.items():
        if len(rows) != 1:
            issues.append({"code": "duplicate_disposition", "reaction_id": rid})
        elif rows[0].keys() != _RECEIPT_FIELDS or not _valid_receipt(rows[0]):
            issues.append({"code": "invalid_disposition", "reaction_id": rid})
        else:
            receipts[rid] = rows[0]
    return receipts


def audit_reactions(feedback_text, inventory, proposal, prediction, dispositions=None):
    """Account for preliminary preferences without changing the classifier's result.

    Saved responses without receipts can establish uniquely linked signals from
    their evidence. Live receipts additionally establish declared context or review
    decisions. Both preserve failed and disputed reactions for human review.
    """
    if not isinstance(inventory, list) or any(not isinstance(item, Mapping) for item in inventory):
        raise ValueError("Expected identified verified statements.")
    original = [{key: value for key, value in item.items() if key != "reaction_id"} for item in inventory]
    if inventory != identify_reactions(feedback_text, original):
        raise ValueError("Identified statements do not match the original feedback revision.")
    reactions = {item["reaction_id"]: item for item in inventory if item["role"] == "preference"}
    revision = sha256(feedback_text.encode()).hexdigest()
    raw_links, source_clauses, raw_spans = _raw_links(feedback_text, revision, reactions, proposal)
    accepted = _accepted_links(source_clauses, raw_spans, prediction)
    issues = []
    indices = defaultdict(list)
    if dispositions is None:
        for index, candidates in raw_links.items():
            for rid in candidates:
                indices[rid].append(index)
        receipts = {rid: {"status": "signal", "signal_index": matches[0], "reason": None}
                    for rid, matches in indices.items() if len(matches) == 1}
    else:
        receipts = _receipts(dispositions, inventory, reactions, issues)
    claims = Counter(row["signal_index"] for row in receipts.values() if row["status"] == "signal")
    rows, linked_raw, linked_validated = [], set(), set()
    for rid, reaction in reactions.items():
        receipt = receipts.get(rid)
        row = {**reaction, "status": "needs_review", "signal_index": None, "validated_signal_index": None,
               "reason": None, "flagged": True}
        if receipt is None:
            code = "missing_disposition"
            if dispositions is None:
                code = "ambiguous_signal_link" if indices.get(rid) else "omitted_reaction"
            row["reason"] = "The classifier output has no unique preference signal for this reaction."
            issues.append({"code": code, "reaction_id": rid})
        elif receipt["status"] != "signal":
            row.update(status=receipt["status"], reason=receipt["reason"])
        else:
            index = receipt["signal_index"]
            row["signal_index"] = index
            if index not in raw_links:
                code = "invalid_signal_index"
            elif claims[index] != 1 or len(raw_links[index]) > 1:
                code = "ambiguous_signal_link"
            elif raw_links[index] != [rid]:
                code = "signal_anchor_mismatch"
            else:
                linked_raw.add(index)
                code = None if index in accepted else "signal_rejected"
            if code is None:
                final_index = accepted[index]
                linked_validated.add(final_index)
                row.update(status="signal", reason=receipt["reason"], validated_signal_index=final_index, flagged=False)
            else:
                row["reason"] = "The claimed link does not identify one grounded and validated preference signal."
                issues.append({"code": code, "reaction_id": rid, "signal_index": index})
        rows.append(row)
    issues.extend({"code": "unaccounted_raw_signal", "signal_index": index}
                  for index in raw_links if index not in linked_raw)
    issues.extend({"code": "unaccounted_validated_signal", "validated_signal_index": index}
                  for index in range(len(_array(prediction, "interpretations"))) if index not in linked_validated)
    return {"reactions": rows, "issues": issues}
