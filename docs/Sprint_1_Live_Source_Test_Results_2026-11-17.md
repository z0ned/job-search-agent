# Sprint 1 — Live Source Feasibility Test Results

**Test date:** 2026-11-17  
**Status:** PARTIAL — One direct employer API feed was successfully retrieved; other sources need validation from a network-enabled environment.  
**Source requirements:** [Source test portfolio](./Sprint_1_Source_Test_Search_Plan.md), [Eligibility decisions](./Sprint_1_Eligibility_Decisions_v1_0.md).

## 1. Executive Summary

**Ashby — single-board technical PASS:** Actual JSON returned from the Ramp employer board, including posting IDs, title, employment type, full description, location, workplace type, posting date, job/apply URLs and structured compensation for some jobs. This does **not** demonstrate comprehensive or representative user-relevant coverage.

**Greenhouse — individual live-looking job pages inspected, API feed access UNVERIFIED:** Actual postings can be read on the hosted job board. Direct JSON feed requests failed in the restricted test environment.

**Lever — an individual employer-hosted application page was readable, API feed access UNVERIFIED.**

**Adzuna — personal job search is permitted in official terms; API key is required; no credentialed test was performed.** Official terms say free key is for evaluation, higher-volume plans depend on account and attribution obligations apply.

**Himalayas — promising additional keyless remote-job API:** Official documentation currently allows filtered keyword/country/employment-type search with no key, once-per-day refresh, and attribution. Direct API search requests were inaccessible here, so relevance and actual counts remain UNVERIFIED.

## 2. Endpoint Test Log

These were bounded public read-only GETs through available browsing. The browser does not reliably expose HTTP status for every success. Tool restrictions do not prove upstream API failure.

| Provider / endpoint | Observed response | Evidence classification |
|---|---|---|
| Ashby https://api.ashbyhq.com/posting-api/job-board/ramp?includeCompensation=true | **JSON returned**; actual jobs and structured pay visible | One successful employer feed |
| Ashby https://api.ashbyhq.com/posting-api/job-board/ramp | **JSON returned** | Optional compensation comparison |
| Ashby https://api.ashbyhq.com/posting-api/job-board/ashby | Failed due to **4 MiB tool response-size cap** | Large board cannot be inspected here; not an API-outage claim |
| Ashby public boards 829studios, leavitt, vultr, junipersquare | Not accessible through browser data tool | Unverified |
| Greenhouse https://boards-api.greenhouse.io/v1/boards/gitlab/jobs?content=true | Tool could not access JSON | Unverified |
| Greenhouse https://boards-api.greenhouse.io/v1/boards/vercel/jobs?content=true | Tool could not access JSON | Unverified |
| Lever https://api.lever.co/v0/postings/lever?mode=json | Tool could not access JSON | Unverified |
| Himalayas https://himalayas.app/jobs/api/search?q=project%20manager | Tool could not access JSON | Unverified |
| Himalayas keyword variants program manager, PMO | Tool could not access JSON | Unverified |
| Remotive and Jobicy filtered JSON requests | Tool could not access JSON | Unverified |
| Adzuna credentialed search | Not attempted; no API key | Pending |
| Local Python request to public Greenhouse API | DNS resolution failed in restricted local runtime | Environmental network limitation |

No overall listing count, provider relevance rate, uptime rate, or 2-day freshness is claimed.

## 3. Actual Structured Ashby Evidence — Ramp

Tested endpoint: https://api.ashbyhq.com/posting-api/job-board/ramp?includeCompensation=true

The JSON visibly included: id, title, department, employmentType, location, secondaryLocations, publishedAt, isListed, isRemote, workplaceType, jobUrl, applyUrl, descriptionHtml, descriptionPlain and optional compensation with pay period, currency, numeric minimum and maximum.

**Three deliberately handpicked rule-test examples, not a representative sample:**

| Observed posting | Data confirmed in JSON | Conclusion |
|---|---|---|
| Senior Technical Program Manager (ID 8be55ffc-d512-4ef3-a14d-3a4cb29a60d4) | Published 2026-10-16; NYC HQ; FullTime; isRemote true but workplaceType **Hybrid**; multiple location-specific salary tiers | Not 100% remote. Also **older than 30 days** as of 2026-11-17; exclude from initial new-source 30-day intake, unless a later policy explicitly permits |
| Product Manager, Growth (ID e0b64893-0459-4d84-ac4f-7b50966ef024) | Published 2026-10-06; NYC onsite; FullTime | Location not eligible as a local commute; outside initial 30-day intake |
| Customer Activation Manager, Public Sector (ID 574f46a4-42b2-46be-ba5c-de07c5e173c5) | Published 2026-11-12; FullTime; SF + remote US secondary; salary example $100k–$155k annual USD | Within 30-day lookback but **below confirmed $180k full-time base threshold**; also not target leadership role |

**Critical source warning:** Ashby documentation says isRemote=true can mean either Hybrid or Remote. Use workplaceType rather than the boolean alone. Location-specific compensation and secondaryLocations also require source-aware handling. An unlisted posting (isListed false) is direct-link-only under the provider documentation.

## 4. Public Job Pages Inspected (NOT equivalent to API-feed success)

| Provider | Employer / posting | Facts visible on publisher's page | Suitability test finding |
|---|---|---|---|
| Greenhouse | [OpenMined — Senior Technical Program Manager](https://job-boards.greenhouse.io/openmined/jobs/4478254009) | Roughly full-time independent contractor, 12-month initial term, remote/Eastern-hours, $127k–$159k **annualized contractor fee** paid monthly; 7+ years technical PM; demanding AI-native and technical background | Promising contract category but compensation is **not stated hourly**. Don't invent hours-equivalent pay; flag skills for manual qualification clarification |
| Greenhouse | [INFUSE — Senior Project Manager, Remote, Contract](https://job-boards.greenhouse.io/infuse/jobs/4748221005) | Title explicitly says remote/contract; location **Portugal** | Cross-border false positive if remote is interpreted as available to a US-based worker; requires employment jurisdiction check |
| Greenhouse | [Crunchyroll — Director, Global PMO](https://job-boards.greenhouse.io/crunchyroll/jobs/8248396) | PMO leadership role, Los Angeles posting; senior leadership duties | Functional full-time fit, but outside ordinary commute/TN relocation; remote not verified. Do not claim eligible automatically |
| Lever | [Idealist Consulting — 1099 Enterprise Project Manager](https://jobs.lever.co/idealistconsulting/a24ec4e5-5caa-473d-abd4-b71f09a8167b/apply) | Chicago listed; contract; remote; application asks deep Salesforce experience; rate not visible on inspected page | Demonstrates 1099 candidate and requirement gaps. Confirm jurisdiction, rate and qualifications; not a finalized recommendation |

These are **diagnostic examples**, intentionally chosen to exercise edge cases. They cannot be used to calculate a statistically meaningful relevance rate. For these individual HTML pages, posting timestamps were not consistently visible and **the 30-day ingestion rule cannot be verified** from index/crawl dates alone.

## 5. Official Terms and Technology Findings

- [Adzuna terms](https://developer.adzuna.com/docs/terms_of_service): personal search permitted; free evaluation key, account-specific limits/paid plans; attribution requirements.
- [Greenhouse public job-board API](https://docs.greenhouse.io/job-board): public GET, employer board token, content=true full posting option.
- [Ashby public postings API](https://developers.ashbyhq.com/docs/public-job-posting-api): public GET, optional compensation, employmentType, workplaceType, posting dates, full description.
- [Lever published postings API](https://github.com/lever/postings-api): employer-site-specific public read interface.
- [Himalayas public jobs API](https://himalayas.app/api): keyless filtered remote jobs, optional free key for higher limits; published terms require visible attribution and supplied application link, no onward job redistribution. [Detailed docs](https://himalayas.app/docs/remote-jobs-api) say cache refreshes about every 24 hours.
- [Remotive remote jobs API](https://remotive.com/remote-jobs/api): additional keyless remote-only candidate, not yet validated; review API terms and staleness.

## 6. Design Consequences

1. Apply the **initial 30-day lookback independently to each newly added job source**, using source-published dates, not crawl/index timestamps.
2. Differentiate **remote, hybrid, and geographic hiring eligibility**. A remote boolean alone is unsafe.
3. Preserve salary currency and period; hourly contract floors cannot automatically be compared to annualized contractor fees without hours assumptions.
4. Display qualifications that need verification, rather than silently rejecting or inventing credentials.
5. Apply Regions/Invesco hard exclusion, 80% contract/20% full-time test mix, and confirmed commute/relocation rules.
6. Keep original job URLs/IDs and observation dates to prevent repeat new-job emails.
7. Preserve the precise commute origin only in local private configuration, never in the public repo.

## 7. Recommendation and Next Verification Step

**Recommended next trial:** Combine a keyless **Himalayas remote-source** search with employer-board tests on **Ashby and Greenhouse**; also provision the free **Adzuna evaluation key** for broad local/hybrid searches. A remote-only source is **not** a substitute for Atlanta onsite/hybrid coverage.

We have one successful source API response, but **not two independently validated API feeds**, not measured search coverage or relevant-job count, and not a second-day freshness check. Do not approve production adapters or declare Sprint 1 completed yet.

To complete the missing access tests, use limited read-only HTTPS GETs on a network-enabled home computer or suitable test environment, with API keys held in local environment variables. One-off feasibility commands are acceptable; production source adapters, SQLite, dashboards and schedulers are not yet authorized.

## 8. Sprint Exit Criteria

- [x] Research official provider docs/terms.
- [x] Confirm at least one structured first-party employer API can return real jobs.
- [x] Inspect public real job pages from other sources for missing-field/eligibility edge cases.
- [x] Find keyless broad-remote data candidate.
- [ ] Validate a second independent API feed with real results.
- [ ] Measure role-specific volume, field completeness, relevant postings and repeat-day freshness.
- [ ] Verify Adzuna credential access or alternative broad local source.
- [ ] Review material eligibility edge cases and approve initial source set.

**Status: IN PROGRESS; no production application code added.**
