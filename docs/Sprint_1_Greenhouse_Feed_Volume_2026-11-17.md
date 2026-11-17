# Sprint 1 — Greenhouse Direct Feed Access and Volume (2026-11-17)

**Status:** FIVE-BOARD API ACCESS PASS; measured 30-day first-publication counts, but eligible recent contract volume NOT YET ESTABLISHED.  
**Test execution:** 2026-11-17 16:59:01 UTC, on user's Windows PowerShell machine.  
**Source:** User-supplied terminal screenshot from `scripts/feasibility/test_greenhouse_feed_volume.ps1`.  
**Access:** Public unauthenticated Greenhouse Job Board API; one GET per named board; zero Adzuna calls.  
**Scope:** Source feasibility only, **not** individual job evaluation or production integration.

## Executive summary

- **5/5** public employer board API GETs succeeded with HTTP **200**.
- **722 total postings**, of which **721 were non-prospect jobs** (OpenMined had one general/prospect post excluded by `internal_job_id` absent). **721 unique IDs within sampled boards.**
- **All 721 non-prospect jobs supplied a parseable `first_published` date** in the actual list results, contrary to the initial documentation concern that this might require per-job GETs.
- **346** jobs were first published within the past **30 days** (**48.0%** of the 721).
- **623** jobs had `updated_at` in the past 30 days. This is **NOT** the newly published count and should not be substituted for the 346.
- **175** job titles matched the script's broad role-family words (project, program, product, portfolio, PMO, transformation, delivery). Not validated eligible roles.
- **254** records triggered the heuristic contract-related title/custom-metadata test, **250 of which came from INFUSE**. Not independently verified contract employment and **not** a count of recent target-role contract positions.
- **No intersection count** was reported for **first-published within 30 days AND contract signal AND target-role signal**, nor for location/remote/US-eligibility. This is now the critical next metric.

## User-run measurements

| Board | HTTP | API postings | Non-prospect jobs | Unique job IDs | Role-family title signals | Contract signals | First-published within 30 days |
|---|---:|---:|---:|---:|---:|---:|---:|
| gitlab | 200 | 252 | 252 | 252 | 23 | 2 | 114 |
| vercel | 200 | 87 | 87 | 87 | 11 | 1 | 18 |
| openmined | 200 | 16 | 15 | 15 | 3 | 0 | 15 |
| infuse | 200 | 269 | 269 | 269 | 126 | 250 | 165 |
| crunchyroll | 200 | 98 | 98 | 98 | 12 | 1 | 34 |
| **Total** | | **722** | **721** | **721 within board** | **175** | **254** | **346** |

### Date fields observed

| Board | First published known | First published recent (30d) | Updated known | Updated recent (30d) | Updated role signals | Updated contract signals |
|---|---:|---:|---:|---:|---:|---:|
| gitlab | 252 | 114 | 252 | 252 | 23 | 2 |
| vercel | 87 | 18 | 87 | 87 | 11 | 1 |
| openmined | 15 | 15 | 15 | 15 | 3 | 0 |
| infuse | 269 | 165 | 269 | 171 | 63 | 171 |
| crunchyroll | 98 | 34 | 98 | 98 | 12 | 1 |
| **Total** | **721** | **346** | **721** | **623** | **112** | **175** |

**Interpretation:** `first_published` and `updated_at` have different meanings; update-date count is 623 and should not be represented as 623 newly published jobs. `first_published` is a platform-provided timestamp; verify semantic behavior for edits/reposts if needed.

## Important risks and qualifiers

1. **Contract heuristic ambiguity:** The script tags title words or selected metadata field values containing `contract`, `temporary`, `1099`, etc. A title such as `Contract Manager` is not necessarily contingent employment. Likewise, custom metadata may be inconsistently used by employers.
2. **INFUSE concentration:** 250/254 (98.4%) contract signals came from one board. A single employer's labeling behavior can dominate the number. Analyze the contract signal field source and actual type/category distribution without assuming valid contract opportunities.
3. **Role overlap missing:** Of 175 broad title signals, 126 are INFUSE, but no overlap with 254 contract signals and 346 first-published-recent dates has been measured. The same applies to US/remote geography.
4. **Selection bias:** Five specifically selected employer boards are not a representative sample of all Greenhouse users. These counts cannot be extrapolated to the provider.
5. **Unique ID scope:** IDs were unique within each board; duplicate postings across boards/providers have not yet been tested.
6. **Daily access:** One successful run does not validate day-over-day uptime or actual new daily IDs.
7. **New posting vs. original vacancy:** `first_published` is much better evidence than `updated_at`, but republishing or copying a job may still create a newer timestamp.

## Comparison with Ashby (separate five-board sample)

| Metric | Ashby | Greenhouse |
|---|---:|---:|
| Employer boards tested successfully | 5/5 | 5/5 |
| Listed/non-prospect jobs | 292 | 721 |
| Published in preceding 30 days | 120 | 346 |
| Contract-like signals (unverified) | 16 | 254 |
| All tested jobs with readable publication dates | Yes | Yes |

**Do not infer** Greenhouse universally has 2.5 times the job volume of Ashby; these are different selected employers.

## Recommendation

**Next highest-information test:** Add a compact aggregate report for the **same five Greenhouse boards** that counts: (a) first published in last 30 days, (b) broad PM/program/product/PMO/portfolio title, (c) contract type / contract metadata evidence, (d) **intersection of all three**, and (e) rough US/remote geographic breakdown, keeping dubious classifications explicitly separate. Determine why INFUSE produces 250 contract signals and whether these describe actual employment type. No individual job suitability scoring or application research.

After that, test five public Lever employer feeds; continue to reserve Adzuna Pending Activation calls. No production implementation has been started.
