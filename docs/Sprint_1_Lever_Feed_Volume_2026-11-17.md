# Sprint 1 — Lever Direct Feed Access, Contract Signals and Volume (2026-11-17)

**Status:** FIVE-BOARD PUBLIC API ACCESS PASS; observed small U.S.-labeled recent-created target-role contract supply in selected boards; sufficient daily contract supply NOT YET PROVEN.  
**Execution:** User-run Windows PowerShell on **2026-11-17 17:18:37 UTC**, using `scripts/feasibility/test_lever_feed_volume.ps1`.  
**Access:** Lever public postings endpoint `GET /v0/postings/{board}?mode=json&limit=100&skip=0`; no authentication or Adzuna calls.  
**Scope:** Source/feed feasibility ONLY; no evaluation of specific jobs or applicant suitability.

## Executive summary

- All **5/5** named employer posting feeds responded **HTTP 200** and returned valid JSON arrays. The `lever` employer board had **zero postings**, which is an accessible empty board, not an API failure.
- **111** postings returned, all with **111 distinct posting IDs within their respective boards**, no missing IDs and no repeated IDs.
- **111/111** had a readable `createdAt`; **40/111** were created within the previous 30 days. **`createdAt` is not a verified first-publication date** and therefore this does not establish 40 new published jobs.
- **23** titles matched a broad project/program/product/portfolio/PMO/transformation/delivery term.
- **15** postings had **explicit contract-like `categories.commitment` labels**, and **3 additional title-only contract hints** (weaker signals).
- **4** postings had the triple intersection **recent `createdAt` AND target-role-title signal AND explicit contract commitment**; **2** of these had `country=US` and `workplaceType=remote`. This is **not confirmed U.S. hiring eligibility**.
- No board required more than one page of 100 results. `lever` successfully returned an empty array. Selected employer boards were deliberately contract-biased; they are not a random Lever sample.

## User-reported results

| Board token | HTTP | Returned/unique | Created within 30 days | Role title signals | Explicit contract commitment | Title-only contract hint | Recent-created + role + explicit contract |
|---|---:|---:|---:|---:|---:|---:|---:|
| lever | 200 | 0 | 0 | 0 | 0 | 0 | 0 |
| pointclickcare | 200 | 87 | 36 | 14 | 5 | 3 | 3 |
| idealistconsulting | 200 | 6 | 0 | 1 | 3 | 0 | 0 |
| compassx | 200 | 11 | 4 | 5 | 3 | 0 | 1 |
| protrials | 200 | 7 | 0 | 3 | 4 | 0 | 0 |
| **Total** | | **111** | **40** | **23** | **15** | **3** | **4** |

The script reported **four** recent-created+role+any-contract matches, exactly the same four as the explicit-commitment intersection; no extra title-only cases qualified as recent-role.

### Geography and workplace in the recent-role-contract intersection

| Board | Triple-overlap | `country=US` | `country` unknown | `workplaceType=remote` | US + remote |
|---|---:|---:|---:|---:|---:|
| pointclickcare | 3 | 1 | 0 | 2 | 1 |
| compassx | 1 | 1 | 0 | 1 | 1 |
| **Total** | **4** | **2** | **0** | **3** | **2** |

**Caution:** Other 2 postings had a non-US country code; not included as U.S. contract supply. None has been checked for actual availability, eligibility of a Georgia resident, compensation, or skills; these checks are deferred. A `remote` label alone does not guarantee U.S. work location.

### Source-provided commitment labels (not inferred from title)

- lever: no active postings
- pointclickcare: **Contract 5; Full-Time 82**
- idealistconsulting: **1099 Contract Part-Time 1; Contract 2; Full-Time 3**
- compassx: **Contract 3; Full-Time 8**
- protrials: **Contract 4; Full Time 3**

### Workplace labels

- pointclickcare: hybrid 36; remote 51
- idealistconsulting: remote 6
- compassx: hybrid 8; remote 3
- protrials: remote 7

## Comparison with earlier source tests

| Provider | Boards tested | Accessible listings | Age-related metric | Contract-role intersection |
|---|---:|---:|---|---|
| Ashby | 5 | 292 | 120 with `publishedAt` in 30 days | Not measured; 16 broad contract signals, unverified |
| Greenhouse | 5 | 722 on second run | 347 with `first_published` in 30 days | 63 recent + role + contract signals, all INFUSE; 250 INFUSE contract-type labels are non-US/UA contractors |
| Lever | 5 | 111 | 40 with **`createdAt`** in 30 days, **not verified publication** | 4 recent-created + role + explicit contract; **2** US-country + remote |

**Do not sum volumes as a daily job-discovery estimate.** These employer-specific samples are selected, no repeat-day new-ID deltas have been measured, cross-source deduplication is not done, and date semantics differ.

## Risk and interpretation

1. Lever is **technically feasible**, including read-only, keyless access with distinct job IDs, employment-type field and simple paging.
2. Explicit commitment classifications are **better evidence** than job-title string matches; still do not guarantee a role is eligible for the user's circumstances.
3. `createdAt` refers to posting creation, **not necessarily when it became externally visible**, so it cannot replace original publication date for a 30-day *new-posting* audit.
4. The sampled boards produce only **two US-country + remote candidates** in the recent-created + target-role + contract bucket. That is **supply evidence, not a rejection of Lever as a platform**.
5. A five-employer sample is not representative of Lever; selection deliberately included consulting, contract and health-oriented boards.

## Recommendation and next steps

**Before expanding more boards arbitrarily, quantify broad remote U.S.-hire contract inventory from an aggregator**—starting with the already accessible Himalayas JSON API—and compare data field availability, filter count and accessible unique IDs. This targets the highest-risk gap: not raw job volume, but job feed volume that can plausibly yield U.S.-eligible project/program manager contracts. Test a small 7/30-day query window using its date semantics carefully (`pubDate` may be update date, not first publication). After aggregators, decide whether systematic employer-board discovery is worth a dedicated sprint. Reserve Adzuna test calls, and continue to defer individual job suitability analysis and production implementation.
