# Sprint 1 — Feed Access and Volume Validation Plan v1.1

**Revised:** 2026-11-17  
**Status:** FEED-ONLY FEASIBILITY TEST — user scope correction  
**Supersedes:** the earlier ten-query posting suitability plan for current Sprint 1 testing. The prior test cases are historical research, not current acceptance evidence.

## Executive Summary

**Current question: Can we programmatically obtain enough job postings, regularly and legally, through feeds/APIs to support a useful local job-discovery agent?**

We are **not** looking for attractive jobs for the user now. We are **not** scoring suitability, applying salary/experience exclusions, or asking whether a sample posting deserves a recommendation. Individual job web pages and search-engine snippets **do not count as successful feed access**.

## Feed-only measurement criteria

For each source record:

| Dimension | What to measure | Pass/fail caveat |
|---|---|---|
| Direct programmatic access | An actual HTTPS feed/API response (endpoint, status, timestamp, auth conditions) | Documentation or browser-rendered posting does not qualify |
| Volume | Total distinct IDs returned, pages/cursors available, number obtainable within terms/quota | A provider-wide advertised total is **not** the accessible relevant inventory |
| Freshness | Number with **original publication date within last 30 days**, where available; distinguish updated/ingested date | Missing original date = UNKNOWN, never guessed |
| Basic discoverability | Broad project/program/product and PMO/portfolio title or keyword counts, when feed supports them | Counts only; **no per-job fit or pay review** |
| Geography & work type metadata | Whether filters/fields exist for Atlanta/local/hybrid/remote, US/CA/MX, contract/full-time | Assess capability and field presence, not personal eligibility |
| Repeated access | Same bounded feed request repeated on a different day | One successful call is a technical proof, not daily reliability |
| Stable identity | Presence of employer, title, posting ID or canonical URL | Determines whether aggregate unique count can be trusted |
| Cost/permission | Permitted automated access, key requirements, rate limits, attribution and ongoing fees | Personal free-first requirement remains |

**Result levels:**
- **PASS — accessible:** The feed/API returns parseable actual posting data.
- **VOLUME EVIDENCE:** Count of accessible postings, unique IDs and 30-day original-date subset measured with enough paging.
- **PASS — enough supply:** Volume is observed across broad relevant role families and geographic types, with repeatability and acceptable permission/cost. Numerical sufficiency threshold should be justified **after measuring** real supply; don't invent a magic number.
- **BLOCKED / UNVERIFIED:** No usable direct API response in the testing environment; do not call the provider broken.
- **NOT TESTED:** No bounded attempt made.

## Source test matrix

| Candidate feed | Role in source mix | Current proven state | Remaining feed-only test |
|---|---|---|---|
| Ashby public job-board API | Multiple employer-specific feeds | **Five of five public boards succeeded locally (HTTP 200): 292 listed posts, 120 published in last 30 days, 0 unknown dates; 16 contract title/type signals not confirmed contracts** | Establish recent true contract inventory, repeat-day stability, and wider employer-board coverage; see [Ashby measurements](./Sprint_1_Ashby_Feed_Volume_2026-11-17.md) |
| Himalayas public jobs API | Broad remote jobs feed | **One unfiltered 20-posting JSON page returned**; API advertised a much larger total | Page/keyword/country/employment-type filtered count, date semantics, duplicate identities and daily access |
| Greenhouse public Job Board API | Multiple employer-specific feeds | **Five of five public boards passed locally (HTTP 200); 721 jobs, 346 first published within last 30 days, 175 broad role-title signals; 254 unverified contract signals (250 INFUSE)**; [measured results](./Sprint_1_Greenhouse_Feed_Volume_2026-11-17.md) | [Targeted recent ∩ role ∩ contract signal script committed](../scripts/feasibility/test_greenhouse_contract_overlap.ps1), awaiting local execution; audit INFUSE metadata/locations and later repeat-day IDs |
| Lever public postings API | Employer-specific feed | Individual job page evidence only; **JSON API unverified**; [five-board paginated local probe committed](../scripts/feasibility/test_lever_feed_volume.ps1) | Run read-only test locally to measure unique post IDs, explicit contract commitment vs title-only hints, role/contract overlap, and createdAt age (NOT first publication); check US/remote metadata and page completeness |
| Adzuna search API | Broad local/hybrid + non-remote coverage | Official docs/terms found; **requires evaluation credentials; no call tested** | Request developer key, observe query counts, volume, pagination, and limits |
| Additional keyless remote feeds | Backup for broad remote volume | Documentation for some; no reliable filtered data volume yet | Only if above sources insufficient |

## Proposed minimal trial

1. **One live GET from each accessible public provider**; record date/time, response status and format. Record failures and environment limitations.
2. **Sample three to five employer boards** for each employer-specific ATS provider. Count posting IDs rather than assess whether postings are good for the user.
3. For broad aggregators, request **bounded sample pages** for broadly named Project Manager, Program Manager, Product Manager and PMO roles, across US/local and remote slices where supported. Count only.
4. Measure total accessible postings, duplicates/overlap, structured work-type/location availability and **true original 30-day age** where supported.
5. Repeat one day later for rate stability and new IDs. Do not build a production connector, dashboard or database as part of this test.
6. Report a comparative volume/coverage/access/cost table and recommend minimal starting feed combination.

## Explicitly deferred work

- Individual job suitability judgments; compensation and qualification gap screening.
- Rejection decisions and AI ranking.
- Career map or career exploration effectiveness.
- Daily digest and dashboard behavior.
- Job-specific human-readable HTML page hunts.

Your confirmed 80% contract/20% full-time strategy is **a future search allocation requirement**, not a reason to spend Sprint 1 manually finding good individual jobs.

## Exit gate

**Sprint 1 feed-validation is complete only when we can show actual repeatable direct-feed access and measured counts sufficient to plausibly supply the daily discovery pipeline**, with documented access costs, restrictions and data age limitations. A source that only has published web pages but no verified accessible feed stays UNVERIFIED.

**No production implementation authorized.**
