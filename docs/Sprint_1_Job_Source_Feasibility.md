# Sprint 1: Job-Source Feasibility Assessment

**Date:** 2026-11-16
**Status:** IN PROGRESS — official API documentation reviewed; real live responses unverified
**Boundary:** Requirements and feasibility research only; do not build production application components.

## Executive summary

**Provisional recommendation:** Evaluate Adzuna as a broad job search provider, and Greenhouse/Ashby as targeted employer-board sources. Lever is a suitable alternative board provider. Selection is conditional on live data quality, costs, and the user's actual eligibility/search requirements.

## Candidate matrix

| Provider | Access | Coverage | Documented useful attributes | Risk | Status |
|---|---|---|---|---|---|
| Adzuna | Registered app ID/key; free evaluation key per provider terms | Search across employers | Title, company, description snippets, region, salary when reported | Unknown quota/ongoing cost, description quality, duplicate/old listings | Documentation verified; live untested |
| Greenhouse | Public GET job-board endpoints with board token, no GET authentication | One employer board per token | Posting ID, job URL, title, location, optional full content, published/updated date | Cannot search all Greenhouse employers without maintaining board list; salary may be absent | Documentation verified; live untested |
| Ashby | Public employer job-board postings endpoint | One employer board per name | Posting URL, full description, remote/workplace fields, employment type, locations, published date, optional compensation | Requires board-name discovery, varies by employer | Documentation verified; live untested |
| Lever | Public employer-site-specific postings GET in JSON mode | One employer site at a time | Posting ID, plain text description, team, location, workplace type, optional salary range | No cross-employer full-text search; employer list required | Documentation verified; live untested |
| USAJOBS | Registration/API key and identifying user-agent | Federal government roles | Official job search/filter data | Relevance depends on whether user wants government opportunities | Deferred pending eligibility |

## Official source references

- Adzuna search: https://developer.adzuna.com/docs/search
- Adzuna access/keys: https://developer.adzuna.com/overview
- Adzuna terms (personal job search permitted; free key intended for evaluation; higher volumes depend on account): https://developer.adzuna.com/docs/terms_of_service
- Greenhouse Job Board API (public GET; content=true option): https://docs.greenhouse.io/job-board
- Ashby Job Postings API (includeCompensation=true option): https://developers.ashbyhq.com/docs/public-job-posting-api
- Lever postings API (site-specific GET; no global full-text search): https://github.com/Lever/postings-api
- USAJOBS API key authentication: https://developer.usajobs.gov/guides/authentication

These citations establish interface documentation only. They do **not** establish real posting volumes, sufficient relevance, data freshness, or permissible high-frequency usage.

## Live validation attempted, but not completed

| Test | Outcome | Interpretation |
|---|---|---|
| Public Greenhouse sample JSON from web tool | Endpoint inaccessible through tool | No conclusion about Greenhouse uptime |
| Public Ashby sample JSON from web tool | Endpoint inaccessible through tool | No conclusion about returned jobs |
| Public Lever sample JSON from web tool | Endpoint inaccessible through tool | No conclusion about returned jobs |
| One HTTPS Greenhouse request from local runtime | DNS resolution failed in runtime | Restricted environment networking, not API failure |
| Adzuna authenticated request | Not attempted; requires registered credentials | Cannot claim account access, quotas, or live sample |

**No live job counts, measured relevance rates, freshness rates, API response timing or dedup rates are available yet.**

## Proposed source test plan

After user eligibility and representative search terms are confirmed:

1. Select 3–5 representative role-family queries and locations/work arrangements for comparison.
2. Obtain only permitted credentials and verified board names/tokens. Request only a limited sample.
3. Record time, exact query, HTTP status, pages/results, source identifier, and URL.
4. Review 20 results per candidate when available, or all results if fewer; label likely relevant, irrelevant, or uncertain against **approved** user requirements.
5. Measure completeness of title, employer, location, work arrangement, employment type, compensation, posting date, requirements/duties text, and stable identity fields.
6. Open representative employer links and spot-check whether postings remain active.
7. Repeat another day and observe actual new postings and stale content; one sample is insufficient to establish daily newness.
8. Record provider quota, rate restrictions, terms and expected recurring cost from the provider account.
9. Compare overlap across providers; select initial candidates only after results support the decision.

## Candidate acceptance gates — proposed, not approved

- Permitted repeatable automated retrieval for a single person's job search.
- Actual currently available jobs relevant to approved search categories, rather than only successful API calls.
- Sufficient job description to evaluate duties/qualifications; missing fields must be explicit.
- Stable source identities/direct employer URLs to assist deduplication.
- Acceptable ongoing usage limits and costs for daily searches.
- Explicit error reporting; a partial source failure may not masquerade as a complete scan.
- Test sample repeatable and documented in this file with dated evidence.

Numerical thresholds for relevance, volume, and data freshness remain OPEN until user eligibility and actual market supply are established.

## Recommendation tradeoffs

Aggregator-only is broad but dependent on one provider's coverage and snippets. ATS-only provides direct rich job posts but misses companies not in the curated employer list. A small **aggregator + employer-board** combination is the simplest practical trial, subject to successful validation.

## Sprint 1 remaining work

- [x] Identify provider candidates and official interface descriptions.
- [x] Define coverage/cost/field-completeness evaluation protocol.
- [ ] Finalize eligibility profile and representative role queries.
- [ ] Acquire Adzuna access or approve a substitute.
- [ ] Choose representative employers and confirm actual board tokens.
- [ ] Execute successful real API sample calls.
- [ ] Manually inspect posting relevance and completeness.
- [ ] Measure repeated-day freshness and provider overlap.
- [ ] Select two initial sources and document an evidence-backed recommendation.
