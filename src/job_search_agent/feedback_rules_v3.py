"""Derive advisory rule findings from confirmed policy and structured job facts."""

import math
import re


_PAY_RULES = {
    "permanent": ("permanent_base_minimum_usd", "base_salary_usd", "annual base", "per year"),
    "w2_contract": ("w2_hourly_minimum_usd", "hourly_rate_usd", "W-2 rate", "per hour"),
    "1099_contract": ("1099_hourly_minimum_usd", "hourly_rate_usd", "1099 rate", "per hour"),
    "c2c_contract": ("c2c_hourly_minimum_usd", "hourly_rate_usd", "C2C rate", "per hour"),
}
_EMPLOYMENT_TYPES = {
    "permanent": "permanent", "full_time": "permanent", "w2": "w2_contract", "w2_contract": "w2_contract",
    "1099": "1099_contract", "1099_contract": "1099_contract", "c2c": "c2c_contract", "c2c_contract": "c2c_contract",
}
_RATE_TYPES = {"w2": "w2_contract", "1099": "1099_contract", "c2c": "c2c_contract"}

# Recognize the confirmed commute policy currently supplied by the v2 fixtures.
# An arbitrary prose rule could describe different thresholds or exceptions.
CONFIRMED_COMMUTE_RULES = (
    "Within 10 driving miles: onsite acceptable.",
    "Greater than 10 and less than 30 driving miles: Mondays and Fridays must be remote. "
    "Unknown days require verification.",
    "At least 30 driving miles: regular work must be fully remote. "
    "Occasional visits or business trips are allowed.",
)
_FULL_ONSITE = {"onsite", "on_site", "fully_onsite", "fully_on_site"}
_KNOWN_REGULAR_HYBRID = re.compile(r"hybrid_[1-5]_on_?site")
_ONSITE_WEEKDAYS = re.compile(r"(?:hybrid_)?on_?site_([a-z_]+)")
_WEEKDAYS = {
    "mon": "Monday", "monday": "Monday", "tue": "Tuesday", "tuesday": "Tuesday",
    "wed": "Wednesday", "wednesday": "Wednesday", "thu": "Thursday", "thursday": "Thursday",
    "fri": "Friday", "friday": "Friday",
}

_REQUEST = re.compile(
    r"(?:^|[.;!?]\s+)(?:please\s+|i\s+(?:want|would like|am asking)\s+to\s+|"
    r"(?:can|could|would)\s+(?:we|you)\s+(?:please\s+)?)"
    r"(?:reconsider|revisit|review|change|adjust|revise|lower|raise|increase|reduce|remove|relax|waive)\s+"
    r"(?P<target>[^.;!?]+)",
    re.IGNORECASE,
)
_TARGET_PREFIX = r"(?:(?:my|our|the|this|current|confirmed|existing|established)\s+)*"
_W2 = r"w[ -]?2"
_PERMANENT = r"permanent|full[ -]time|annual base|base salary|base pay"
_C2C = r"c2c|corp[ -]to[ -]corp"
_PAY_TARGET = re.compile(
    _TARGET_PREFIX + rf"(?:(?:{_W2}|1099|{_C2C}|{_PERMANENT}|pay|salary|compensation|hourly rate)\s+)?"
    r"(?:minimum(?:\s+(?:pay|salary|rate))?|floor)\b(?=\s*(?:$|,|(?:to|from|for|now|temporarily|altogether)\b))",
    re.IGNORECASE,
)
_PAY_TARGET_FOR = re.compile(r"\s+for\s+(.*?)(?=\s+(?:to|from|now)\b|,|$)", re.IGNORECASE)
_PAY_TARGET_TYPES = {
    "permanent": re.compile(rf"\b(?:{_PERMANENT})\b", re.IGNORECASE),
    "w2_contract": re.compile(rf"\b{_W2}\b", re.IGNORECASE),
    "1099_contract": re.compile(r"\b1099\b"),
    "c2c_contract": re.compile(rf"\b(?:{_C2C})\b", re.IGNORECASE),
}
_COMMUTE_TARGET = re.compile(
    _TARGET_PREFIX + r"(?:commuting?|commute|distance|location|on[ -]?site|remote work|hybrid work)\s+"
    r"(?:rule|limit|requirement|threshold)\b",
    re.IGNORECASE,
)


def _normalize(value):
    return re.sub(r"[\s-]+", "_", value.strip().casefold()) if isinstance(value, str) else ""


def _nonnegative_number(value):
    return (type(value) is int and value >= 0) or (type(value) is float and math.isfinite(value) and value >= 0)


def _compensation_violation(context, rules):
    employment = _EMPLOYMENT_TYPES.get(_normalize(context.get("employment_type")))
    rate_type = _RATE_TYPES.get(_normalize(context.get("rate_type")).replace("_", ""))
    if not employment or (rate_type and rate_type != employment):
        return None
    rule_key, context_key, description, unit = _PAY_RULES[employment]
    floor, amount = rules.get(rule_key), context.get(context_key)
    if _nonnegative_number(floor) and _nonnegative_number(amount) and amount < floor:
        return f"The confirmed {description} of ${amount:,} {unit} is below the ${floor:,} {unit} minimum."
    return None


def _confirmed_commute_policy(rules):
    supplied = rules.get("commute_rules")
    if not isinstance(supplied, (list, tuple)) or not all(isinstance(line, str) for line in supplied):
        return False
    return sorted(" ".join(line.split()) for line in supplied) == sorted(CONFIRMED_COMMUTE_RULES)


def _required_onsite_days(arrangement):
    if arrangement in _FULL_ONSITE:
        return set(_WEEKDAYS.values())
    encoded = _ONSITE_WEEKDAYS.fullmatch(arrangement)
    if not encoded:
        return set()
    requested_days = encoded.group(1).split("_")
    if not all(day in _WEEKDAYS for day in requested_days):
        return set()
    return {_WEEKDAYS[day] for day in requested_days}


def _commute_violation(context, rules):
    distance = context.get("distance_miles")
    if not _confirmed_commute_policy(rules) or not _nonnegative_number(distance) or distance <= 10:
        return None
    arrangement = _normalize(context.get("arrangement"))
    onsite_days = _required_onsite_days(arrangement)
    if distance >= 30 and (onsite_days or _KNOWN_REGULAR_HYBRID.fullmatch(arrangement)):
        return f"Regular onsite attendance at {distance:,} driving miles conflicts with the confirmed remote-work rule."
    conflicting_days = [day for day in ("Monday", "Friday") if day in onsite_days]
    if 10 < distance < 30 and conflicting_days:
        days = " and ".join(conflicting_days)
        return f"Required onsite attendance on {days} at {distance:,} driving miles conflicts with the confirmed commute rule."
    return None


def eligibility_violation(context, rules):
    """Describe proven conflicts with the supplied rules, or return None."""
    findings = (_compensation_violation(context, rules), _commute_violation(context, rules))
    return " ".join(finding for finding in findings if finding) or None


def rule_reconsideration_supported(quote, rules):
    """Recognize explicit requests to reconsider a supplied, confirmed rule."""
    active_pay_rules = {kind for kind, (key, *_) in _PAY_RULES.items() if _nonnegative_number(rules.get(key))}
    for request in _REQUEST.finditer(quote.strip()):
        target = request.group("target").strip()
        if _COMMUTE_TARGET.match(target) and _confirmed_commute_policy(rules):
            return True
        pay_target = _PAY_TARGET.match(target)
        if not pay_target or not active_pay_rules:
            continue
        pay_scope = pay_target.group()
        qualifier = _PAY_TARGET_FOR.match(target, pay_target.end())
        if qualifier:
            pay_scope += " " + qualifier.group(1)
        specific_types = {kind for kind, pattern in _PAY_TARGET_TYPES.items() if pattern.search(pay_scope)}
        if not specific_types or active_pay_rules & specific_types:
            return True
    return False
