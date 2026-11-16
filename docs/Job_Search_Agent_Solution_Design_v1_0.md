# Job Search Agent — MVP Solution Architecture

**Version:** 1.0 (proposed)  
**Date:** November 16, 2026  
**Status:** Architecture proposal for review; no production implementation has started  
**Requirements baseline:** [Job Search Agent — MVP Requirements v1.1](./Job_Search_Agent_MVP_Requirements_v1_1.md)  
**Traceability:** Requirements FR-01 through FR-33; AT-01 through AT-10

> **Decision key:** CONFIRMED means carried forward from requirements v1.1; RECOMMENDED means an architectural choice presented for adoption; OPEN means a user decision or integration feasibility check is still required. This document does not silently promote recommended choices to approved requirements.

## 1. Executive Summary

Build a single-user, local-only job recommendation application composed of a Streamlit browser dashboard, modular Python services, a SQLite database, and an operating-system-scheduled command-line worker. The worker fetches jobs from a small set of approved sources, canonicalizes and deduplicates them, applies explicit eligibility constraints, requests structured AI assessments, ranks qualifying roles, saves all qualifying jobs, and sends a short daily email containing only top-ranked newly found jobs. The dashboard handles job review, free-form reasons, the separate learning approval queue, a Career Opportunity Map, a weekly blind audit, and recommendation-quality monitoring.

The top architectural priority is **correct recommendations with protected learning**, rather than technology sophistication. Use a deterministic policy boundary around AI: an AI model may evaluate jobs and propose preferences, but it may not silently change hard eligibility rules or activate preference changes without approved feedback and phase permission.

**Recommended MVP technology:** Python 3.12+, Streamlit, Pydantic, SQLAlchemy 2, Alembic, SQLite, httpx, OpenAI API, Gmail API, OS Task Scheduler / systemd timer or cron. Choose a supported OpenAI model via configuration rather than hardcoding a model name. Use a local virtual environment; containers are unnecessary for the single-computer MVP.

**MVP scope boundary:** No application tracking, interview handling, application submission, candidate outreach, or cloud-hosted dashboard.

## 2. Requirements Basis, Assumptions, and Open Decisions

### 2.1 Confirmed behavior (source: requirements v1.1)

- Home-computer deployment and local browser dashboard only; automatic daily search; multiple job sources; deduplication and historical suppression of previously seen jobs.
- Hard eligibility screening; comprehensive AI job assessment; all qualifying jobs stored; only selected top new jobs emailed.
- Unreviewed, Interested, Rejected/Archived states. Interested means **“I would seriously consider applying for this job.”**
- Required original free-form explanation for both Interested and Rejected. AI interpretation is proposed, corrected or clarified in a later **batch approval** queue. Unapproved interpretations may not influence preferences.
- Rejecting one employer, salary, work arrangement, or seniority level must not automatically reduce interest in an entire career category.
- Career Opportunity Map tracks category, interest, career fit, confidence, market opportunity, and trend.
- Weekly audit: five randomly sampled lower-ranked eligible jobs; blind assessment display until all five are reviewed; audit jobs excluded from ordinary recommendation precision.
- Initial 50 ordinary reviewed recommendations with learning frozen; one activation of approved baseline learning; next 50 reviewed with learning frozen; success threshold is +10 percentage points. Following that, rolling 50-job measurement and approved continuous learning.
- If the initial improvement is inadequate: investigate before enabling continuous learning; after approved corrections, resume ongoing learning without a further controlled 50-job phase. If subsequent quality declines beyond a threshold, pause learning but keep discovery and recommendations running.

### 2.2 Architectural assumptions (RECOMMENDED, not yet approved)

- One local user and one SQLite database; no user accounts or remote login.
- Two initial source adapters, one broad-search provider plus one direct employer-board provider; expand sources after validation.
- Only high-confidence duplicate matches are merged automatically; ambiguous matches remain separate and are flagged.
- One scheduled discovery pipeline and one scheduled weekly-audit assembly command; the Streamlit UI does not run a permanent background scheduler.
- AI uses structured schema-constrained responses and supports UNKNOWN fields, evidence excerpts, and explicit uncertainty.
- User-visible recommendation cohorts are committed before feedback; frozen original scores are never recomputed in place.
- Audit batches must reach five eligible candidates to be launched; incomplete audits retain progress across sessions.
- Zero known hard-criteria violations is a design quality target, not a guarantee of perfect extraction from incomplete postings.

### 2.3 OPEN decisions (do not silently default)

Exact eligibility rules, career categories, compensation floor, remote/geographic/travel restrictions, employment types; employer and source priorities; provider credentials and commercial terms; daily schedule and missed-run policy; digest size; lifecycle/repost policy; score weights and minimum ranking threshold; proposed 80/20 exploration allocation; approval queue treatment of discarded proposals; low-supply audit handling; local email links; and the rolling-precision degradation threshold and reference benchmark.

## 3. Functional Design and Use Cases

| Use case | Actor / trigger | Result | Key requirements |
|---|---|---|---|
| UC-01 Scheduled job discovery | OS scheduler | Source runs, canonical jobs, eligibility and ranked assessments, stored results | FR-01–06 |
| UC-02 Deliver daily shortlist | Completed discovery run | Digest of newly discovered top-ranked jobs only | FR-07–08 |
| UC-03 Review job | User | Interested or Rejected decision with required comment, independently of AI approval | FR-09–11,16–17 |
| UC-04 Approve AI learning | User | Corrections/clarifications followed by one reviewed bulk approval action | FR-18–23 |
| UC-05 Manage profile | User | Explicit facts/preferences revised with provenance; hard rules governed separately | FR-12–13 |
| UC-06 Explore careers | Daily discovery + user | Adjacent categories searched and mapped without violating eligibility | FR-14–15 |
| UC-07 Weekly blind audit | Weekly scheduler + user | Five blind job reviews, then one combined reveal | FR-24–26 |
| UC-08 Baseline and comparison | Evaluation controller | Two frozen 50-job phases and one approval-gated activation in between | FR-27–30 |
| UC-09 Monitor regression | Metrics controller | Rolling 50 quality view; pause learning on configured quality decline | FR-31–33 |

### Example user stories

1. As a job seeker, I want top new eligible jobs delivered daily so that I can review opportunities without repeating searches.
2. As a job seeker, I want to reject a job because of salary without being taught to dislike its role category.
3. As a job seeker, I want to review jobs quickly and approve the AI's interpretations later in one batch.
4. As a job seeker, I want unfamiliar career directions surfaced while preserving every hard requirement.
5. As a job seeker, I want lower-ranked jobs evaluated blindly so I can detect missed opportunities.
6. As the system owner, I want reproducible rankings and source-run failures logged so I can know whether apparent improvement is genuine.

## 4. Logical Architecture

~~~mermaid
flowchart TB
    subgraph HOME["Home computer — local only"]
      UI["Streamlit dashboard\n127.0.0.1 only"]
      CLI["Scheduled Python CLI worker"]
      SVC["Python service layer\nDiscovery / Rules / Assessment / Ranking\nFeedback / Learning / Audit / Metrics"]
      DB[("SQLite + Alembic migrations")]
      LOG["Structured logs + local backups"]
      UI --> SVC
      CLI --> SVC
      SVC <--> DB
      SVC --> LOG
    end
    subgraph EXTERNAL["External services — internet required"]
      AGG["Aggregator API"]
      ATS["Employer job-board GET APIs"]
      LLM["OpenAI structured responses"]
      MAIL["Gmail API"]
    end
    SVC --> AGG
    SVC --> ATS
    SVC --> LLM
    SVC --> MAIL
~~~

**Design rationale:** A modular monolith delivers component separation while avoiding a distributed queue, microservices, container orchestration, cloud database, external message broker, or public backend API.

**Alternatives:** FastAPI plus a React UI is extensible but adds a front-end stack and infrastructure; PostgreSQL supports more concurrent writers but is unnecessary for one local user; APScheduler inside Streamlit couples scheduling to UI uptime and reruns. Recommend deferring all three until a specific requirement justifies them.

### Component responsibilities

| Component | Inputs / responsibility | Output |
|---|---|---|
| SourceAdapter | Query/board configuration, credentials, HTTP responses | Validated RawJob array |
| DiscoveryOrchestrator | Schedule, adapters, idempotent run key | RunReport + source status |
| CanonicalizationService | RawJob and existing source listings | Canonical job ID, dedup decision |
| EligibilityService | Confirmed mandatory criteria and normalized job facts | PASS / FAIL / UNKNOWN + reasons |
| AssessmentService | Eligible posting, profile version, model/prompt version | Immutable structured assessment |
| RankingService | Assessment dimensions, active approved preferences, phase snapshot | Score, rank, explanation |
| CareerMapService | Explicit profile + approved learning + observed job supply | Category snapshots |
| RecommendationCohortService | Newly scored eligible roles | Frozen top-ten evaluation cohorts |
| FeedbackService | Job decision and mandatory user explanation | Decision record + interpretation task |
| InterpretationService | Original feedback and grounded context | Structured signals or Needs Clarification |
| ApprovalService | Reviewed interpretations and corrections | Immutable approval batch |
| LearningController | Approved batches and evaluation phase | Activated preference version or held update |
| AuditService | Eligible lower-ranked non-reviewed pool | Five-item blind audit and later reveal |
| MetricsService | Completed decisions/cohorts and audits | Precision, missed-opportunity rate, diagnostic results |
| DigestService | Newly discovered recommended jobs | Idempotent email outbox with send status |
| RunHealthService | Task/source/AI/email outcomes | Dashboard status and error details |

## 5. Job Source and External Integration Strategy

### 5.1 Initial provider strategy

**RECOMMENDED for feasibility spike:** (1) Adzuna as a broad searchable feed, subject to credentials, permitted use, coverage, and quotas; (2) Greenhouse Job Board API for selected employers with known board tokens. Source priority is OPEN until verification with real results. If aggregator access is impractical, substitute a second public employer-board adapter such as Ashby while explicitly acknowledging narrower market coverage. Lever is another later adapter.

| Candidate | Verified technical interface | Design caveat |
|---|---|---|
| Adzuna | Search endpoint for job adverts with app ID/key | Requires registration; validate US coverage, costs, quotas, description completeness |
| Greenhouse | Public GET board jobs, optional expanded content | Requires discovering relevant employer board tokens; not a global search engine |
| Ashby | Public job-board postings endpoint, optional compensation field | Requires employer job-board name; missing fields possible |
| Lever | Public postings endpoints per employer | Requires employer site name; limited global/full-text discovery |

Official integration references:
- Adzuna search: https://developer.adzuna.com/docs/search
- Greenhouse Job Board API: https://docs.greenhouse.io/job-board
- Ashby public job postings: https://developers.ashbyhq.com/docs/public-job-posting-api
- Lever postings API: https://github.com/Lever/postings-api
- OpenAI structured outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- Gmail messages.send: https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/send

These references establish that endpoints exist, **not** that every desired data source offers sufficient access, rights, coverage, or pricing for this project. Perform a credential, terms, and sample-data gate before committing to a source.

### 5.2 Adapter contract

Every adapter returns a uniform RawJob containing source key, external ID (nullable), employer name, title, location fields, work arrangement (nullable), salary fields (nullable), published/updated dates (nullable), canonical source URL, description text, and source-specific metadata. A missing attribute must remain missing; never invent a salary or geographic eligibility result.

The discovery pipeline tracks:
- Source request success/failure, HTTP status, pages, timing, record count, and any rate-limit response.
- Original listing identifier and source URL.
- First and last sighting to distinguish a genuinely new posting from an already known job.
- Explicit source provenance for every merged canonical job.
- Per-provider timeouts, bounded retries with backoff, and respectful usage limits.

### 5.3 Discovery flow and run semantics

1. OS scheduler launches one Python CLI command with a local logical run date.
2. Acquire a local process lock and create or resume the unique daily run.
3. Fetch each enabled source independently; a source failure is recorded rather than hidden.
4. Normalize source records; canonicalize/deduplicate before expensive AI calls.
5. Apply hard rules; FAIL is not recommended; UNKNOWN requires explicit conservative handling.
6. Evaluate qualifying new/changed jobs; reuse cached assessments for unchanged posting + profile + scorer versions.
7. Rank and persist job assessments, career-category observations, and evaluation cohort candidates.
8. Build an email outbox containing new, not previously emailed recommendations; send only after the run's required completeness gate.
9. Record run outcomes and digest outcome separately. On partial source failure, label run PARTIAL and do not claim market coverage was complete.

**RECOMMENDED:** Run once per scheduled day, and at next startup attempt the most recent missed run. Detailed missed-day backfill policy remains OPEN; avoid an uncontrolled backlog of old job notifications.

## 6. Deduplication and Posting Lifecycle

### 6.1 Conservative hierarchy

1. **Exact provider identity:** same (provider, external listing ID) maps to the same SourceListing.
2. **Known employer requisition:** stable requisition ID plus normalized employer where supplied.
3. **Strong cross-source match:** normalized employer identity + title + location/work arrangement + substantially matching description/content or original employer link.
4. **Ambiguous match:** do not auto-merge. Keep separate records and mark as potential duplicates for inspection.

Never merge solely on matching titles; employers routinely advertise several openings with the same title.

### 6.2 Newness and reposting

A canonical Job retains first_seen_at and last_seen_at. SourceListing retains provider identity, link, first_seen_at, last_seen_at and current content hash. New-for-email means **not previously notified as that canonical job**, not merely a new source observation or changed updated_at timestamp.

**OPEN:** Decide when a genuinely distinct requisition or a repost is new enough to notify again. Default design preserves identity instead of silently treating updates as new. Expired/inactive jobs remain in history and can be hidden from live recommendations without deleting feedback.

### 6.3 Merge traceability

Persist merge evidence and both source listing IDs. If a wrong merge is discovered, support an administrative correction with audit logging. For MVP, such correction may be a simple maintenance operation rather than a full user-facing merge editor.

## 7. Eligibility, Assessment, and Ranking

### 7.1 Deterministic hard-filter boundary

Rules are confirmed facts such as required geography, work authorization, salary minimum where salary is known, employment type, and maximum travel. Each rule evaluates to PASS, FAIL, or UNKNOWN. A clearly evidenced FAIL excludes a job. UNKNOWN is never silently converted into PASS or FAIL; apply a configurable review/penalty policy once chosen. Rule evaluation includes source evidence and profile rule version.

The AI can extract facts from a job description, but **only deterministic policy code decides exclusions** using validated facts. No prompt may override hard constraints.

### 7.2 AI assessment schema (conceptual)

~~~text
JobAssessmentOutput
  qualification_fit: 0..100
  responsibility_interest_fit: 0..100
  transferable_strengths: list of grounded statements
  missing_or_unclear_requirements: list
  concerns: list
  career_category_suggestions: list
  evidence: list of source text spans / field references
  unknowns: list
  explanation: concise text
  uncertainty: low | medium | high
~~~

Use Pydantic validation and the provider's structured-output mode; handle refusals, API failures, insufficient posting information, and malformed outputs. Source descriptions are **untrusted data** and must not be allowed to instruct the model or trigger actions. Assessment evidence should refer to the job description and the versioned professional profile; do not infer credentials or experience that have not been confirmed.

### 7.3 Ranking policy (weights still OPEN)

RECOMMENDED ranking components: professional fit, responsibilities/interest alignment, approved attribute preferences, career exploration bonus, confidence/uncertainty adjustment. Hard eligibility is a gate, not a weight. Calculate a transparent deterministic final score from structured component scores; save weights and scorer version.

The initial profile comes from resume import and interview. During the first 50-job baseline, the learned weights are frozen, not the ingestion of new market observations. Never use feedback from a job to change that same job's original frozen score.

### 7.4 Career Opportunity Map

A career category contains stable identity and optional parent category. Its view includes:
- **Interest:** confirmed and approved positive/negative role-level evidence.
- **Career fit:** skills, experience and transferable strengths.
- **Confidence:** volume, consistency, and specificity of approved evidence.
- **Market opportunity:** observed eligible job supply, explicitly source-coverage dependent.
- **Trend:** change in interest or opportunity over comparable periods.

Distinguish approved-learning scores from externally observed market counts. During learning freezes, **learned interest/fit projections stay frozen**, while job-volume observations may continue to refresh. Proposed 80/20 familiar/exploratory allocation is OPEN, not a fixed implementation rule.

## 8. Feedback, Approval, and Learning Governance

### 8.1 Two independent state machines

**Job decision:** UNREVIEWED → INTERESTED or REJECTED_ARCHIVED, with mandatory nonblank user text. A later revised decision is a new event; original feedback is retained.

**AI interpretation:** PENDING_AI → NEEDS_CLARIFICATION or PENDING_APPROVAL → APPROVED or DISMISSED. Clarification generates a revised interpretation proposal; only a reviewed explicit bulk approval action authorizes its signals.

Approval and activation are **different events**: during frozen phases, approved signals remain unapplied until the permitted transition.

### 8.2 Proposed preference signal

~~~text
PreferenceSignal
  dimension: responsibilities | employer | compensation |
             work_arrangement | seniority | career_category | other
  attribute: canonical string
  polarity: positive | negative | uncertain
  scope: specific_job | specific_employer | role_family | global
  evidence_text: exact supporting feedback excerpt
  confidence: 0..1
  proposed_delta: bounded, versioned preference adjustment
~~~

One comment may yield multiple signals. A salary complaint with a positive remark about responsibilities produces separate compensation-negative and responsibilities-positive signals. A posting-level rejection is never itself a negative career-category signal.

### 8.3 Bulk approval

The queue displays each original comment alongside AI-proposed signals and any confidence warnings. User edits or clarifies mistaken interpretations. The user clicks an explicit bulk approval action covering all remaining **reviewed and eligible** proposals. Any item still Needs Clarification or explicitly dismissed is excluded. Record approval time, final signals, and the exact interpretation IDs included; no implicit auto-approval.

### 8.4 Learning application gates

- **Phase 1:** Collect and approve signals, but apply zero learned changes through completion of 50 designated ordinary reviews.
- **Transition:** Freeze and calculate Phase 1 results. User reviews pending proposals; take one authorized snapshot of approved baseline feedback, create new preference/model version, and apply it once.
- **Phase 2:** Freeze the new ranking weights through the next designated 50 ordinary reviews.
- **Transition:** Calculate Phase 2 and compare to Phase 1; if gain ≥10 percentage points, enable approved continuous learning; if not, enter INVESTIGATE state without stopping job discovery.
- **After correction:** Apply approved correction and resume continuous learning without a further mandatory 50-job experiment.
- **Continuous:** Apply only approved signals while learning state is ACTIVE; on configured decline, switch to PAUSED_FOR_QUALITY. Existing model continues ranking jobs.

**OPEN:** Quality decline reference benchmark and threshold. Until configured, show a monitor-only state; do not invent a threshold.

## 9. Measurement and Weekly Discovery Audit

### 9.1 Cohorts and reproducible precision

Each ordinary evaluation cohort is a fixed ordered list of **ten** top-ranked eligible recommendations selected under a specific scorer/profile version before user feedback. Five completed cohorts form Phase 1; five further completed cohorts form Phase 2. Assign a job to at most one ordinary evaluation cohort, retain original rank/score, and do not include audit-selected jobs.

Precision@10 = Interested count among ten reviewed cohort jobs ÷ 10. Phase precision = Interested count among all 50 assigned-and-reviewed ordinary jobs ÷ 50. Incomplete cohorts remain incomplete and are excluded from the completed metric. If fewer than ten new eligible candidates exist, the open cohort can be filled by later daily runs under the same frozen model version; no need to falsify sample size.

The 10-point threshold is a **practical product success target**, not proof of causal or statistically significant gains. Preserve a labeled reference set to compare versioned scorers on identical job descriptions.

### 9.2 Weekly blind audit

- Build one AuditBatch per scheduled week from eligible, lower-ranked jobs **not already reviewed or selected in ordinary top-recommendation cohorts**, without using predicted attraction to choose among this pool.
- Randomly select five distinct jobs and save random seed, pool definition, original assessment ID/rank, and time of selection.
- Until all five have Interested/Rejected decisions **and nonblank comments**, UI must hide scores, ranks, AI explanation, and comparisons for all five.
- Persist partial review progress; on the fifth completed review reveal the five original assessments together.
- Only then calculate the five-item missed-opportunity sample rate = Interested / five and enqueue normal AI interpretation proposals.
- If fewer than five eligible candidates exist, preserve a pending audit rather than fabricating jobs; exact skip/carry-forward policy is OPEN.

**Interpretation:** This is a lower-ranked-pool interest rate, not an unbiased estimate of all unseen jobs. Trend across weeks is more useful than one week's n=5 rate.

### 9.3 Quality scorecard

| Metric | Definition | Phase |
|---|---|---|
| Precision@10 | Interested / ten completed ordinary cohort reviews | All |
| Phase precision | Interested / 50 fully reviewed ordinary recommendations | Phases 1–2 |
| Practical learning gain | Phase 2 precision minus Phase 1 precision; target ≥10 pp | After Phase 2 |
| Rolling precision | Interested / latest 50 ordinary reviewed recommendations | Continuous |
| Audit missed-opportunity rate | Interested / five completed blind audit jobs | Weekly |
| Rule violations | Known-hard-rule violations shown to user | All |
| Interpretation correction rate | Corrected AI interpretations / reviewed interpretations | All |
| Source health | Successful, partial, failed provider runs; records found | Daily |
| Duplicate suppression | Repeated source listings collapsed into existing canonical jobs | Daily |

Also show category-level interest, exploratory success, error/unknown rates, and sources/coverage as separate supporting measurements. Quality metrics are always tied to immutable original assessment versions.

## 10. Persistence Design — SQLite

### 10.1 Storage principles

Use SQLAlchemy 2 models, repositories, foreign keys, unique constraints, Alembic migrations, and SQLite WAL mode. Store structured AI payloads as validated JSON plus indexed workflow fields where needed. Use UTC timestamps for persistence and local timezone only for scheduling/display. Do not use SQLite as a task queue or depend on concurrent writers beyond one scheduled worker and one dashboard process.

### 10.2 Proposed relational schema

| Table | Essential columns / constraints |
|---|---|
| profile_versions | id PK; version; confirmed_facts_json; explicit_preferences_json; created_at; immutable |
| eligibility_rule_sets | id PK; profile_version_id FK; rules_json; created_at; active_flag; explicit approval provenance |
| preference_versions | id PK; version; learned_weights_json; source_approval_batch_ids_json; activated_at; frozen_flag |
| career_categories | id PK; slug UNIQUE; name; parent_id FK nullable |
| career_map_snapshots | id PK; category_id FK; preference_version_id FK; interest_score; career_fit; confidence; market_opportunity; trend; observed_at |
| job_sources | id PK; provider_key; employer_board_key nullable; enabled; config_json; UNIQUE(provider_key, employer_board_key) |
| search_runs | id PK; logical_run_date UNIQUE; started_at; finished_at; status; error_json |
| source_runs | id PK; search_run_id FK; job_source_id FK; status; fetched_count; error_json; started_at; finished_at |
| jobs | id PK; employer_key; title_normalized; location_normalized; arrangement; description_text; content_hash; first_seen_at; last_seen_at; lifecycle_state |
| source_listings | id PK; job_id FK; job_source_id FK; external_id; source_url; requisition_id nullable; first_seen_at; last_seen_at; content_hash; original_json; UNIQUE(job_source_id, external_id) where external_id present |
| job_assessments | id PK; job_id FK; profile_version_id FK; preference_version_id FK; model_version; prompt_version; content_hash; eligibility_state; fit_json; score; rationale; evaluated_at; immutable |
| recommendation_cohorts | id PK; phase_key; sequence_no; model_version; preference_version_id FK; state; created_at; completed_at; UNIQUE(phase_key, sequence_no) |
| recommendation_items | id PK; cohort_id FK; job_id FK; assessment_id FK; original_rank; selected_at; UNIQUE(cohort_id, job_id); no duplicate ordinary evaluation membership |
| decision_events | id PK; job_id FK; context_type (ordinary/audit); decision; original_feedback_text NOT EMPTY; created_at; supersedes_id nullable FK |
| interpretations | id PK; decision_event_id FK; proposal_json; corrected_json nullable; clarification_text nullable; status; proposed_at; reviewed_at; approval_batch_id nullable FK |
| approval_batches | id PK; approved_at; approved_interpretation_ids_json; confirmation_note; immutable |
| learning_events | id PK; approval_batch_id FK; preference_version_before FK; preference_version_after FK; phase_key; activated_at; change_json; immutable |
| evaluation_phases | id PK; phase_key UNIQUE; evaluation_state; target_jobs; activated_at; completed_at; config_json |
| audit_batches | id PK; week_start UNIQUE; random_seed; sampled_pool_metadata_json; state; created_at; revealed_at |
| audit_items | id PK; audit_batch_id FK; job_id FK; original_assessment_id FK; original_rank; decision_event_id nullable FK; UNIQUE(audit_batch_id, job_id) |
| digest_outbox | id PK; digest_date UNIQUE; search_run_id FK; state; payload_hash; provider_message_id nullable; attempted_at; sent_at |
| digest_items | id PK; digest_id FK; job_id FK; assessment_id FK; UNIQUE(digest_id, job_id); UNIQUE(job_id) for at-most-once digest inclusion |

SQLite implementation note: nullable external IDs should have a separate normalized URL/content fingerprint constraint or a partial unique index; do not rely on normal UNIQUE semantics for nulls. When an employer legitimately posts multiple jobs with the same title, identity remains distinct unless evidence is strong.

### 10.3 Entity relationship diagram

~~~mermaid
erDiagram
    PROFILE_VERSIONS ||--o{ JOB_ASSESSMENTS : contextualizes
    PREFERENCE_VERSIONS ||--o{ JOB_ASSESSMENTS : scores_with
    PREFERENCE_VERSIONS ||--o{ CAREER_MAP_SNAPSHOTS : maps
    CAREER_CATEGORIES ||--o{ CAREER_MAP_SNAPSHOTS : has
    SEARCH_RUNS ||--o{ SOURCE_RUNS : contains
    JOB_SOURCES ||--o{ SOURCE_RUNS : executes
    JOB_SOURCES ||--o{ SOURCE_LISTINGS : publishes
    JOBS ||--o{ SOURCE_LISTINGS : observed_as
    JOBS ||--o{ JOB_ASSESSMENTS : assessed_in
    RECOMMENDATION_COHORTS ||--o{ RECOMMENDATION_ITEMS : includes
    JOBS ||--o{ RECOMMENDATION_ITEMS : selected_for
    JOB_ASSESSMENTS ||--o{ RECOMMENDATION_ITEMS : frozen_as
    JOBS ||--o{ DECISION_EVENTS : reviewed_as
    DECISION_EVENTS ||--o{ INTERPRETATIONS : explained_by
    APPROVAL_BATCHES ||--o{ INTERPRETATIONS : approves
    APPROVAL_BATCHES ||--o{ LEARNING_EVENTS : authorizes
    AUDIT_BATCHES ||--o{ AUDIT_ITEMS : includes
    JOBS ||--o{ AUDIT_ITEMS : sampled_from
    JOB_ASSESSMENTS ||--o{ AUDIT_ITEMS : preserved_as
    SEARCH_RUNS ||--o{ DIGEST_OUTBOX : produces
    DIGEST_OUTBOX ||--o{ DIGEST_ITEMS : contains
    JOBS ||--o{ DIGEST_ITEMS : emailed_once
~~~

### 10.4 Key indexes and integrity rules

- Index jobs(first_seen_at), jobs(lifecycle_state), jobs(employer_key, title_normalized), source_listings(job_id), job_assessments(job_id, evaluated_at).
- Index decision_events(job_id, created_at), interpretations(status, proposed_at), audit_batches(week_start), recommendation_items(cohort_id, original_rank).
- Keep decision events, assessments, approvals, and learning events append-only; derived current status may be projected for fast display.
- Enforce a nonempty feedback comment at service and database levels. Apply foreign key enforcement on each SQLite connection.
- A digest item may be inserted once per canonical job, even across daily digest rows, unless a future approved repost policy explicitly changes it.
- Back up with SQLite's consistent backup API while the application is running; do not copy an active WAL-backed database naively.

## 11. Service API and Data Contracts (Python-internal for MVP)

**RECOMMENDED:** Streamlit calls the same service layer as the CLI. Do **not** introduce a localhost FastAPI service just to connect Streamlit to Python.

| Service operation | Input contract | Output / invariants |
|---|---|---|
| run_daily_discovery | run_date: date, run_key: str | RunReport; idempotent for same run_key |
| collect(source_config) | SourceConfig | list[RawJob]; typed errors |
| canonicalize(raw_job) | RawJob | CanonicalizationResult with job_id, confidence, evidence |
| evaluate_eligibility(job, rule_set) | Job, RuleSet | EligibilityDecision PASS/FAIL/UNKNOWN and evidence |
| assess_job(job_id, profile_version, preference_version) | Typed IDs | Immutable JobAssessment with grounded JSON |
| rank_candidates(run_id, scoring_policy) | Run ID, versioned weights | Ordered immutable score records |
| list_jobs(status, filters, paging) | JobListQuery | Paginated JobSummary |
| submit_decision(job_id, decision, explanation, context) | JobDecisionInput | DecisionEvent; rejects blank text |
| propose_interpretation(decision_id) | Decision ID | Proposal or NeedsClarification |
| clarify_interpretation(id, text) | ClarificationInput | New validated proposal; no preference change |
| bulk_approve(interpretation_ids, edits, confirmation) | BatchApprovalInput | ApprovalBatch; all-or-nothing |
| activate_approved_learning(phase_id) | Valid phase transition | New PreferenceVersion or held event |
| assemble_weekly_audit(week_start) | date | AuditBatch of five when supply permits |
| review_audit_item(item_id, decision, text) | AuditReviewInput | Progress state; reveal only once all five reviewed |
| calculate_scorecard(window) | EvaluationWindowQuery | Versioned metrics with numerator/denominator |
| send_daily_digest(run_id) | Eligible completed run | DigestOutbox state and provider message reference |

### Example service transaction boundaries

- **Submit decision:** one transaction writes DecisionEvent and an interpretation task; UI returns immediately without waiting for AI.
- **Approve batch:** one transaction validates only reviewed proposals, records corrections and approval IDs, and marks those proposals APPROVED. No score update in this transaction.
- **Apply learning:** separate guarded transaction checks phase/quality state, creates the next PreferenceVersion and LearningEvent, and switches the active version atomically.
- **Audit reveal:** one transaction checks completion of all five items and updates batch state; UI never exposes partial results before commit.

## 12. Sequence Diagrams

### 12.1 Daily discovery and digest

~~~mermaid
sequenceDiagram
    actor Clock as OS Scheduler
    participant Worker as Python Worker
    participant Source as Job Source APIs
    participant Store as SQLite
    participant Rules as Eligibility + Ranking
    participant AI as OpenAI API
    participant Mail as Gmail API
    Clock->>Worker: Run daily discovery
    Worker->>Store: Begin/resume unique run
    Worker->>Source: Fetch configured source pages
    Source-->>Worker: Raw postings / source errors
    Worker->>Store: Upsert listings and canonical jobs
    Worker->>Rules: Evaluate hard criteria
    Rules-->>Worker: PASS / FAIL / UNKNOWN
    Worker->>AI: Assess eligible new/changed postings
    AI-->>Worker: Structured qualification assessment
    Worker->>Rules: Rank using frozen active preferences
    Worker->>Store: Persist immutable assessments, cohorts
    Worker->>Store: Prepare new-only digest outbox
    Worker->>Mail: Send eligible digest
    Mail-->>Worker: Message ID or error
    Worker->>Store: Record final run and digest states
~~~

### 12.2 Feedback and guarded batch approval

~~~mermaid
sequenceDiagram
    actor User
    participant UI as Streamlit
    participant Store as SQLite
    participant AI as Interpretation AI
    participant Queue as Approval Service
    participant Gate as Learning Controller
    User->>UI: Interested/Rejected + required free-form reason
    UI->>Store: Save DecisionEvent immediately
    UI-->>User: Continue reviewing jobs
    Queue->>AI: Interpret pending original feedback
    AI-->>Queue: Proposed attribute signals or ambiguity
    Queue->>Store: Queue proposal / Needs Clarification
    User->>UI: Open approval queue later
    UI->>Queue: Clarify/correct reviewed proposals
    User->>UI: Approve remaining reviewed proposals
    UI->>Queue: Bulk approval transaction
    Queue->>Store: Persist approved signal snapshot
    Queue->>Gate: Request application of approved signals
    alt Learning phase frozen
      Gate->>Store: Hold approved updates for next gate
    else Learning active
      Gate->>Store: Create new preference version + learning event
    end
~~~

### 12.3 Two frozen evaluation phases

~~~mermaid
sequenceDiagram
    actor User
    participant Eval as Evaluation Controller
    participant Rank as Ranking Service
    participant Store as SQLite
    Eval->>Rank: Activate baseline profile/scorer snapshot
    loop Until 50 ordinary cohort jobs fully reviewed
      Rank->>Store: Save top-ten immutable cohort selections
      User->>Store: Save decisions and explanations
      Eval->>Store: Keep learned preference weights frozen
    end
    Eval->>Store: Finalize Phase 1 precision
    User->>Eval: Confirm reviewed approved-learning snapshot
    Eval->>Store: Activate one approved preference version
    loop Until next 50 ordinary cohort jobs fully reviewed
      Rank->>Store: Save top-ten cohort selections
      User->>Store: Save decisions and explanations
      Eval->>Store: Keep new weights frozen
    end
    Eval->>Store: Finalize Phase 2 precision and compare
    alt Improvement >= 10 percentage points
      Eval->>Store: Enable approved continuous learning
    else Below target
      Eval->>Store: Investigate, hold new learning application
    end
~~~

### 12.4 Weekly blind audit

~~~mermaid
sequenceDiagram
    actor User
    participant Audit as Audit Service
    participant Store as SQLite
    participant UI as Streamlit
    Audit->>Store: Randomly select five eligible lower-ranked jobs
    Audit->>Store: Save original assessment IDs/ranks, hide until complete
    loop For each of five jobs
      User->>UI: Review posting without AI scores
      UI->>Store: Save decision and mandatory explanation
      Store-->>UI: Remaining count, assessments still hidden
    end
    Audit->>Store: Check five complete review records
    Audit->>Store: Atomically mark audit REVEALED
    UI-->>User: Reveal all five original assessments together
    Audit->>Store: Record audit rate, enqueue feedback interpretations
~~~

## 13. Service Class Structure

~~~mermaid
classDiagram
    class DiscoveryOrchestrator {
      +run(run_date) RunReport
    }
    class SourceAdapter {
      <<interface>>
      +fetch(config) list~RawJob~
    }
    class GreenhouseAdapter
    class AggregatorAdapter
    class JobRepository {
      +upsertListing(raw) Job
      +get(job_id) Job
    }
    class CanonicalizationService {
      +resolve(raw) CanonicalizationResult
    }
    class EligibilityService {
      +evaluate(job, rules) EligibilityDecision
    }
    class AssessmentService {
      +assess(job, profile) JobAssessment
    }
    class RankingService {
      +score(assessment, prefs) Score
    }
    class FeedbackService {
      +submit(decision) DecisionEvent
    }
    class ApprovalService {
      +approveBatch(items) ApprovalBatch
    }
    class LearningController {
      +activateIfAllowed(batch) PreferenceVersion
    }
    class AuditService {
      +createWeeklyAudit() AuditBatch
      +submitBlindReview() AuditProgress
    }
    class MetricsService {
      +precisionAtTen() MetricResult
      +rollingPrecision() MetricResult
    }
    SourceAdapter <|.. GreenhouseAdapter
    SourceAdapter <|.. AggregatorAdapter
    DiscoveryOrchestrator --> SourceAdapter
    DiscoveryOrchestrator --> CanonicalizationService
    DiscoveryOrchestrator --> EligibilityService
    DiscoveryOrchestrator --> AssessmentService
    DiscoveryOrchestrator --> RankingService
    CanonicalizationService --> JobRepository
    FeedbackService --> ApprovalService
    ApprovalService --> LearningController
    AuditService --> MetricsService
~~~

## 14. Data Flow Diagram

~~~mermaid
flowchart LR
    A["Job APIs / employer feeds"] --> B["Raw validated jobs"]
    B --> C["Normalize + deduplicate"]
    C --> D["Canonical postings in SQLite"]
    D --> E["Hard-eligibility filter"]
    E --> F["Grounded AI assessment"]
    F --> G["Versioned deterministic ranking"]
    G --> H["Dashboard and new-only digest"]
    H --> I["Interested / Rejected + written reason"]
    I --> J["AI interpretation proposal"]
    J --> K["Clarification + corrected bulk approval"]
    K --> L["Learning phase / quality gate"]
    L --> M["Activated versioned preferences"]
    M --> G
    G --> N["Weekly blind lower-ranked audit"]
    N --> O["Precision and missed-opportunity metrics"]
    O --> L
~~~

**Feedback-loop safety:** No direct arrow from unapproved AI interpretation to active ranking weights. The gate is mandatory.

## 15. Dashboard Information Architecture

| Screen | MVP functions |
|---|---|
| Unreviewed | Sort and browse qualifying jobs; open source and full match detail; submit Interested/Rejected with required free-form text |
| Interested | Saved seriously-considered opportunities; revisit detail and original feedback |
| Rejected / Archived | Historical postings with dates, comments, and source links; searchable |
| Job Detail | Original job facts, AI assessment, strengths, gaps, concerns, evidence and score explanation (except blind audit context) |
| Learning Approval Queue | Pending count; original comments; proposed signals; edit/clarify; exclude unresolved; explicit bulk approval |
| Career Opportunity Map | Category, interest, career fit, confidence, market opportunity, trend, with provenance and confirmed-vs-inferred distinction |
| Weekly Audit | Five blind postings and progress; reveal all together when five valid reviews exist |
| Quality Scorecard | Baseline/comparison cohorts, completed Precision@10, rolling 50, missed-opportunity trends, pause and diagnosis state |
| Profile & Rules | Resume/import results, explicit facts and preferences, manual edits, separately governed mandatory rules |
| Run Health | Last successful/partial/failed runs, provider status, daily digest status, pending approvals, configurable schedule health |

Streamlit page state and client-side hiding **must not be the sole blind-review enforcement**. Service methods must refuse to return audit assessment fields until the audit batch is REVEALED.

**Local link caveat:** A digest link using 127.0.0.1 or localhost works only on the same home computer; opening it from a phone points at that phone, not the home PC. Email should therefore include the job's external listing URL and optionally a local-only dashboard deep link. Whether external job links suffice is OPEN.

## 16. Reliability, Privacy, and Non-Functional Requirements

| Dimension | RECOMMENDED MVP target / mechanism |
|---|---|
| Reliability | Daily run idempotency and recovery; clear SUCCESS/PARTIAL/FAILED status; no hidden source failures |
| Data integrity | Conservative duplicate merging, immutable scoring snapshots, versioned approvals, unique digest membership |
| Maintainability | Modules, repositories and service layer; migrations; isolated adapters; typed settings |
| Explainability | Saved posting text/hash, profile and model version, score components, reasons and approval evidence |
| Security | Bind Streamlit to 127.0.0.1; secrets outside repository; minimum Gmail scope; local protected files |
| Performance | Designed for thousands of postings on one host; batch HTTP requests responsibly; cache unchanged AI evaluations |
| Cost | No hosting subscription required; meter external API calls and configurable usage limit |
| Portability | Windows Task Scheduler or Linux systemd timer; no dependency on Docker |
| Backup/recovery | Daily consistent SQLite backup with rotation; periodic restore test |
| Observability | Structured JSON logs; per-run source/AI/email counters; dashboard error display |

### Important security controls

- Treat every job description, employer webpage, resume import, and email-linked payload as untrusted content. Strip unsafe HTML and sanitize rendered content. Never allow an external job description to change instructions or authorize actions.
- Keep Gmail OAuth tokens and OpenAI/API credentials in environment variables or a user-private local credential store; exclude from Git.
- Use least-privilege Gmail send scope when practical; if sent-mail lookup is needed for ambiguous delivery reconciliation, seek explicit additional scope.
- Avoid logging personally identifying resume content, secrets, or full feedback text by default.
- Store backup copies outside the repository; restrict filesystem access to the local user.
- Do not present a partial API search as comprehensive market coverage.

### Email delivery edge case

A transaction cannot atomically commit SQLite and Gmail's external send call. Use an outbox: prepare a uniquely keyed digest, attempt send, then record provider response. A crash after a successful Gmail send but before local status update creates an **uncertain send state**. In the MVP, stop automatic resend of uncertain items, flag for reconciliation, and prefer a missed email over a duplicate. Do not claim exactly-once Gmail delivery.

## 17. Recommended Repository and Folder Structure

~~~text
job-search-agent/
  README.md
  pyproject.toml
  .env.example
  .gitignore
  alembic.ini
  docs/
    Job_Search_Agent_MVP_Requirements_v1_1.md
    Job_Search_Agent_Solution_Design_v1_0.md
    ADR/
  src/job_search_agent/
    config.py
    logging_config.py
    domain/
      models.py
      enums.py
      policies.py
    schemas/
      job.py
      assessment.py
      feedback.py
      metrics.py
    repositories/
      jobs.py
      feedback.py
      profile.py
      metrics.py
    services/
      discovery.py
      canonicalization.py
      eligibility.py
      assessment.py
      ranking.py
      career_map.py
      feedback.py
      approval.py
      learning.py
      audits.py
      metrics.py
      digest.py
    integrations/
      jobs/base.py
      jobs/adzuna.py
      jobs/greenhouse.py
      openai_client.py
      gmail_client.py
    persistence/
      models.py
      session.py
    ui/
      app.py
      pages/
        unreviewed.py
        interested.py
        rejected.py
        learning_queue.py
        weekly_audit.py
        career_map.py
        scorecard.py
        profile.py
        health.py
    cli.py
  migrations/
  tests/
    unit/
    integration/
    contracts/
    end_to_end/
    fixtures/
  scripts/
    install_windows_task.ps1
    install_linux_timer.sh
  data/           # ignored by Git
  logs/           # ignored by Git
  backups/        # ignored by Git
~~~

Do not create modules that have no implementation yet. The above is a target organizing scheme; begin with only the components required for the current sprint.

## 18. Deployment and Local Operation

### 18.1 Windows (RECOMMENDED if this will run on a Windows home PC)

1. Install Python 3.12+ and Git; clone the repository.
2. Create a virtual environment and install locked project dependencies.
3. Create a local configuration file from the example; configure source access, OpenAI credentials, Gmail OAuth, local timezone and schedule.
4. Initialize SQLite schema via Alembic migrations.
5. Run smoke tests using fixture providers, a fake AI client, and a fake email client.
6. Start Streamlit bound to 127.0.0.1, not all network interfaces.
7. Configure Windows Task Scheduler to launch the Python CLI daily under the local user account. Configure missed-start behavior and overlap prevention explicitly.
8. Configure a weekly audit selection task; use a second scheduled action or a date-aware branch within the same CLI.
9. Check a single end-to-end dry run, a restart recovery test, and local backup/restore before enabling live email.

### 18.2 Linux alternative

Use a Python virtual environment and systemd user timer (or cron if simpler and reliable in the target environment). The dashboard may run as a local user service. Record scheduler execution and missed-run behavior. Do not add a cloud host or externally exposed port.

### 18.3 Operational recovery

- A failed source does not erase previously collected jobs.
- A failed AI evaluation remains retryable and visible; do not label the job fully assessed.
- A restarted daily run reuses source IDs, canonical jobs, immutable cached assessments and outbox keys.
- A source/AI/Gmail error is surfaced on the Health page with actionable diagnostics.
- An overdue scheduled run should be visible even if the dashboard is opened days later.

## 19. Development Roadmap and Sprint Plan

The following is a **recommended sequencing plan**, not a date commitment.

| Sprint | Goal | Deliverables | Exit gate |
|---|---|---|---|
| Sprint 0 — Decisions and spike | Validate source access and scoring expectations | Eligibility interview, provider sample calls, architecture ADRs, baseline profile, test corpus | At least two suitable sources or documented fallback |
| Sprint 1 — Foundation | Reliable collection and dedup | Project skeleton, migrations, two adapters, run logging, canonical jobs, rule engine | Repeat runs do not duplicate jobs; failures visible |
| Sprint 2 — Recommendation | High-quality useful job assessments | Pydantic AI outputs, scoring, ranked dashboard, profile management, new-only digest | Grounded evaluations; no known hard-rule violation |
| Sprint 3 — Learning controls | Guarded preference evolution | Mandatory free-form feedback, interpretation queue, clarification, corrections, bulk approval, career map | No unapproved or frozen learning updates |
| Sprint 4 — Measurement | Reproducible improvement framework | Immutable cohorts, two-phase freeze controller, 5-item weekly blind audit, scorecard, regression pause state | All FR-24–33 acceptance tests pass |
| Sprint 5 — Release hardening | Reliable home deployment | Task scheduler, backup, authentication setup, diagnostics, integration tests, recovery runbook | Local restart/retry/restore verified |

**Testing/release approach:** Do not wait for 100 live reviews to test phase behavior. Simulate cohorts with controlled fixture decisions, then validate genuine behavior with real user feedback during operation.

## 20. Acceptance Criteria and Test Plan

### Core acceptance criteria

| Test | Given / when | Expected |
|---|---|---|
| AC-01 / FR-03 | Same role appears in two feeds and again tomorrow | One canonical job, source provenance preserved, no repeat new email |
| AC-02 / FR-04 | Source clearly violates a confirmed hard rule | No eligible recommendation or email item |
| AC-03 / FR-16–17 | Interested/Rejected submitted with blank explanation | Validation error; no decision saved |
| AC-04 / FR-19 | User rejects solely due to pay but praises duties | Compensation-negative and responsibilities-positive proposals; no category-wide penalty |
| AC-05 / FR-22–23 | Ambiguous text is interpreted | Needs Clarification; no learned preference mutation |
| AC-06 / FR-20–23 | User bulk-approves corrected proposals | Original comments retained; exact reviewed signals approved atomically |
| AC-07 / FR-28–29 | Learning is frozen in Phase 1 and Phase 2 | Preference version unchanged except at the one authorized phase transition |
| AC-08 / FR-24–26 | Four of five audit items reviewed | All AI scores hidden; fifth review reveals saved scores together |
| AC-09 / FR-27 | Audit reviews and incomplete cohorts exist | Neither contaminates completed ordinary precision denominator |
| AC-10 / FR-33 | Degradation threshold crossed | Preference application paused; daily discovery and email continue |
| AC-11 / FR-07 | Daily process retries after send uncertainty | No automatic duplicate digest; status flagged for reconciliation |
| AC-12 / FR-08 | One provider fails and others succeed | PARTIAL run visible with failed provider details |

### Test layers

- **Unit:** normalization; source identity keys; dedup confidence; eligibility PASS/FAIL/UNKNOWN; deterministic score math; signal scoping; precision; phase transition guards; audit hiding.
- **Integration:** SQLite constraints/migrations/rollback; mock provider responses; AI structured-output parsing; Gmail outbox retry states; OS command return statuses.
- **Contract:** saved fixtures for each job source, including missing salary, multiple locations, duplicate ATS IDs, HTML descriptions, and schema changes.
- **End-to-end:** local dashboard job review → AI proposal → correction → batch approval → phase-gated learning activation.
- **Negative/security:** prompt injection in job text, stale or modified profile, invalid model responses, duplicate email attempt, accidental visibility of audit score, unknown eligibility, corrupted token, interrupted backup.
- **Evaluation:** frozen test fixtures for baseline and comparison cohorts, version-diff diagnostics, and a small manually labeled reference set.

## 21. Tradeoffs, Risks, and Mitigations

| Risk | Impact | MVP mitigation | Future enhancement |
|---|---|---|---|
| Sources inaccessible or sparse | Too few jobs | Prove provider feasibility first; pluggable adapters; partial-run health | More aggregators and ATS connectors |
| Wrong cross-source merge | Missed opportunity | Conservative identity rules; retain observations and evidence | Assisted merge review |
| Incomplete job description | Poor filtering/ranking | UNKNOWN state; evidence and uncertainty | Source enrichment |
| AI overinterprets feedback | Mislearned preferences | Human-reviewed batch approval; original text; attribute scope | Better confidence calibration |
| Scoring evaluation leakage | Inflated apparent improvement | Immutable scored cohorts, original versions and feedback timing | Offline model comparison tooling |
| Low number of reviewed jobs | Delayed evaluation | Allow cohorts to span days; no invented decisions | Statistical confidence estimates |
| Daily PC unavailable | Missed postings | Scheduler recovery and health dashboard | Always-on machine |
| External API cost grows | Uncontrolled expense | Cache by content/profile version; daily quotas and budgets | Cheap-first model routing |
| Email send ambiguous after crash | Duplicate or missed digest | Outbox with uncertain state and conservative resend | Reconciliation workflow |
| Local resume/token disclosure | Privacy breach | Secret storage, loopback binding, filesystem permissions | OS keyring integration |

## 22. Future Enhancements (not MVP)

Potential v2: more ATS/aggregator adapters, employer discovery from career-category exploration, assisted duplicate merge review, embedding-based semantic similarity, more nuanced ranking experiments, statistical confidence intervals, historical model replay with holdout sets, adaptive audit sampling, richer preference ontology, optional mobile-ready remote view, and a separately justified FastAPI service.

Explicitly **not** part of v2 by implication: application tracking, interviews, or automated applications. Those require a new scope decision.

## 23. Open Decision Register and Recommended Next Actions

| Priority | OPEN decision | Why it blocks implementation | Proposed next action |
|---|---|---|---|
| P0 | Exact eligibility filters and source geography | Determines source search and hard-filter acceptance | Complete professional/eligibility interview |
| P0 | First two providers and their usable credentials | Determines whether automated discovery can work | Execute source feasibility spike on sample US roles |
| P0 | Ranking weights, unknown facts policy, minimum fit | Determines scores and inclusion semantics | Define a manually labeled starter corpus |
| P1 | Scheduling time, catch-up behavior, digest count | Determines OS task and notification rules | Choose daily operational settings |
| P1 | Repost/newness and expiry handling | Determines dedup and email inclusion | Approve lifecycle policy examples |
| P1 | Weekly audit lower-ranked pool and low supply | Determines unbiased sample eligibility | Choose pool and carry-forward rules |
| P1 | Approval queue dismissal/correction details | Determines complete queue state machine | Review mock interface |
| P1 | Exact regression threshold and benchmark | Determines learning pause trigger | Set after enough post-baseline data |
| P2 | 80/20 exploration allocation | Determines category diversity policy | Approve or adjust after baseline trials |
| P2 | Email link behavior on non-host devices | Determines digest UX | Keep external job links in MVP, decide dashboard link wording |

### Recommended design approval sequence

1. Approve the **modular monolith and internal service architecture** first.
2. Run an early **job-source feasibility spike** and **sample ranking calibration** before writing the main dashboard.
3. Finalize **eligibility and exclusion rules** explicitly; keep unknown information visible.
4. Approve the **database identity/learning/evaluation model**, with particular attention to immutable cohorts and separation between signal approval and activation.
5. Only then begin Sprint 1 implementation.

## 24. External Reference Notes

External documentation was consulted for technical feasibility, not to alter approved product requirements:

1. Greenhouse Job Board API: publicly documented GET endpoint for job boards and published job content.
2. Adzuna Search API: documented job advertisement search interface and key-based parameters.
3. Ashby Job Postings API: publicly documented employer job-board listings, optional compensation request field.
4. Lever Postings API: public employer postings endpoints.
5. OpenAI Structured Outputs: schema-constrained outputs and Pydantic compatibility with validation caveats.
6. Gmail API messages.send: OAuth-authenticated message delivery endpoint.

Provider access permissions, price, quotas, coverage, and acceptable use **must still be confirmed** against the exact sources selected. No source completeness claim or fee quote is made here.

---

**Design status:** Proposed architecture. Functional requirements remain authoritative in v1.1; areas labeled OPEN are not implementation decisions.
