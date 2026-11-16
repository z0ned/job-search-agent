"""Validated contracts used by source adapters and application services."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator


class EligibilityStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_CONFIGURED = "NOT_CONFIGURED"


class RawJob(BaseModel):
    source_key: str = Field(min_length=1)
    external_id: str | None = None
    employer: str = Field(min_length=1)
    title: str = Field(min_length=1)
    location: str | None = None
    description: str = ""
    url: str = Field(min_length=8)
    requisition_id: str | None = None
    employment_type: str | None = None
    work_arrangement: str | None = None
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    salary_period: str | None = None
    salary_is_estimate: bool = False
    published_at: datetime | None = None
    source_payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("url")
    @classmethod
    def check_url(cls, value: str) -> str:
        parts = urlsplit(value.strip())
        if parts.scheme.lower() not in {"https", "http"} or not parts.netloc:
            raise ValueError("Job URL must be an absolute http(s) URL")
        return value.strip()


class IngestOutcome(BaseModel):
    job_id: int
    is_new_job: bool
    is_new_listing: bool
    match_reason: str


class EligibilityDecision(BaseModel):
    status: EligibilityStatus
    reasons: list[str] = Field(default_factory=list)


class RunSummary(BaseModel):
    logical_date: str
    status: str
    source_statuses: dict[str, str]
    new_jobs: int
    new_listings: int
    observed: int
