"""Persistence operations with conservative canonical-job linking."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Job, SearchRun, SourceListing, SourceRun, utc_now
from .normalization import (
    canonical_url, clean_description, digest_text, listing_external_key,
    normalize_text,
)
from .schemas import IngestOutcome, RawJob


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, item: RawJob, seen_at: datetime | None = None) -> IngestOutcome:
        now = seen_at or utc_now()
        source_key = item.source_key
        external_key = listing_external_key(item.external_id, item.url)
        existing_listing = self.session.scalar(
            select(SourceListing).where(
                SourceListing.source_key == source_key,
                SourceListing.external_key == external_key,
            )
        )
        description = clean_description(item.description)
        description_hash = digest_text(description)
        employer_key = normalize_text(item.employer)
        title_key = normalize_text(item.title)
        location_key = normalize_text(item.location)

        if existing_listing is not None:
            job = self.session.get(Job, existing_listing.job_id)
            if job is None:
                raise RuntimeError("Listing references missing canonical job")
            existing_listing.last_seen_at = now
            existing_listing.url = canonical_url(item.url)
            existing_listing.source_payload = item.source_payload
            self._refresh_job(job, item, description, description_hash, now)
            self.session.flush()
            return IngestOutcome(
                job_id=job.id, is_new_job=False, is_new_listing=False,
                match_reason="same_source_identity",
            )

        candidate: Job | None = None
        reason = "new_canonical_job"
        # Requisition ID alone can be reused: require employer AND title,
        # and require an existing listing from another source.
        if item.requisition_id:
            candidate = self.session.scalar(
                select(Job)
                .join(SourceListing, SourceListing.job_id == Job.id)
                .where(
                    SourceListing.source_key != source_key,
                    SourceListing.requisition_id == item.requisition_id,
                    Job.employer_key == employer_key,
                    Job.title_key == title_key,
                    Job.location_key == location_key,
                )
                .limit(1)
            )
            if candidate is not None:
                reason = "cross_source_requisition"

        # Only identical, substantial cleaned descriptions are auto-linked.
        # A title and location match without matching content is insufficient.
        if candidate is None and len(description) >= 120:
            candidate = self.session.scalar(
                select(Job)
                .join(SourceListing, SourceListing.job_id == Job.id)
                .where(
                    SourceListing.source_key != source_key,
                    Job.employer_key == employer_key,
                    Job.title_key == title_key,
                    Job.location_key == location_key,
                    Job.description_hash == description_hash,
                )
                .limit(1)
            )
            if candidate is not None:
                reason = "cross_source_content_fingerprint"

        is_new_job = candidate is None
        if candidate is None:
            candidate = Job(
                employer=item.employer.strip(), employer_key=employer_key,
                title=item.title.strip(), title_key=title_key,
                location=item.location, location_key=location_key,
                description_text=description, description_hash=description_hash,
                employment_type=item.employment_type,
                work_arrangement=item.work_arrangement,
                salary_min=item.salary_min, salary_max=item.salary_max,
                salary_period=item.salary_period,
                salary_is_estimate=item.salary_is_estimate,
                first_seen_at=now, last_seen_at=now,
            )
            self.session.add(candidate)
            self.session.flush()
        else:
            self._refresh_job(candidate, item, description, description_hash, now)

        self.session.add(SourceListing(
            job_id=candidate.id, source_key=source_key,
            external_key=external_key, external_id=item.external_id,
            requisition_id=item.requisition_id,
            url=canonical_url(item.url), source_payload=item.source_payload,
            first_seen_at=now, last_seen_at=now,
        ))
        self.session.flush()
        return IngestOutcome(
            job_id=candidate.id, is_new_job=is_new_job, is_new_listing=True,
            match_reason=reason,
        )

    @staticmethod
    def _refresh_job(
        job: Job, item: RawJob, cleaned: str, description_hash: str, now: datetime,
    ) -> None:
        job.last_seen_at = now
        # Never overwrite richer existing job content with an aggregator snippet.
        if len(cleaned) > len(job.description_text):
            job.description_text = cleaned
            job.description_hash = description_hash
        for attr in ("employment_type", "work_arrangement", "salary_min", "salary_max", "salary_period"):
            if getattr(job, attr) is None and getattr(item, attr) is not None:
                setattr(job, attr, getattr(item, attr))


class RunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ensure_run(self, logical_date: str) -> SearchRun:
        run = self.session.scalar(
            select(SearchRun).where(SearchRun.logical_date == logical_date)
        )
        if run is None:
            run = SearchRun(logical_date=logical_date, status="RUNNING")
            self.session.add(run)
            self.session.flush()
        return run

    def record_source(
        self,
        run: SearchRun,
        source_key: str,
        status: str,
        observed: int = 0,
        new_jobs: int = 0,
        new_listings: int = 0,
        error_code: str | None = None,
    ) -> None:
        row = self.session.scalar(select(SourceRun).where(
            SourceRun.search_run_id == run.id,
            SourceRun.source_key == source_key,
        ))
        if row is None:
            row = SourceRun(search_run_id=run.id, source_key=source_key, status=status)
            self.session.add(row)
        row.status = status
        row.observed = observed
        row.new_jobs = new_jobs
        row.new_listings = new_listings
        row.error_code = error_code
        row.completed_at = utc_now()
