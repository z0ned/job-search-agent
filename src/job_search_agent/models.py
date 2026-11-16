"""Sprint 1 SQLAlchemy persistence model; later sprints add their own migrations."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employer: Mapped[str] = mapped_column(String(250))
    employer_key: Mapped[str] = mapped_column(String(250), index=True)
    title: Mapped[str] = mapped_column(String(300))
    title_key: Mapped[str] = mapped_column(String(300), index=True)
    location: Mapped[str | None] = mapped_column(String(250))
    location_key: Mapped[str] = mapped_column(String(250))
    description_text: Mapped[str] = mapped_column(Text)
    description_hash: Mapped[str] = mapped_column(String(64))
    employment_type: Mapped[str | None] = mapped_column(String(80))
    work_arrangement: Mapped[str | None] = mapped_column(String(80))
    salary_min: Mapped[float | None]
    salary_max: Mapped[float | None]
    salary_period: Mapped[str | None] = mapped_column(String(40))
    salary_is_estimate: Mapped[bool] = mapped_column(default=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    lifecycle_state: Mapped[str] = mapped_column(String(32), default="ACTIVE")


Index(
    "ix_jobs_identity_fingerprint",
    Job.employer_key, Job.title_key, Job.location_key, Job.description_hash,
)


class SourceListing(Base):
    __tablename__ = "source_listings"
    __table_args__ = (
        UniqueConstraint("source_key", "external_key", name="uq_source_external_key"),
        Index("ix_listing_job_id", "job_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    source_key: Mapped[str] = mapped_column(String(200))
    external_key: Mapped[str] = mapped_column(String(800))
    external_id: Mapped[str | None] = mapped_column(String(250))
    requisition_id: Mapped[str | None] = mapped_column(String(250))
    url: Mapped[str] = mapped_column(Text)
    source_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SearchRun(Base):
    __tablename__ = "search_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    logical_date: Mapped[str] = mapped_column(String(10), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="RUNNING")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    observed: Mapped[int] = mapped_column(Integer, default=0)
    new_jobs: Mapped[int] = mapped_column(Integer, default=0)
    new_listings: Mapped[int] = mapped_column(Integer, default=0)


class SourceRun(Base):
    __tablename__ = "source_runs"
    __table_args__ = (UniqueConstraint("search_run_id", "source_key", name="uq_run_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    search_run_id: Mapped[int] = mapped_column(ForeignKey("search_runs.id"))
    source_key: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20))
    observed: Mapped[int] = mapped_column(Integer, default=0)
    new_jobs: Mapped[int] = mapped_column(Integer, default=0)
    new_listings: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(80))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EligibilityCheck(Base):
    __tablename__ = "eligibility_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    rules_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20))
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
