# Sprint 1 — Himalayas US Remote Contractor/Temporary Filtered Feed Volume (2026-11-17)

**Status:** Filtered programmatic ACCESS PASS for all eight query slices. Substantial provider-reported remote contractor inventory; sufficient **new, actually US-eligible target-role** jobs unproven.

**Execution:** User ran `scripts/feasibility/test_himalayas_feed_volume.ps1` locally in Windows PowerShell on **2026-11-17 at 18:31:36 UTC**. Eight first-page GET requests, one per query, each **HTTP 200** with no credentials. No Adzuna trial calls consumed.

**Scope:** API access, query-level inventory counts and first-page filter sanity check only. No individual job evaluation, no production implementation.

## Executive summary

- **8/8 filtered search requests succeeded**.
- Broad `country=US&employment_type=Contractor,Temporary` (no keyword) reported **6,325 matches** in the Himalayas **remote-only** feed. This is a **provider-reported count**, not 6,325 locally downloaded, personally eligible, recently first-published or distinct jobs independently verified.
- Across eight searches, **144 sample rows** were retrieved. They represented **118 distinct GUIDs across query samples**, or **26 repeated appearances across overlapping result slices**. Within each query's sampled page, no repeated or missing GUIDs were reported.
- Sampled classifications were strictly `Contractor` or `Temporary` (zero type mismatches) and location restrictions were either **US explicit or worldwide** (zero other-country/unknown location restrictions).
- **0 expired samples** by `expiryDate` and **0 HTTP errors**. These are source-provided fields, not employer-verification evidence.
- **`pubDate` measures LAST UPDATED, not first published**, so 30-day `UpdatedRecent` metrics **must not** be interpreted as 30-day newly posted jobs. No original first-published date is present in this feed.

## Exactly reported search volumes

| Query slice (all are US-or-worldwide remote Contractor/Temporary) | API-reported totalCount | Sample fetched | Unique IDs within sample | Updated in last 30d (sample) | Broad role-title hints in sample | Compensation disclosed in sample |
|---|---:|---:|---:|---:|---:|---:|
| ALL_US_CONTRACT | 6,325 | 20 | 20 | 20 | 1 | 12 |
| PROJECT_MANAGER | 231 | 20 | 20 | 20 | 9 | 9 |
| PROGRAM_MANAGER | 131 | 20 | 20 | 20 | 12 | 7 |
| PRODUCT_MANAGER | 93 | 20 | 20 | 20 | 8 | 7 |
| PMO | 6 | 6 | 6 | 3 | 4 | 0 |
| PORTFOLIO_MANAGER | 18 | 18 | 18 | 11 | 8 | 2 |
| IMPLEMENTATION_MANAGER | 32 | 20 | 20 | 15 | 11 | 6 |
| TRANSFORMATION | 65 | 20 | 20 | 20 | 5 | 1 |
| **Total sample (overlapping)** | **DO NOT SUM** | **144** | **118 distinct across all query slices** | **129 sample appearances** | **58 sample appearances** | **44 sample appearances** |

Do **not add** provider-reported counts for named queries; matches overlap. Counts for updated/role/pay across rows also include repeated job appearances, not globally unique jobs.

## Filter sanity check: exact sample breakdown

| Slice | Contractor | Temporary | US-restricted | Worldwide | Wrong type / other-country restrictions |
|---|---:|---:|---:|---:|---:|
| ALL_US_CONTRACT | 18 | 2 | 15 | 5 | 0 |
| PROJECT_MANAGER | 15 | 5 | 20 | 0 | 0 |
| PROGRAM_MANAGER | 14 | 6 | 20 | 0 | 0 |
| PRODUCT_MANAGER | 19 | 1 | 20 | 0 | 0 |
| PMO | 6 | 0 | 6 | 0 | 0 |
| PORTFOLIO_MANAGER | 16 | 2 | 18 | 0 | 0 |
| IMPLEMENTATION_MANAGER | 19 | 1 | 20 | 0 | 0 |
| TRANSFORMATION | 20 | 0 | 20 | 0 | 0 |

**Important**: `country=US` implicitly includes worldwide-allowed jobs. These are **geographic availability metadata**, not proof that a Georgia-based applicant can be hired. Time zone and contractual jurisdiction requirements remain unchecked.

## What has and has not been proven

**PASS:**
- Search API can be called without an account/key from the user's machine, including keywords, country restriction and Contractor/Temporary filters.
- Search gives per-query `totalCount` and GUID-bearing results; 8/8 queries returned actual JSON.
- Many nominal US/worldwide contractor/temporary postings are available in a broad aggregator, unlike testing isolated employer boards one-by-one.

**OPEN / NOT PROVEN:**
1. **Pagination depth and stability**. Only first page fetched for seven query slices, and all records returned only for two small slices (PMO 6 and Portfolio Manager 18). Validate page 2 (IDs new, same filters enforced).
2. **Original posting freshness and new arrivals.** `pubDate` is last updated, not first published; test cross-day new GUIDs and check origin/visibility if required.
3. **Title/role precision**. For `q=project manager`, just **9 of the first 20** titles included any broad role-family term. Keyword matches can occur outside job title. Search count should not be conflated with relevant project manager positions.
4. **Cross-query and cross-source deduplication.** 118 distinct GUIDs from 144 retrieved entries. Not yet compared with ATS or Adzuna results.
5. **Compensation and duration**. Many sample listings lack disclosed pay, so pay filters should remain disabled for source-feasibility checks; unknown salary is allowed by MVP requirements. No pay validation completed.
6. **Employment eligibility**. US/worldwide tags and remote labels do not prove that the employer hires Georgia residents, uses US work contracts, or meets timezone expectations.
7. **Source terms/quotas**. Public API is documented as keyless and daily-cached; for production a free key may give more stable shared quotas. Visible Himalayas attribution and `applicationLink` usage are required by its API terms.
8. **Local work arrangements**. The source covers remote jobs, not local onsite or hybrid roles; complementary sources still necessary.

## Comparison to earlier source validation

| Provider | Test performed | Observed direct records | Evidence for recent US contract-role inventory |
|---|---|---:|---|
| Ashby | 5 employer board GETs | 292 postings, 120 `publishedAt` in past 30d | 16 contract heuristics, role/date intersection not tested |
| Greenhouse | 5 employer boards with contract overlap | 722 postings, 347 `first_published` in past 30d | 63 recent-role-contract signals, all from INFUSE; contractor metadata predominantly non-US/UA |
| Lever | 5 employer boards with commitment overlap | 111 postings, 40 created in past 30d | 4 recent-created explicit contract-role hints, 2 US-country remote; `createdAt` ≠ published |
| Himalayas | 8 country/type-filtered keyword search slices | 144 sample appearances / 118 unique GUIDs | 6,325 provider-reported unfiltered-role US/worldwide contractor/temporary records; **true fresh/eligible target-role quantity not yet verified** |
| Adzuna | 1 API query + website filtered observation | 20 initial API results; website 11 contract results (7d, 25mi, $150K+) | App key trial quota; contract website volume restrictive, especially with salary requirement |

Comparison is **not a ranking of providers by actual eligible jobs**. Samples differ in geography, dates, role filters and provider shape.

## Recommended next validation (minimal)

1. **Pagination + filter stability:** Sample **page 2 only for Project Manager and Program Manager** (2 additional public requests), and compare new GUIDs against page 1 and type/country fields. Script currently supports `-MaxPages 2` for all 8 slices; to minimize calls, add a minimal query-selection parameter or run a narrowly scoped independent spot-check.
2. **Daily new-job rate:** Revisit a small stable query after a 24h API refresh, retain only GUID snapshots and compare new IDs. This distinguishes daily supply from a large stock of old/updated listings.
3. **Title-filter precision and jurisdiction coverage:** Measure title/category match rates and US-timezone restrictions on a bounded multi-page sample, not per-job suitability.
4. If stable, recommend Himalayas as a **complementary remote source** alongside targeted employer ATS feeds. Do not decide it is sufficient for the 80%-contract search effort until per-day newly discoverable, plausible U.S.-eligible role volume is observed.

**No production agent app or personal recommendations implemented.**
