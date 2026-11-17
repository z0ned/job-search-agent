# Sprint 1 — Ashby Feed Access and Volume Test (2026-11-17)

**Status:** FEED-ACCESS PASS for five named employer boards; provider-wide volume and contract supply NOT established.  
**Source:** User-run Windows PowerShell output supplied in conversation; `scripts/feasibility/test_ashby_feed_volume.ps1`.  
**Execution time:** 2026-11-17 16:49:53 UTC.  
**Window:** 30 days from test execution, using each posting's `publishedAt` field.  
**Scope:** API access and volume only; **no job suitability evaluation**.

## Executive summary

- **5 of 5** employer-specific Ashby public JSON feeds returned HTTP **200** and parseable jobs arrays.
- **292 listed postings** were returned across the five named boards; each board's listed IDs were unique within that board.
- **120 postings** had a parseable `publishedAt` within the preceding 30 days (**41.1%** of these five boards' listed jobs).
- **0 missing/unparseable publication timestamps** were reported.
- **16 records** triggered the script's **contract-like title or employment-type heuristic**, representing **5.5% of the 292**. They are **NOT 16 verified contract positions** and the run did not report how many of the 16 were in the recent-30-day subset.
- **One posting** was explicitly typed `Temporary`; none of the employer feeds' printed type labels included a dedicated `Contract` type.
- This result validates five specific boards on **one day**; it is not evidence of a representative Ashby-wide job inventory or daily new-job counts.

## Exact user-supplied measurements

| Employer board slug | HTTP | Jobs returned | Listed | Unique listed IDs | Published in last 30d | Date unknown |
|---|---:|---:|---:|---:|---:|---:|
| ramp | 200 | 179 | 179 | 179 | 66 | 0 |
| junipersquare | 200 | 52 | 52 | 52 | 22 | 0 |
| greenlight-workforce-solutions | 200 | 23 | 23 | 23 | 13 | 0 |
| coder | 200 | 27 | 27 | 27 | 16 | 0 |
| teamworks | 200 | 11 | 11 | 11 | 3 | 0 |
| **Total** | | **292** | **292** | **292 within-board IDs** | **120** | **0** |

**Employment-type labels from the output:**
- ramp: FullTime 173; Intern 5; Temporary 1
- junipersquare: FullTime 52
- greenlight-workforce-solutions: FullTime 23
- coder: FullTime 27
- teamworks: FullTime 11

**Printed summary:** successful boards 5/5; listed postings 292; published in last 30 days 120; contract title/type signals 16.

## Interpretation relevant to source selection

### Confirmed

1. **Access:** From the user's home network, all five public board endpoints return live JSON successfully without an API key.
2. **Feed breadth across these boards:** At least 292 listed postings can be fetched through five requests, showing useful page-volume efficiency at the individual-board level.
3. **Timestamps and stable identities:** All returned listed postings had parseable `publishedAt` values and each board had unique IDs. This permits a preliminary 30-day count, not a measured day-over-day arrival rate.
4. **Basic employment-type fields exist:** However, the type taxonomy is overwhelmingly `FullTime` in these boards.

### Not confirmed

1. **Provider-wide contract supply:** These five chosen employer boards are not a random sample and are not the whole Ashby marketplace.
2. **Actual contract count:** The 16 signals may include job-title words that are not genuinely contract employment; contracts lacking these exact labels may be missed.
3. **Recent contracts:** No intersection was reported between the 16 contract signals and the 120 recent postings.
4. **Cross-board or cross-provider deduplication:** UniqueIDs was calculated within each board; do not infer that the 292 are deduplicated against other source providers or the same employer posting elsewhere.
5. **Daily reliability/freshness:** A one-day successful fetch cannot demonstrate new jobs per day or successful repeated runs on a later date.
6. **Terms/rate limits:** The five reads worked; this alone does not authorize arbitrary high-volume scraping or prove all publishers' usage rules.

## Recommendation — hardest risk first

**Priority now is measuring access to recent contract-type inventory**, since 80% of the requested initial search allocation is contract-focused and these five boards were dominated by FullTime classification.

1. Repeat the same five-board script on a different day to check access stability and added/removed IDs. Current script prints aggregate counts only, so a true new-ID comparison would require a bounded, non-sensitive ID snapshot for each run.
2. Before expanding to dozens of additional unrelated Ashby employers, test another **public employer-feed family** (Greenhouse, then Lever) and compare obtainable contract-signal counts, date coverage, and ease of scalable employer-board discovery.
3. Use free public feeds first. Preserve Adzuna's limited trial calls for one or two controlled API checks against salary-neutral, contract-filtered searches, after the website proxy research.
4. Keep job-specific relevance, pay, seniority screening and ranking **out of this source-feasibility test**.

**Sprint 1 status:** SOURCE TECHNICAL ACCESS ACHIEVED FOR THESE 5 BOARDS; enough relevant recent contract volume **UNPROVEN**. No production application code written.
