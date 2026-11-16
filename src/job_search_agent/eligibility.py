"""Hard-rule evaluator. Unknown data never silently becomes a failure."""
from __future__ import annotations

from hashlib import sha256

from pydantic import BaseModel, Field

from .normalization import normalize_text
from .schemas import EligibilityDecision, EligibilityStatus, RawJob


class RuleSet(BaseModel):
    active: bool = False
    excluded_employers: list[str] = Field(default_factory=list)
    allowed_employment_types: list[str] = Field(default_factory=list)
    allowed_work_arrangements: list[str] = Field(default_factory=list)
    min_annual_salary: float | None = Field(default=None, ge=0)

    @property
    def fingerprint(self) -> str:
        return sha256(self.model_dump_json().encode("utf-8")).hexdigest()


def evaluate(item: RawJob, rules: RuleSet) -> EligibilityDecision:
    if not rules.active:
        return EligibilityDecision(
            status=EligibilityStatus.NOT_CONFIGURED,
            reasons=["No confirmed hard-eligibility rule set has been activated."],
        )

    fail: list[str] = []
    unknown: list[str] = []
    if normalize_text(item.employer) in {
        normalize_text(x) for x in rules.excluded_employers
    }:
        fail.append("Employer explicitly excluded.")

    def check_allowed(attr: str | None, allowed: list[str], label: str) -> None:
        if not allowed:
            return
        if not attr:
            unknown.append(f"{label} is missing.")
        elif normalize_text(attr) not in {normalize_text(x) for x in allowed}:
            fail.append(f"{label} is explicitly outside approved values.")

    check_allowed(item.employment_type, rules.allowed_employment_types, "Employment type")
    check_allowed(item.work_arrangement, rules.allowed_work_arrangements, "Work arrangement")

    if rules.min_annual_salary is not None:
        if item.salary_is_estimate or item.salary_period != "year":
            unknown.append("Verified annual compensation is unavailable.")
        elif item.salary_max is not None and item.salary_max < rules.min_annual_salary:
            fail.append("Verified upper salary bound is below required minimum.")
        elif item.salary_min is None or item.salary_min < rules.min_annual_salary:
            unknown.append("Salary range does not establish the required minimum.")

    if fail:
        return EligibilityDecision(status=EligibilityStatus.FAIL, reasons=fail + unknown)
    if unknown:
        return EligibilityDecision(status=EligibilityStatus.UNKNOWN, reasons=unknown)
    return EligibilityDecision(status=EligibilityStatus.PASS)
