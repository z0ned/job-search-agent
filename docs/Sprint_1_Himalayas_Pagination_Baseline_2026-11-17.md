# Sprint 1 — Himalayas Filtered Pagination and First GUID Baseline (2026-11-17)

**Status:** PAGE-TWO PAGINATION PASS, filter sanity check PASS, rolling baseline CREATED. Day-over-day change measurement is **pending**.

**Execution:** User-run Windows PowerShell on **2026-11-17 at 18:41:13 UTC** using `scripts/feasibility/test_himalayas_daily_delta.ps1`. Four unauthenticated GET requests, two pages each for Project Manager and Program Manager. No Adzuna calls.

## Executive summary

- Pages 1 and 2 each returned 20 records for both role searches.
- **40 distinct GUIDs within each query**; no duplicate GUID between pages 1 and 2 of a single query.
- **71 distinct GUIDs across the two queries** out of 80 total appearances; **9 GUIDs were present in both queries**.
- All sampled employment types were Contractor or Temporary, and all sampled location restrictions were explicitly U.S. (no worldwide or disallowed-country cases in this batch).
- All 80 sampled postings had parseable `pubDate` last-update timestamps, and all 80 were last updated within 30 days. **`pubDate` is NOT a first-publication date** and must not be described as newly published postings.
- Initial GUID-only snapshot saved locally under `.local-test-data/himalayas_pm_contract_page_samples.json`, ignored by the repository's `.gitignore`. No posting descriptions or credentials were written.

## Actual measurements

| Query | Provider-reported matches | Page 1 | Page 2 | Unique GUIDs per query | U.S.-restricted | Worldwide | Role-title keyword matches | Known update dates | Updated last 30d |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Project Manager | 231 | 20 | 20 | 40 | 40 | 0 | 13 | 40 | 40 |
| Program Manager | 131 | 20 | 20 | 40 | 40 | 0 | 18 | 40 | 40 |
| **Combined** | **DO NOT SUM COUNTS** | **40** | **40** | **71 across-query distinct** | **80 appearances** | **0** | **31 appearances** | **80** | **80** |

**Method:** Same `country=US`, `employment_type=Contractor,Temporary`, `sort=recent` filters on both pages. Country and type were validated for each returned posting. API reported totals are not full downloaded inventories. Zero duplicate GUIDs *within* each search; **nine overlapping GUIDs across searches**.

## What remains unverified

1. **Day-over-day new-to-sample GUIDs.** The first run created the reference snapshot; no day-two comparison has yet occurred.
2. **True newly posted opportunities.** Because results are sorted by last update and only the first 40 per query were captured, a GUID entering the sampled window can simply be an existing listing that was edited or moved in ranking.
3. **Accessible volume beyond page 2.** Pages 3+ and the full 231/131 reported match inventories have not been verified or deduplicated.
4. **U.S. employment eligibility and roles.** Country restriction metadata does not prove an employer will engage a Georgia-based worker; role title keyword signal is not eligibility/fit assessment.
5. **Repeatability and terms.** Only a single-day set of API calls has been observed for this pagination script.

## Next action

From the same cloned repo root on or after **2026-11-18 18:41 UTC** (at least 24 hours after baseline), run:

```powershell
powershell -NoProfile -File .\scripts\feasibility\test_himalayas_daily_delta.ps1
```

Then record the **new-to-top-40 GUIDs**, **no-longer-in-top-40 GUIDs**, **reported search count deltas**, **hours since baseline**, and whether the local baseline advanced. Avoid calling those deltas true new vacancies until origin/publication metadata or a wider feed ID comparison supports that claim.

The 24-hour repeat is a **manual source validation** step, not a background job or automation.

**Current Sprint 1 conclusion:** Himalayas country/contract filtered search and 1→2 pagination are technically demonstrated. Sustainable daily supply of genuinely new U.S.-eligible contract opportunities remains unproven.
