"""Validate evidence-backed feedback proposals and compute their review route."""

import argparse
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
import sys

from .feedback import (
    NEEDS_CLARIFICATION,
    PENDING_APPROVAL,
    POLARITIES,
    PROFILE_FACT_REVIEW,
    REPORT_ELIGIBILITY_VIOLATION,
    REQUIRE_RULE_CONFIRMATION,
    STRENGTHS,
    UNCHANGED,
    FeedbackInputError,
    FeedbackOutputError,
    FeedbackProviderError,
    _json_context,
    _nonblank,
)
from .feedback_extraction_v3 import (
    CLAUSE_ROLES,
    CONDITION_KINDS,
    DIMENSION_SCOPES,
    PROMPT_VERSION,
    QUALIFIER_KINDS,
    OpenAIFeedbackProviderV3,
)
from .feedback_rules_v3 import eligibility_violation, rule_reconsideration_supported
from .feedback_taxonomy import _VOCABULARY, canonicalize_signal


_CONTEXT_QUALIFIERS = {
    "amount": {"base_salary_usd", "hourly_rate_usd"},
    "employment_type": {"employment_type", "rate_type"},
    "work_mode": {"arrangement"},
    "distance": {"distance_miles"},
    "location": {"location"},
    "schedule": {"onsite_days", "arrangement"},
}
_REACTION = re.compile(
    r"\b(?:like|love|enjoy|prefer|appeals?|value|want|would avoid|would pass|"
    r"excites?|attractive|unattractive|dislike|hate|resonates?|worthwhile|"
    r"looks? (?:good|great|excellent)|sounds? (?:good|great|excellent))\b",
    re.IGNORECASE,
)
_CAREER_SCOPE = re.compile(r"\b(?:careers?|roles?|positions?|profession|line of work)\b", re.IGNORECASE)
_NEGATIVE_REACTION = re.compile(
    r"\b(?:not|never|don['’]t|avoid|no longer|dislike|reject|hate)\b", re.IGNORECASE,
)
_NUMBER = re.compile(r"(?<![\d.])[-+]?\d+(?:,\d{3})*(?:\.\d+)?(?!\d)")
_DISTANCE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*-?\s*(?:driving\s+)?(mi(?:les?)?|km|kilometers?)\b",
    re.IGNORECASE,
)
_REGISTERED = {
    (dimension, scope_type, feature_id, scope_id)
    for (dimension, scope_type), rows in _VOCABULARY.items()
    for feature_id, _, scope_id, _ in rows
}
_PROJECT_LABELS = {
    "core banking replacement", "core banking replacement transformation",
    "core banking system replacement", "core banking replacement projects",
}
_EMPLOYMENT_TYPES = {
    "c2c": "c2c", "c2c contract": "c2c", "corp to corp": "c2c",
    "w2": "w2", "w 2": "w2", "w2 contract": "w2", "w 2 contract": "w2",
    "1099": "1099", "1099 contract": "1099",
    "permanent": "permanent", "full time": "permanent",
}


def _label_key(value):
    return " ".join(re.sub(r"[_-]", " ", value.casefold()).split())


def _number(value):
    try:
        number = Decimal(str(value).replace(",", ""))
    except InvalidOperation:
        return None
    return number if number.is_finite() and number >= 0 else None


def _distance_value(value, quote, context):
    stated = _DISTANCE.fullmatch(value.strip())
    number = _number(stated[1] if stated else value)
    if number is None:
        raise FeedbackOutputError("Distance qualifier must state a nonnegative distance.")
    anchors = [(match[1], "miles" if match[2].lower().startswith("mi") else "km")
               for match in _DISTANCE.finditer(quote)]
    known_miles = _number(context.get("distance_miles"))
    if quote == "distance_miles" or (known_miles == number and not anchors
                                     and re.search(r"\bmiles?\b", quote, re.IGNORECASE)):
        anchors.append((str(known_miles), "miles"))
    unit = ("miles" if stated[2].lower().startswith("mi") else "km") if stated else None
    for amount, anchored_unit in anchors:
        if _number(amount) == number and unit in (None, anchored_unit):
            return f"{number:f} {anchored_unit}"
    raise FeedbackOutputError("Distance qualifier must match its evidence, including the unit.")


def _object(value, fields, description):
    if not isinstance(value, Mapping) or value.keys() != fields:
        raise FeedbackOutputError(f"Invalid {description} fields.")
    return value


def _span(feedback, quote, role, revision, within=None):
    if not _nonblank(quote):
        raise FeedbackOutputError("Evidence requires a verbatim feedback quote.")
    lower, upper = (within["start"], within["end"]) if within else (0, len(feedback))
    start = feedback.find(quote, lower, upper)
    if start < 0 or feedback.find(quote, start + 1, upper) >= 0:
        raise FeedbackOutputError("Evidence quote must locate a unique original feedback span.")
    return {"origin": "feedback", "role": role, "source_revision": revision,
            "start": start, "end": start + len(quote), "quote": quote}


def _clause(raw, feedback, revision):
    _object(raw, {"role", "quote", "detail"}, "clause")
    role, quote, detail = raw["role"], raw["quote"], raw["detail"]
    if role not in CLAUSE_ROLES or (detail is not None and not _nonblank(detail)):
        raise FeedbackOutputError("Invalid clause role or detail.")
    return {"role": role, "detail": detail, "evidence": _span(feedback, quote, role, revision)}


def _qualifier(raw, feedback, revision, assertion, context):
    _object(raw, {"kind", "value", "source", "quote"}, "qualifier")
    kind, value, source, quote = (raw[key] for key in ("kind", "value", "source", "quote"))
    if kind not in QUALIFIER_KINDS or not _nonblank(value) or not _nonblank(quote):
        raise FeedbackOutputError("Invalid qualifier kind, value, or evidence.")
    if source == "feedback":
        evidence = _span(feedback, quote, "qualifier", revision, within=assertion)
        if kind == "amount":
            number = _number(value)
            if number is None or all(_number(match) != number for match in _NUMBER.findall(quote)):
                raise FeedbackOutputError("Numeric qualifier must match its feedback evidence.")
    elif source == "job_context" and quote in _CONTEXT_QUALIFIERS.get(kind, set()):
        known = context.get(quote)
        if isinstance(known, bool) or not isinstance(known, (int, float, str)):
            raise FeedbackOutputError("Qualifier names an unavailable structured posting field.")
        known_key, value_key = _label_key(str(known)), _label_key(value)
        if kind == "employment_type":
            known_key = _EMPLOYMENT_TYPES.get(known_key, known_key)
            value_key = _EMPLOYMENT_TYPES.get(value_key, value_key)
        if kind == "amount":
            known_key, value_key = _number(known), _number(value)
        if kind != "distance" and (known_key is None or known_key != value_key):
            raise FeedbackOutputError("Qualifier disagrees with structured posting evidence.")
        evidence = {"origin": "job_context", "role": "context_only", "key": quote, "value": known}
    else:
        raise FeedbackOutputError("Qualifier source must be feedback or a matching structured posting field.")
    normalized = _distance_value(value, quote, context) if kind == "distance" else value.strip()
    return dict(raw, value=normalized, evidence=evidence)


def _condition(raw, feedback, revision, assertion):
    if raw is None:
        return None
    _object(raw, {"kind", "value", "quote"}, "condition")
    if raw["kind"] not in CONDITION_KINDS or not _nonblank(raw["value"]):
        raise FeedbackOutputError("Condition must be supported within its preference clause.")
    evidence = _span(feedback, raw["quote"], "condition", revision, within=assertion)
    return dict(raw, value=raw["value"].strip(), evidence=evidence)


def _feature_id(dimension, label, scope, polarity):
    scope_type, referent = scope["type"], scope["referent"]
    if scope_type == "project_type" and _label_key(referent) in _PROJECT_LABELS:
        return "role.core_banking_replacement_project"
    qualifiers = {item["kind"]: item["value"] for item in scope["qualifiers"]}
    if (dimension == "compensation" and scope_type == "compensation_context"
            and {"amount", "currency", "compensation_unit", "employment_type"} <= qualifiers.keys()):
        return "compensation.quoted_rate"
    canonical = canonicalize_signal({
        "dimension": dimension, "feature": label, "polarity": polarity,
        "scope": {"type": scope_type, "value": referent},
    })
    registered = (dimension, scope_type, canonical.feature_id, canonical.scope_id)
    if registered not in _REGISTERED or registered == (
        "career_category", "career_category", "core_banking_replacement", "core_banking_replacement",
    ):
        return None
    namespace = {"career_category": "career", "role_responsibilities": "role"}.get(dimension, dimension)
    return f"{namespace}.{canonical.feature_id}"


def _signal(raw, clauses, feedback, revision, context, violation):
    _object(raw, {"clause_index", "dimension", "display_label", "polarity", "strength", "scope", "condition"},
            "signal")
    index = raw["clause_index"]
    if type(index) is not int or not 0 <= index < len(clauses):
        raise FeedbackOutputError("Signal must identify its preference clause.")
    clause = clauses[index]
    if clause is None or clause["role"] != "preference":
        raise FeedbackOutputError("Signal must cite a validated preference clause.")

    label, dimension = raw["display_label"], raw["dimension"]
    polarity, strength = raw["polarity"], raw["strength"]
    scope = _object(raw["scope"], {"type", "referent", "qualifiers"}, "scope")
    if (not _nonblank(label) or not isinstance(dimension, str) or dimension not in DIMENSION_SCOPES
            or scope["type"] not in DIMENSION_SCOPES[dimension] or not _nonblank(scope["referent"])
            or not isinstance(scope["qualifiers"], list) or polarity not in POLARITIES or strength not in STRENGTHS):
        raise FeedbackOutputError("Invalid signal label, dimension, scope, polarity, or strength.")

    assertion = clause["evidence"]
    if violation and not _REACTION.search(assertion["quote"]):
        raise FeedbackOutputError("An eligibility violation alone cannot support a preference.")
    qualifiers = [_qualifier(item, feedback, revision, assertion, context) for item in scope["qualifiers"]]
    qualifier_kinds = [item["kind"] for item in qualifiers]
    if len(qualifier_kinds) != len(set(qualifier_kinds)):
        raise FeedbackOutputError("A scope cannot repeat a qualifier kind.")
    scope = {"type": scope["type"], "referent": scope["referent"].strip(), "qualifiers": qualifiers}
    label = label.strip()
    condition = _condition(raw["condition"], feedback, revision, assertion)
    feature_id = _feature_id(dimension, label, scope, polarity)
    career_review = dimension == "career_category" and polarity == "negative"
    career_scope_cue = bool(_CAREER_SCOPE.search(assertion["quote"]) and _NEGATIVE_REACTION.search(assertion["quote"]))
    return {
        "clause_index": index, "dimension": dimension, "display_label": label, "feature_id": feature_id,
        "identity_status": "registered" if feature_id else "candidate",
        "scope": scope, "polarity": polarity, "strength": strength, "condition": condition,
        "evidence": [clause["evidence"], *[item["evidence"] for item in qualifiers],
                     *([condition["evidence"]] if condition else [])],
        "application_status": "held_for_review",
        "career_evidence_review": ("explicit_scope_cue" if career_scope_cue else "needs_support_review")
        if career_review else None,
    }


def _validated_proposal(raw, feedback, context, violation):
    _object(raw, {"clauses", "signals"}, "extraction proposal")
    if not isinstance(raw["clauses"], list) or not isinstance(raw["signals"], list):
        raise FeedbackOutputError("Clauses and signals must be arrays.")
    revision = sha256(feedback.encode()).hexdigest()
    clauses, signals, issues = [], [], []
    for index, clause in enumerate(raw["clauses"]):
        try:
            clauses.append(dict(_clause(clause, feedback, revision), index=index))
        except FeedbackOutputError as error:
            clauses.append(None)
            issues.append({"field": "clauses", "index": index, "message": str(error)})

    used_clauses, used_evidence, identities = set(), set(), set()
    for index, item in enumerate(raw["signals"]):
        try:
            signal = _signal(item, clauses, feedback, revision, context, violation)
            clause_index = signal["clause_index"]
            quote = clauses[clause_index]["evidence"]["quote"]
            if clause_index in used_clauses or quote in used_evidence:
                raise FeedbackOutputError("A single preference assertion may support only one signal.")
            scope = signal["scope"]
            condition = signal["condition"]
            key = (
                signal["dimension"], signal["feature_id"] or _label_key(signal["display_label"]),
                scope["type"], _label_key(scope["referent"]), signal["polarity"],
                tuple(sorted((q["kind"], _label_key(q["value"])) for q in scope["qualifiers"])),
                (condition["kind"], _label_key(condition["value"])) if condition else None,
            )
            if key in identities:
                raise FeedbackOutputError("Duplicate preference signal.")
        except FeedbackOutputError as error:
            issues.append({"field": "signals", "index": index, "message": str(error)})
        else:
            used_clauses.add(clause_index)
            used_evidence.add(quote)
            identities.add(key)
            signals.append((index, signal))

    condition_spans = [(index, signal["condition"]["evidence"])
                       for index, signal in signals if signal["condition"]]
    independent = []
    for index, signal in signals:
        assertion = signal["evidence"][0]
        if any(
            parent != index and condition["start"] <= assertion["start"] and assertion["end"] <= condition["end"]
            for parent, condition in condition_spans
        ):
            issues.append({"field": "signals", "index": index,
                           "message": "A condition cannot also be emitted as an independent preference."})
        else:
            independent.append(signal)
    return [clause for clause in clauses if clause is not None], independent, issues


def _review(clauses, signals, violation, rules):
    by_role = {role: [clause for clause in clauses if clause["role"] == role]
               for role in ("rule_reconsideration", "profile_fact", "vague_reaction")}
    reconsiderations = by_role["rule_reconsideration"]
    requests = [clause for clause in reconsiderations
                if rule_reconsideration_supported(clause["evidence"]["quote"], rules)]
    action = (REQUIRE_RULE_CONFIRMATION if requests else REPORT_ELIGIBILITY_VIOLATION if violation else UNCHANGED)

    if requests or by_role["profile_fact"]:
        facts = [*requests, *by_role["profile_fact"]]
        # A tentative pay exception can be extracted separately from the rule request.
        if requests:
            facts.extend(clause for clause in clauses if clause["role"] == "context"
                         and "$" in clause["evidence"]["quote"]
                         and re.search(r"\b(?:if|unless|provided)\b", clause["evidence"]["quote"], re.IGNORECASE))
        summary = " ".join(clause["evidence"]["quote"] for clause in sorted(facts, key=lambda item: item["index"]))
        if violation:
            summary = f"{summary} {violation}"
        return PROFILE_FACT_REVIEW, action, None, summary
    if violation and not signals:
        return PROFILE_FACT_REVIEW, action, None, violation
    if by_role["vague_reaction"] or reconsiderations or not signals:
        vague = by_role["vague_reaction"]
        question = next((item["detail"] for item in vague if item["detail"]), None)
        question = question or "What specifically influenced your reaction to this opportunity?"
        return NEEDS_CLARIFICATION, action, question, None
    return PENDING_APPROVAL, action, None, None


def interpret_feedback_v3(decision, feedback, job_context=None, *, provider, hard_rules=None):
    """Return a read-only v3 interpretation, retaining validated review evidence."""
    decision = decision.strip().lower() if isinstance(decision, str) else ""
    if decision == "rejected_archived":
        decision = "rejected"
    if decision not in {"interested", "rejected"}:
        raise FeedbackInputError("Decision must be Interested or Rejected.")
    if not _nonblank(feedback):
        raise FeedbackInputError("Feedback must contain a written reason.")
    context = _json_context(job_context, "Job context")
    rules = _json_context(hard_rules, "Hard rules")
    violation = eligibility_violation(context, rules)
    raw = provider.propose(decision, feedback, context, rules)
    clauses, signals, issues = _validated_proposal(raw, feedback, context, violation)
    review_status, action, question, fact = _review(clauses, signals, violation, rules)
    return {
        "decision": decision, "original_feedback": feedback, "model": provider.model,
        "prompt_version": PROMPT_VERSION, "clauses": clauses, "interpretations": signals,
        "review_status": review_status, "clarification_question": question, "profile_fact_candidate": fact,
        "hard_constraint_action": action, "hard_constraints_mutated": False,
        "eligibility_violation": violation, "validation_issues": issues,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", help="OpenAI model, defaults to OPENAI_FEEDBACK_MODEL")
    parser.add_argument("--temperature", type=float)
    args = parser.parse_args(argv)
    try:
        try:
            data = json.load(sys.stdin)
        except ValueError:
            raise FeedbackInputError("Provide valid JSON on stdin.") from None
        if not isinstance(data, dict) or data.keys() - {"decision", "feedback", "job_context", "hard_rules"}:
            raise FeedbackInputError("Provide decision, feedback, and optional job_context and hard_rules.")
        provider = OpenAIFeedbackProviderV3(args.model, temperature=args.temperature)
        result = interpret_feedback_v3(
            data.get("decision"), data.get("feedback"), data.get("job_context"),
            provider=provider, hard_rules=data.get("hard_rules"),
        )
    except (FeedbackInputError, FeedbackProviderError) as error:
        print(error, file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
