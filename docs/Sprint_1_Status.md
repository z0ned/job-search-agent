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

## Adzuna access update (2026-11-17)

The user has created a local untracked `.env` in the repository root with their Adzuna credentials and reports **Pending Activation — 25 test API calls**. According to their provider account notice, the **API Access** tier offers 5,000 calls/month and 500/day, while **Pro** offers 20,000 calls/month; prices shown when selecting a plan. **These numbers are user-reported account conditions, not tested quotas or approved paid subscriptions.**

- Credentials are **not** in GitHub; this repository does not contain the user's app ID/key.
- **Trial call budget:** 25 total test requests (reported), with zero confirmed executed from the user's local key so far.
- First local test should use **one bounded search request** and report only status, API-reported total, returned count and whether pagination is visible. Never publish key, full request URL with credentials, or proprietary response dumps.
- Prioritize a small handful of high-information searches that answer **feed access and total accessible job volume**, then stop before exhausting the trial balance. No automatic loops or broad paging during the trial.
- Full paid activation requires an explicit cost/terms decision, **not** an automatic next step.

## Adzuna country-coverage verification (2026-11-17)

Official **standard Job Search API** OpenAPI specification `https://developer.adzuna.com/swagger/spec/test2.json` explicitly enumerates `us` (United States), `ca` (Canada), and `mx` (Mexico) for `GET /jobs/{country}/search/{page}`. Supported request fields include `what`, `where`, `contract=1`, `permanent=1`, `max_days_old` and pagination. The USA endpoint is `https://api.adzuna.com/v1/api/jobs/us/search/1`, with `app_id` and `app_key` added locally at execution time.

**Important distinction:** Adzuna's separate **Intelligence** API documentation says its analytics API currently serves UK data only; that limitation does not apply to the standard job search endpoint's published `us` country support.

**Evidence level:** U.S. support **CONFIRMED IN OFFICIAL SPECIFICATION**, but actual U.S. API response using the user's **Pending Activation** key remains **UNTESTED**. No trial calls spent by this documentation-only verification, and no actual U.S. volume claimed.

Sources:
- Standard search OpenAPI: https://developer.adzuna.com/swagger/spec/test2.json
- Standard API overview: https://developer.adzuna.com/overview
- Separate Intelligence API coverage note: https://developer.intelligence.adzuna.com/doc-593840

## Adzuna authenticated U.S. source test — PASS (2026-11-17)

**Evidence:** User executed a PowerShell one-request test locally using the Adzuna Pending Activation trial credential, with country path `/jobs/us/search/1`, keyword `project manager`, location `Atlanta`, and `results_per_page=20`. The user supplied a screenshot showing:

- **API access: SUCCESS**
- **Total US jobs matching search: 8509** (provider-reported estimate/inventory count for **that specific query**, not all U.S. jobs)
- **Jobs returned: 20** (one response page)

**Interpretation:** Authenticated programmatic access to U.S.-country Adzuna jobs is **VERIFIED** on the user's local Windows computer. This does **not** establish distinct inventory, actual 30-day freshness, usable page depth, contract category coverage, sustained rate limits, or daily reliability. The first local request appears to consume **1 of 25** user-reported trial calls, provided no other local requests were made.

**Security:** Neither `ADZUNA_APP_ID` nor `ADZUNA_KEY` was disclosed or committed; both remain in the local ignored `.env`.

**Next highest-value check:** One bounded `/jobs/us/search/1` call with `contract=1`, `max_days_old=30`, `where=Atlanta`, `what=project manager`, `results_per_page=20`; inspect aggregate `count`, returned count and presence of job identifiers, creation dates and pagination. Do not evaluate individuals' suitability.

## Adzuna website volume observation (user-reported, 2026-11-17)

The user reports **419 job listings** on Adzuna's U.S. **website** when filtering to jobs **posted within the last 7 days**, **within 25 miles** of their Atlanta-area search, and **minimum $150,000 equivalent**. **Applying the Contract filter reduces the displayed count to 11 jobs** with the other website criteria unchanged. The earlier browsing context was a Project Manager search in Atlanta; exact query wording and how the website derives estimated salary-equivalents remain unverified.

**Evidence tier:** User-reported website displayed count; **NOT an authenticated API count**, unique job count, or verified original-post-date count. The **419** figure includes contract and/or permanent job results (not a contract-only count); the **11** figure is contract-filtered. These are website counts, may include duplicates, and website inventory/filter semantics may differ from API search. No new Adzuna trial API calls consumed.

**Implication:** A meaningful volume signal worth testing, but not proof that hundreds of recent contract PM jobs can be programmatically accessed. Contract filtering is now confirmed by the user: **11 of 419** are contract-filtered results (approximately **2.6%**, based on displayed counts only). This reinforces the importance of finding multiple contract job sources. The annual-equivalent $150K cutoff is close to but somewhat higher than $70/hour at 2,080 paid hours ($145,600/year), and can exclude contracts without compensation information; the website is not a substitute for a pay-neutral contract volume check. Reserve API calls for limited feed/website parity tests.

## Ashby direct-feed volume test — prepared (2026-11-17)

- **Live public JSON read succeeded** for the Ramp board through the browser-based source test.
- **Other selected public Ashby board API requests did not return usable data through this environment** (and the `ashby` board exceeded the browser tool's 4 MiB response limit). These are tool limitations, not observed proof of source downtime.
- **Direct shell request from this environment failed DNS resolution**; this is not an upstream API failure.
- Committed a **one-off, read-only feasibility tool** at [scripts/feasibility/test_ashby_feed_volume.ps1](../scripts/feasibility/test_ashby_feed_volume.ps1). It makes **one GET each** for five employer boards (Ramp, Juniper Square, GreenLight Workforce Solutions, Coder, Teamworks) and reports successfully parsed jobs, listed/unique job IDs, recent posting dates, basic contract-type metadata signals and HTTP status or failed board.
- The script stores no job descriptions, credentials or personal commute address. It needs **no API key** and uses **zero Adzuna trial calls**. **Executed successfully on the user's home computer on 2026-11-17; see the verified measurements below.**
- This is source **access and volume** validation only, not job quality or individual opportunity searching.

## Ashby five-board direct API results — VERIFIED (2026-11-17)

User-run PowerShell test at **2026-11-17 16:49:53 UTC** returned **HTTP 200 from all five boards**: Ramp 179 listed/66 recent, Juniper Square 52/22, Greenlight Workforce Solutions 23/13, Coder 27/16, Teamworks 11/3. **Total: 292 listed posts, 120 with publishedAt in last 30 days, zero unknown dates**, 292 IDs distinct **within their respective boards**. **16 title/employment-type contract signals** are a rough heuristic, **not 16 verified contracts**; only one record was tagged `Temporary` and employment-type labels were otherwise `FullTime` or `Intern`. The contract-signal/30-day intersection was not reported.

**Scope:** Demonstrates accessible **feed volume at these five employer boards** with zero API credentials and no Adzuna calls. It does not measure Ashby-wide supply, repeat-day new postings, cross-provider deduplication, or sufficient **recent contract** volume.

[Full measurements and interpretation](./Sprint_1_Ashby_Feed_Volume_2026-11-17.md).

## Greenhouse five-board read-only feed probe — prepared (2026-11-17)

- Committed [scripts/feasibility/test_greenhouse_feed_volume.ps1](../scripts/feasibility/test_greenhouse_feed_volume.ps1) to test five named public Greenhouse board tokens: **gitlab, vercel, openmined, infuse, crunchyroll**.
- Script makes **one unauthenticated GET per board** against official public `GET /v1/boards/{board_token}/jobs`, with the compact list response (no `content=true`). It counts total postings, non-prospect jobs (`internal_job_id` present), unique job-post IDs, broad role-title signals, and **contract title/custom-metadata heuristic signals (unverified)**.
- **Critical date distinction:** The Greenhouse list API documents `updated_at`; `first_published` is documented on the individual job GET response. The script counts first-published dates **only if present on the list records**. The updated-in-30-days number is **not** a count of newly published jobs. No one-request-per-posting enrichment is attempted.
- **Executed successfully locally on 2026-11-17; actual measurements below supersede this pre-test note.**
- Requires **no keys** and **zero Adzuna trial calls**. This is a feasibility probe, not production code or job suitability evaluation.

## Greenhouse five-board direct API results — VERIFIED (2026-11-17)

The user ran the read-only Greenhouse script locally at **2026-11-17 16:59:01 UTC**. **All 5/5 board feeds returned HTTP 200**: GitLab **252** non-prospect jobs (**114 first-published within 30 days**), Vercel **87/18**, OpenMined **15/15** (16 raw postings; 1 excluded prospect), INFUSE **269/165**, Crunchyroll **98/34**. **Totals: 721 non-prospect jobs (722 raw board postings), 346 first published within 30 days, 721 readable first-published timestamps and unique per-board IDs**. Separately **623** were updated within 30 days, which is **not** a new-posting count.

Of the 721, **175** titles match broad project/program/product/portfolio/PMO/transformation/delivery keywords; **254** triggered the rough contract title/metadata heuristic (**250 from INFUSE alone**). **Crucial: these are not confirmed contracts and neither the recent+contract+role intersection nor US geographic suitability has been measured.** Do not conflate the provider's many recent update timestamps with original postings or infer provider-wide market totals. No keys or Adzuna trial calls consumed.

[Full five-board source-volume report](./Sprint_1_Greenhouse_Feed_Volume_2026-11-17.md). Recommended next action: probe recent **contract ∩ role** inventory and validate INFUSE contract classification, then test Lever. No production application code has been started.

## Greenhouse recent × role × contract overlap probe — approved and committed (2026-11-17)

The user approved a **targeted follow-up on the same five validated Greenhouse boards before moving to Lever**. Committed the read-only PowerShell script [scripts/feasibility/test_greenhouse_contract_overlap.ps1](../scripts/feasibility/test_greenhouse_contract_overlap.ps1).

**Purpose:** With one unauthenticated `GET /v1/boards/{board}/jobs` per selected employer, report each board's **30-day first-published ∩ broad target-role-title ∩ contract-signal** count, separate contract evidence from **title only, employer custom metadata only, or both**, and show aggregated INFUSE work-type-like metadata field/value frequency and location labels among the intersection. This provides a direct diagnostic for whether the **250 INFUSE contract signals** in the initial test reflect meaningful type metadata rather than a misleading heuristic. Counts remain **signals**, not verified job contracts, and remote/U.S. location labels do **not** establish eligibility.

**Execution:** The script has been committed but **not yet run on the user's PC**. No count for the triple intersection is claimed. No production code, applicant evaluation, credential use or Adzuna calls. Run from the repo root with:

    git pull origin main
    powershell -NoProfile -File .\scripts\feasibility\test_greenhouse_contract_overlap.ps1

Completed; measured results recorded below. Selected next source for feasibility validation: Lever.

## Greenhouse recent × role × contract follow-up — COMPLETED (2026-11-17)

**User-run at 17:09:27 UTC:** Five of five Greenhouse boards succeeded. **722** non-prospect postings, **347** first published within 30 days, **175** broad target-role title signals, **254** contract-like title/metadata signals. **63** satisfied **recent ∩ role ∩ contract signals**, all from INFUSE. All 63 had both title and metadata signals. INFUSE type metadata comprised **247 Non-US Contractor, 3 UA Contractor, 17 US Employee, 1 INTL Employee, 1 APAC Employee**. The 250 contractor-type signals thus refer to international/UA contract categories, **not verified opportunities eligible for a U.S.-based applicant**. Two of 63 overlap records have Atlanta/Georgia literal location labels, but work eligibility remains unverified.

**Decision:** Greenhouse is technically valid as a per-employer feed, but **U.S.-eligible recent contract PM supply has not been demonstrated** in the five-board sample. Next source to test is **Lever**. Do not assume Greenhouse-wide absence. [Full measured report](./Sprint_1_Greenhouse_Contract_Overlap_2026-11-17.md).

## Next actions

1. **Adzuna U.S. direct authenticated feed is now verified.** Next measure its 30-day contract search volume and page retrieval limits. Continue unverified Greenhouse/Lever APIs in parallel.
2. Measure accessible job **volumes** (total returned and unique IDs, page/cursor reach, count with reliable original post dates in last 30 days).
3. Check broad keyword/location/work-type feed filter capabilities without reviewing postings for personal suitability.
4. Test repeatability and provider quotas, access permissions, key/cost requirements.
5. Present a quantified **feed access, volume, data fields, freshness and cost** comparison and recommend the smallest viable set. Final job-selection logic is a separate later task.

## Sprint naming correction

The earlier solution-design draft called source discovery Sprint 0 and application foundation Sprint 1. Correct project numbering is **Sprint 1 = source validation and eligibility**, **Sprint 2 = foundation**, Sprint 3 = recommendation, Sprint 4 = learning, Sprint 5 = measurement, Sprint 6 = release hardening.
