# Sprint 1: Source Validation and Eligibility Definition

**Status:** IN PROGRESS (updated November 17, 2026)

## Objective

Validate that permitted job sources can supply relevant, sufficiently detailed new postings; finalize explicit user-specific eligibility requirements **before any application implementation**.

## Deliverables

- [Source feasibility and provider test plan](./Sprint_1_Job_Source_Feasibility.md) — prepared; real API measurement pending.
- [Eligibility definition workbook](./Sprint_1_Eligibility_Definition.md) — existing confirmed criteria.
- [Questionnaire with user answers](./Sprint_1_Remaining_Decisions_Questionnaire.md) — committed; read and preserved verbatim.
- [Eligibility Decisions v1.0](./Sprint_1_Eligibility_Decisions_v1_0.md) — answers classified as confirmed, conditional, or open.
- [Source Test Search Plan](./Sprint_1_Source_Test_Search_Plan.md) — representative 80% contract / 20% full-time validation queries.
- [First live source validation results (2026-11-17)](./Sprint_1_Live_Source_Test_Results_2026-11-17.md) — **two independent public JSON feeds successfully retrieved**, remaining targeted source tests pending.
- Actual comparison of live source results — not yet completed.
- Approved versioned eligibility rules and initial provider selection — not yet completed.

## Completed

1. Premature Python foundation commit bd8aa7a was reverted by 3b16cfa; docs preserved.
2. Read official Adzuna, Greenhouse, Ashby, Lever, USAJOBS interface documentation.
3. Defined an evidence-based live source test protocol and honest limitations.
4. Received the user's consolidated questionnaire answers; extracted the decisions without altering the original.
5. Documented 80/20 contract/full-time source search mix, 30-day initial lookback for each new source, Regions/Invesco exclusions, TN-only relocation possibility, and salary/workload qualifications.
6. Created source-testing portfolio and noted the unanswered repost scenario (Q18), conditional C2C classification, and foreign hiring eligibility questions.
7. Retrieved a real Ashby Ramp employer-board JSON feed with full job descriptions and structured compensation; documented the hybrid-isRemote trap.
8. Retrieved a real Himalayas unfiltered remote-jobs JSON page and observed country restrictions, currency, salary-period and update timestamps; direct keyword-filtered API calls could not be validated in the browsing environment.
9. Inspected public Greenhouse and Lever job posting pages as rule-test examples; direct API JSON feeds remain unverified, not declared down.
10. Reviewed official Himalayas API terms, Adzuna personal-search terms and free-key access.

## Next actions

1. Complete targeted query tests for representative 80% contract/20% full-time searches, especially actual relevant postings (unfiltered feeds alone are inadequate).
2. Confirm accessible live Greenhouse/Lever board APIs and a local/hybrid broad-source provider; Adzuna needs a personal evaluation key.
3. Measure actual job relevance, source overlap, original posting age versus last-updated dates, salary and work arrangements, and revisit on another date for freshness.
4. Resolve only material remaining Q18/C2C/foreign-hiring/TN-relocation edge cases, approve initial sources and eligibility before Sprint 2 implementation.

## Sprint naming correction

The earlier solution-design draft called source discovery Sprint 0 and application foundation Sprint 1. Correct project numbering is **Sprint 1 = source validation and eligibility**, **Sprint 2 = foundation**, Sprint 3 = recommendation, Sprint 4 = learning, Sprint 5 = measurement, Sprint 6 = release hardening.
