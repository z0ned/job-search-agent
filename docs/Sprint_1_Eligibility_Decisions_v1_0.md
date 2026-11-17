# Sprint 1 — Eligibility Decisions v1.0

**Date:** 2026-11-17  
**Status:** Answers extracted from user-committed questionnaire; final eligibility policy and source testing still open.  
**Primary source:** [User's original answers](./Sprint_1_Remaining_Decisions_Questionnaire.md). Do not alter that document.  
**Other confirmed rules:** [Eligibility workbook](./Sprint_1_Eligibility_Definition.md).

## Executive summary

Two search tracks: **80% of source-validation searches contract / 20% full-time**. This split is separate from the *unapproved* proposed 80% familiar/20% exploratory allocation. Contract work should accommodate practical PM/program execution, approximately 40 hours/week preferred, to preserve time to develop AI skills. Full-time work targets senior PMO/portfolio/financial-services technology leadership.

## Exact response extraction and policy classification

| Questionnaire ID | User answer | Classification and interpretation |
|---|---|---|
| Q1 Search split | **80/20** | Confirmed: contract/full-time source search allocation |
| Q2 Remote countries | **USA, Canada and Mexico** | Confirmed geographic exploration scope. Work eligibility, physical work location and remote jurisdiction remain to verify |
| Q3 Relocation | **Only somewhere in Tennessee** | Confirmed relocation boundary: Tennessee only; TN onsite should be flagged as relocation candidate, not silently auto-approved |
| Q4 10–30-mile unspecified hybrid days | **Stay eligible with verification flag** | Confirmed: keep uncertain Monday/Friday hybrid schedule and show verification flag |
| Q5 30+-mile remote job with periodic office visits | **Yes** | Confirmed: occasional business trips allowed, distinct from regular commute |
| Q6 Contract duration | **Any duration** | Confirmed: no minimum duration. Do not adopt unconfirmed six-month preference |
| Q7 C2H, temp, C2C | **Suggestion accepted** | Confirmed: contract-to-hire and temporary staffing acceptable. The suggestion explicitly left **C2C requiring confirmation**; keep C2C OPEN |
| Q8 45–55-hour contract | **Suggestion accepted** | Confirmed: include, but rank below equivalent predictable 40-hour contracts |
| Q9 Full-time compensation | **Base** | Confirmed: annual **base salary**, not bonus or equity |
| Q10 Salary ranges crossing floor | **Include and flag** | Confirmed: if high end reaches minimum, include with uncertainty warning |
| Q11 Junior experience rule | **Intended to eliminate junior roles, e.g. asking for min 3 years experience** | Confirmed intent, not a mathematical blanket >5-year threshold; 5-year experienced roles should not be automatically discarded; role scope still matters |
| Q12 Unknown mandatory qualification | **For the first time, include with explicit qualification gap, but for subsequent jobs it should learn my answers** | Confirmed: first encounter flagged; capture explicit factual clarification for reuse, never fabricate credentials |
| Q13 Excluded employers | **No new hard bans without explicit names/reasons. Absolute exclusion Employers = Regions, Invesco** | Confirmed: hard reject those two employers; avoid unsupported subsidiary/alias inference |
| Q14 Adjacent careers | **Yes** | Confirmed: test AI implementation/product, business relationship, consulting/client engagement, regulatory tech, transformation families without displacing main tracks |
| Q15 ATS employer sample | **Balanced mix** | Confirmed: finance, technology and consulting employer boards |
| Q16 Provider budget | **Suggestion approved** | Confirmed: free-first, any paid subscription requires separate explicit consent |
| Q17 Source lookback | **Suggestion approved. If we add a new job source, first run should also be 30 days.** | Confirmed: initial 30-day lookback for **each newly added source**, not only first launch. Subsequent newly discovered older jobs may be included with posted age shown; never resend an already alerted canonical job |
| Q18 Refreshed/reposted req | **No answer entered** | OPEN: do not silently adopt suggested repost policy; keep existing "don't re-email same already-known job as new" requirement |

## Previously confirmed requirements retained

- Both W-2 and 1099 contracts eligible; W-2 preferred. Contract floor **$70/hour**, full-time floor **$180,000/year base** when disclosed; unspecified compensation still eligible.
- Flexible overnight travel with **no fixed maximum** for both tracks.
- Driving/road miles from private user-specified street origin in 30307 (do not commit address).
- Within 10 driving miles: onsite acceptable. "Atlanta" with no specific office: onsite accepted by explicit exception, but distance unverified.
- Greater than 10 and less than 30 driving miles: Mondays/Fridays remote; if "hybrid" dates not specified, **include with verification flag** (Q4).
- At least 30 driving miles: regular 100% remote, but **occasional business/office travel is acceptable** (Q5).
- If onsite requirement absent: **include with verification flag** regardless of city; do not assert that remote is confirmed.
- Contract role need not be executive-level or restricted to financial services.
- Experience rule is designed to suppress **junior** postings; Product Manager / Product Owner roles have an experience requirement exception.
- Never apply AI-derived preference changes to hard constraints without explicit authorization.

## Important design distinctions

- **80/20 contract/full-time** is a search workload ratio, **not** the separate proposed career-exploration mix.
- An advertised annual base of $160k–$210k is provisionally eligible (high end ≥$180k) but pay is not guaranteed. A contract advertising $60–$85/hour is likewise eligible but flagged.
- A job at **Regions or Invesco** is excluded in both tracks even if other attributes match.
- Salary with missing amount stays included with "compensation undisclosed" labeling.
- Canada/Mexico entries must preserve source currency, posted work location, employer authorization and visa/work eligibility unknowns. No invented exchange rates or assumptions that foreign onsite work is allowed.
- A Tennessee onsite role may be a relocation opportunity; flag rather than treat as eligible under normal commute rules automatically.
- The user's answers about objective credentials/qualifications should become **confirmed facts** when explicitly supplied, not inferred from rejection. Preference-learning controls remain separate.

## Still open, not grounds for another long interview

1. **Q18** refreshed/reposted requisitions: no answer supplied (new-only alerting remains confirmed generally).
2. **C2C**: earlier suggestion expressly required confirmation.
3. International job work location, hiring eligibility and salary-currency treatment.
4. Tennessee relocation details for jobs outside routine commute range.
5. Practical junior-role heuristics and evidence for unverified qualifications.

## Recommended Sprint 1 next steps

1. Construct 80/20 representative contract/full-time search portfolio.
2. Verify live job provider endpoints and employer board identities (free-first).
3. Inspect actual sample postings for salary, schedule, experience, employer exclusions, descriptions, age and missing fields.
4. Present evidence and narrowly scoped remaining edge-case decisions before final eligibility signoff. No production code yet.
