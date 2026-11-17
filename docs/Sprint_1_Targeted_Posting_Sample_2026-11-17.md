# Sprint 1 — Targeted Job-Posting Source Sample

**Test date:** 2026-11-17 (one-day snapshot)  
**Status:** PARTIAL SOURCE-FIT TEST, NOT PRODUCTION SOURCE ACCEPTANCE  
**Objective:** Compare ten user-derived search categories (**8 contract / 2 full-time**), test eligibility logic on actual employer-hosted descriptions, and identify remaining provider API barriers without writing product code.

## 1. Executive Summary

A bounded search across Greenhouse, Ashby, and Lever-hosted listings surfaced **relevant-looking job-page examples** in both tracks. We manually assessed one diagnostic posting per test slot. This is **purposive diagnostic sampling, not a representative API search result set**. No reliable per-query recall, source completeness, or per-day volume percentage can be calculated from a web-index sample.

**Critical distinction:** We were able to open and read several employer-hosted Greenhouse posting HTML pages, but direct **Greenhouse JSON API** requests still were not accessible here. Ashby/Ramp and Himalayas provided structured JSON in the earlier same-day feasibility test; Ashby individual job pages sometimes render no readable body in this browser. Lever individual pages or JSON requests may return 403. A readable/ indexed employer page is *not* proof that daily automated API retrieval succeeds.

## 2. Search slots and observed example postings

The question is whether the sources contain *test cases to exercise eligibility*, not whether the displayed roles should be emailed to the user now.

| Slot | Search family | Employer posting tested | Source evidence | What the example teaches | Provisional interpretation |
|---|---|---|---|---|---|
| C1 | Contract Project Manager | [Radicle Health — GovRAMP Project Manager (Contractor)](https://job-boards.greenhouse.io/radiclehealth/jobs/5284661007) | Direct Greenhouse HTML read: remote; 12-month contract-to-hire possibility; **$72/hour**; **5+ years** PM | Strong evidence of an execution-focused regulated-technology contract with pay above the floor | **Potentially eligible**, subject to posting age / work eligibility / other facts |
| C2 | Contract Program Manager | [EnergyHub — Launch Program Manager (Contract)](https://job-boards.greenhouse.io/energyhub/jobs/8928138002) | Direct Greenhouse HTML: US remote; **1099**; six months; **$55–$65/hour**; 6+ years | Strong role relevance can coexist with a **confirmed pay hard-fail** | **EXCLUDE**, top of posted hourly range is below $70 |
| C3 | Technical PM contract | [Reactivate — Temp Technology Project Manager](https://job-boards.greenhouse.io/reactivate/jobs/4725311006) | Direct Greenhouse HTML: remote; six months; **$75–$100/hour**, but **3–4 years required** | Pay passes, yet requirement looks junior against user's stated intent to eliminate 3-year jobs | **JUNIOR / SCOPE REVIEW**, not a verified good recommendation |
| C4 | IT/Technical PM contract | [Linda Werner & Associates — Technical Project Manager III, Infrastructure & Capacity](https://job-boards.greenhouse.io/lindawernerassociates/jobs/5441843008) | Direct Greenhouse HTML: US remote; **40 hours/week**, 6+ month contract; rate not stated; specialized data-center/hardware duties | Workload/schedule matches, but pay UNKNOWN and specialized technical qualifications need a gap check | **INCLUDE WITH PAY + SKILL WARNINGS** |
| C5 | Banking / finance PM contract | [EQ Bank — Senior Technical Program Manager (18-Month Contract)](https://jobs.lever.co/eqbank/13c7317a-cab0-4083-a9ec-7f3aa2b0c819) | Lever indexed title/summary only; direct page returned 403 in this environment | Evidence of a relevant banking contract title, but cannot verify jurisdiction, salary, posting date or full duties from this source | **INSUFFICIENT EVIDENCE**; do not count as validated eligible |
| C6 | Contract Product Owner | [Beyond Sports — Product Owner, Contractor](https://jobs.ashbyhq.com/wearebeyondsports/c7fae5a2-7b06-463f-86e5-b90366204f52) | Ashby indexed title/remote/contract snippet; direct page returned minimal JavaScript shell | The title exists in a first-party ATS index, but rate, US hiring eligibility and original posting date unverified | **INSUFFICIENT EVIDENCE** |
| C7 | Contract Product Manager | [Parsley Health — Fractional Growth Product Manager (1099)](https://job-boards.greenhouse.io/parsleyhealth/jobs/8202839003) | Current Greenhouse HTML opened via employer's listing: **$130–$200/hour**, **~20 hours/week**, 3 months, US remote | High hourly pay passes; hours differ from ~40-hour preference; growth experiment/product specialty has gaps; **older indexed job ID redirected to the board** | **ELIGIBLE ON RATE; lower workload preference fit / skills to review** |
| C8 | Regulatory technology / compliance PM contract | [Linda Werner & Associates — Technical PM III, Legal/Privacy/Compliance](https://job-boards.greenhouse.io/lindawernerassociates/jobs/5471169008) | Direct Greenhouse HTML: US remote; 3+ month contract; **40 hours/week**; 5+ years required; hourly pay not stated | Highly relevant compliance and formal-approval work, schedule fits, pay UNKNOWN | **INCLUDE WITH PAY-UNSPECIFIED WARNING** |
| F1 | PMO Director / Head of PMO | [Juniper Square — Director, PMO (Engineering)](https://jobs.ashbyhq.com/junipersquare/bd8dc231-abb8-48ac-9569-85ca36c3644f) | Employer Ashby page indexed with **$200k–$250k US base**, remote options, PMO scope; direct page body unavailable in current browser | Matches full-time target track and salary; remote jurisdiction and posted age need source-API confirmation | **PROMISING, API VERIFICATION PENDING** |
| F2 | Portfolio / technology leadership | [Kura Oncology — Associate Director/Director, IT](https://job-boards.greenhouse.io/kuraoncology/jobs/6184395004) | Direct Greenhouse HTML: remote; Associate Director **$186k–$218k base**, Director **$221k–$259k base**; IT portfolio and AI governance work | Both levels clear full-time salary floor; drug-development validation/GxP experience is a qualification gap to verify | **PROMISING FULL-TIME ADJACENT**, subject to age/experience checks |

### Evidence hierarchy

- **Direct readable employer page:** C1, C2, C3, C4, C7, C8, F2 (7 cases).
- **Indexed employer ATS summary, direct content not readable by this environment:** C5, C6, F1 (3 cases).
- **Source API collection validation:** None of these ten results is currently backed by a successful **query-specific** job-source API response in this turn. The separate [Live Source Test Results](./Sprint_1_Live_Source_Test_Results_2026-11-17.md) confirms public Ashby/Ramp and unfiltered Himalayas API JSON only.
- **Source publication age:** Genuine original posting dates could **not** be verified for these ten from their full employer pages. A crawler date, a “New” badge, or an aggregator's discovered date is **not** adequate proof of the 30-day first-import rule. The third-party-reported October dates for F1 are suggestive, not first-party validated.

## 3. Specific newly observed edge cases

### 3.1 Contract compensation: hard failure vs attractive role

EnergyHub's Launch Program Manager covers client-facing integrations, governance and program launches; nevertheless, it explicitly offers $55–$65/hour on 1099, which is below the $70/hour contract hard minimum and should be excluded. Radicle offers $72/hour, 5+ years and a project delivery role with compliance work, so it is a much stronger preliminary match.

### 3.2 Experience rule and junior titles

Reactivate's well-paid PM contract explicitly requires **3–4 years**. The user said the experience filter exists to eliminate junior jobs “e.g. minimum 3 years.” Therefore do not count Reactivate as a strong eligible example merely because the pay passes. Preserve the exact experience requirement and make seniority interpretation an explicit rule-design review item; a role's nontrivial duties can provide context but should not silently override the user's anti-junior instruction.

### 3.3 Preferred contract workweek vs high-paid fractional opportunities

Parsley Health's refreshed board has a live new requisition for a fractional 1099 Product Manager, $130–$200/hour, approximately **20 hours/week**. This passes the stated hourly threshold and Product Manager experience exemption, but differs from the user's expressed approximately 40-hour-week goal. No **hard 40-hour minimum** was approved. Rank with workload caveat rather than inventing a rejection.

The older indexed Parsley job ID (7753967003) redirected to the employer's current board, whose live listing link points at **8202839003**. This demonstrates that **index search hits can be stale even when a similar role is still published**. Do not assume two IDs are identical requisitions without employer evidence.

### 3.4 Full-time salary and qualifications

Juniper Square's PMO Director has indexed U.S. base salary $200k–$250k and fits the full-time leadership target. Kura Oncology explicitly lists Associate Director $186k–$218k and Director $221k–$259k base for an IT portfolio/AI leadership position. Both clear the full-time **base** floor. Kura also requires pharmaceutical industry/GxP compliance and general IT leadership; these must be shown as possible qualification gaps without inventing experience.

### 3.5 Remote is not hiring jurisdiction

A remote-labeled role can be restricted to an excluded country or to particular US states. Canada and Mexico appear in the user's source-search scope; this does **not** establish eligibility to perform foreign onsite work or that an employer will hire a Georgia-based resident. Preserve country and compensation currency. TN relocation remains a separate exception only.

## 4. Source completeness and accessibility (this test only)

| Source | Public board/example evidence | Actual API evidence so far | What remains |
|---|---|---|---|
| Greenhouse | 7 directly readable pages in the ten-slot sample | Direct JSON GET still inaccessible here | Confirm authenticated? No; public GET is documented, but direct endpoint must be fetched from network-enabled machine |
| Ashby | 2 indexed job summaries here; direct JS pages not readable | **Ramp board JSON succeeded** in earlier test; one employer | Verify C6/F1 via board API on connected machine and assess broader boards |
| Lever | 1 indexed job summary; direct employer page 403 | Direct feed JSON not yet accessible | Verify source GET from connected environment and employer job ID |
| Himalayas | Broad unfiltered API feed, not used as a source for any of the ten targeted page examples | **Unfiltered JSON succeeded** earlier; query-specific requests inaccessible | Confirm q/employment_type/country filtering and rank match quality |
| Adzuna | Public API docs and personal-search terms | Credentialed search not yet run | Registered evaluation app ID/key; quota and permitted ongoing use |

A deliberately selected ten-slot diagnostic sample **cannot** justify a 70% source relevance score merely because seven pages were readable. Readability is a technical feature, not job suitability; query discovery through a search index is not API search coverage.

## 5. Provider and architecture recommendations

**Recommendation:** Continue evaluating **Greenhouse public employer-board feeds**, **Ashby employer feeds**, and **Himalayas remote-only discovery**, while seeking an accessible **broad Atlanta/local source** (Adzuna after key provisioning). These are *candidate* integrations, not production approvals.

The most useful source-quality fields identified from employer postings are:
- Required experience years plus qualitative role scope.
- Employment structure W-2/1099/contract-to-hire and stated weekly hours.
- Salary min/max, currency, period and **base-vs-variable compensation** distinction.
- Workplace arrangement, exact remote days, country hiring authorization and office address.
- Posting/req identity, original publication date, last-updated date and source URL.
- Requirements evidence and qualification gaps with later user-confirmed facts.

## 6. Outstanding Sprint 1 exit gates

- [x] Ten source-testing categories (8 contract, 2 full-time) have at least one diagnostic example, with source-evidence tier recorded.
- [x] Salary pass/fail, junior-scope caution, and 20-hour fractional-workload caution tested on real posting text.
- [x] Two independent **unfiltered** structured public API feeds previously retrieved (Ashby and Himalayas).
- [ ] Run actual **source API queries** for each of the 10 categories; record returned counts and per-query precision manually.
- [ ] Prove original posting age ≤30 days for each newly activated source; do not replace date with last-updated/crawl date.
- [ ] Verify reliable public Greenhouse and Lever JSON access outside this tool environment.
- [ ] Obtain or explicitly waive Adzuna free key and validate Atlanta onsite/hybrid source.
- [ ] Compare repeating the same live queries on a second date; no one-day shortcut constitutes this check.
- [ ] Approve final initial source set and residual eligibility edge cases.

**Sprint 1 remains IN PROGRESS. No product code or database implementation has been added.**
