# Sprint 1 — Job Source Test Search Plan v1.0

**Date:** 2026-11-17  
**Status:** Proposed testing portfolio. **No live provider results, relevance percentages, or freshness figures claimed yet.**  
**Evidence basis:** [User questionnaire](./Sprint_1_Remaining_Decisions_Questionnaire.md) and [eligibility decisions](./Sprint_1_Eligibility_Decisions_v1_0.md).

## Recommended 10-query test allocation

The **confirmed 80% contract / 20% full-time** division governs the initial validation workload, not final recommendation counts or career exploration.

| Slot | Track | Representative search phrase | Evaluation focus |
|---|---|---|---|
| C1 | Contract | Project Manager | Conventional 40-hour execution roles |
| C2 | Contract | Program Manager | Cross-functional delivery, no executive-level requirement |
| C3 | Contract | Technical Project Manager | Technology implementations |
| C4 | Contract | IT Project Manager | Enterprise delivery |
| C5 | Contract | Banking Project Manager | Finance/technology strength |
| C6 | Contract | Product Owner | Transferable product skills, relaxed experience criterion |
| C7 | Contract | Product Manager | Product and AI-adjacent exposure |
| C8 | Contract | Regulatory Technology Program Manager | Adjacent compliance/tech experience |
| F1 | Full-time | Head of PMO / PMO Director | Senior PMO/portfolio leadership |
| F2 | Full-time | Enterprise Portfolio Director / Transformation Leader | Senior strategic delivery |

These phrases are **trial inputs**, not an exclusive approved title list. Split alternatives when an API doesn't support OR queries. Evaluate actual responsibilities, employment type and eligibility, not only the job title.

## Geographic test slices

1. Atlanta and metro roles: use actual **road miles** from a private origin (not ZIP centroid) when a precise employer office is available.
2. US remote: verify states where employment is allowed, onsite frequency and occasional travel expectations.
3. Canada and Mexico: include in source coverage research as user-requested markets, but **do not presume** that a US-based worker can take any posting or that international relocation is desired. Preserve compensation currency.
4. Tennessee: include potential onsite/relocation scenarios for review; do not classify as ordinary local commute opportunities.

Never commit the user's private street address to this public repo.

## Candidate providers for testing

| Candidate | Purpose | Verification method |
|---|---|---|
| Adzuna | Broad search | Credentialed sample after user provisions free key, confirm terms/quotas; record actual responses |
| Greenhouse | Direct employer published jobs | Pick balanced finance, tech, consulting board tokens; inspect public GET job and content fields |
| Ashby | Direct employer published jobs | Sample employer boards, including whether compensation/arrangement are exposed |
| Lever | Direct employer postings fallback | Sample distinct employer boards and compare additional coverage |

Official docs for interface feasibility: [Adzuna](https://developer.adzuna.com/docs/search), [Greenhouse](https://docs.greenhouse.io/job-board), [Ashby](https://developers.ashbyhq.com/docs/public-job-posting-api), [Lever](https://github.com/Lever/postings-api).

Documentation confirms API interfaces exist; it does **not** establish actual currently open relevant roles or acceptable usage terms/price for this user's workload.

## Evidence to record for each real call

- Exact timestamp/timezone, provider, board token or query, request status, page count and posted listing count.
- At least up to 20 available representative postings per source/query where the source has sufficient volume.
- Posting ID, canonical employer, title, direct apply/source URL, complete duties and requirements.
- Employment type (W-2/1099/C2H/C2C where actually disclosed), hours, work arrangement and exact remote days.
- Location, candidate road-route feasibility (private origin stays local), posted date and whether the role is active.
- Pay minimum/maximum, period and original currency; missing/estimated versus employer-stated compensation.
- Manually judged eligibility, likely interest, relevance, missing critical fields, source overlap and stale/resurfaced postings.
- Source-specific terms, quota, fees, access prerequisites and observed error behavior.

Each newly enabled job source receives its own **30-day initial lookback**, as explicitly specified by the user. A later scan can include newly discovered older open roles with age visible; do not re-email a previously known canonical posting as new.

## Source acceptance gate

A provider passes when:
1. It permits repeatable personal-use automated collection at acceptable cost (free-first).
2. Real samples include **relevant open opportunities** for the two target tracks.
3. Descriptions and source identity support meaningful suitability ranking and deduplication.
4. Unknown salary/work arrangement is preserved honestly and linked to source evidence.
5. Failures and partial search runs are visible; advertised age is not treated as absolute newness.

Do not announce completed source validation until dated live responses and manually inspected sample findings are recorded.

## Next actions

- [x] Derive search portfolio from user-submitted questionnaire.
- [ ] Select employers with verified public board identities, excluding Regions and Invesco from recommendations.
- [ ] Execute real API samples and record actual response fields/relevance.
- [ ] Verify provider usage terms and any credentials/payment implications.
- [ ] Recommend initial sources and obtain source/eligibility approval.
