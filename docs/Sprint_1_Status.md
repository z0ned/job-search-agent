# Sprint 1: Source Validation and Eligibility Definition

**Status:** IN PROGRESS (updated November 17, 2026)

## Objective

**Current active task:** Verify that job feeds/APIs can be accessed programmatically, repeatedly, legally, and at sufficient **posting volume** to support the local agent. Job-specific desirability, suitability, pay, qualification gaps, and recommendations are **out of scope for the current source test**. Eligibility requirements have been collected separately; no implementation starts before design approval.

## Deliverables

- [Source feasibility and provider test plan](./Sprint_1_Job_Source_Feasibility.md) — prepared; real API measurement pending.
- [Eligibility definition workbook](./Sprint_1_Eligibility_Definition.md) — existing confirmed criteria.
- [Questionnaire with user answers](./Sprint_1_Remaining_Decisions_Questionnaire.md) — committed; read and preserved verbatim.
- [Eligibility Decisions v1.0](./Sprint_1_Eligibility_Decisions_v1_0.md) — answers classified as confirmed, conditional, or open.
- [Feed Access and Volume Validation Plan v1.1](./Sprint_1_Source_Test_Search_Plan.md) — corrected feed-only scope, access/count/freshness test matrix.
- [First live source validation results (2026-11-17)](./Sprint_1_Live_Source_Test_Results_2026-11-17.md) — **two independent public JSON feeds successfully retrieved**, remaining targeted source tests pending.
- [Earlier targeted posting sample](./Sprint_1_Targeted_Posting_Sample_2026-11-17.md) — historical exploratory work **outside current feed-only test scope**; these individual HTML examples **do not** count toward feed verification.
- Actual direct-feed count comparison across providers, sources and repeat runs — **not yet completed**.
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

## User scope correction (2026-11-17)

**The user explicitly clarified:** “We are not searching for good jobs right now, we are only validating that we can access enough jobs though feeds.”

This overrides any prior language implying that handpicked job pages, subjective role-fit review, or salary qualification checks are Sprint 1 feed-test deliverables. The 10 manually inspected posting examples remain historical notes only. **No individual job recommendation activity is authorized in the active feasibility test.**

## Next actions

1. Get actual **direct HTTPS JSON feed responses** from each candidate provider; distinguish tool/network restrictions from source unavailability.
2. Measure accessible job **volumes** (total returned and unique IDs, page/cursor reach, count with reliable original post dates in last 30 days).
3. Check broad keyword/location/work-type feed filter capabilities without reviewing postings for personal suitability.
4. Test repeatability and provider quotas, access permissions, key/cost requirements.
5. Present a quantified **feed access, volume, data fields, freshness and cost** comparison and recommend the smallest viable set. Final job-selection logic is a separate later task.

## Sprint naming correction

The earlier solution-design draft called source discovery Sprint 0 and application foundation Sprint 1. Correct project numbering is **Sprint 1 = source validation and eligibility**, **Sprint 2 = foundation**, Sprint 3 = recommendation, Sprint 4 = learning, Sprint 5 = measurement, Sprint 6 = release hardening.
