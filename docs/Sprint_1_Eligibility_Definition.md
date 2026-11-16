# Sprint 1: Eligibility Requirements Workbook

**Date:** 2026-11-16
**Status:** OPEN — interview guide, not approved personal job criteria

## Executive summary

Before writing hard filters, distinguish mandatory disqualifiers from preferences used only to rank eligible jobs. AI learning may modify soft preferences only after explicit interpretation approval; it may never quietly modify mandatory rules.

## Confirmed principles from requirements v1.1

1. The application recommends jobs, not applications or interview management.
2. An explicit known violation of a confirmed mandatory criterion excludes a job from recommendations.
3. A rejection due to compensation, employer, travel or job arrangement does not imply rejection of that career category.
4. The system must handle ambiguous or missing facts without inventing salary, geography or eligibility evidence.
5. Adjacent career exploration stays within confirmed mandatory constraints.
6. Important explicit user preferences are distinct from AI-inferred preferences.

## Confirmed two-track search strategy (user clarification, 2026-11-16)

This user correction supersedes treating the senior financial-services/PMO leadership characterization as the target profile for **both** employment tracks.

| Dimension | Contract work — immediate practical priority | Full-time work — senior career track |
|---|---|---|
| Desired kind of work | A **40-hour/week project manager or program manager role** is welcome; execution-focused work is attractive because it preserves time to develop AI and other skills | Senior financial-services technology, portfolio/PMO leadership, and business transformation roles |
| Title targeting | Project Manager, Program Manager, Product Manager/Product Owner and similar roles or work loosely matching the resume | Head of PMO, PMO Leader, Portfolio Manager and comparable senior roles or work loosely matching the resume |
| Seniority interpretation | **Do not require director/VP/SVP leadership responsibilities or title.** A conventional experienced individual-contributor PM/program-manager contract may be a very good match | Use senior leadership scope and enterprise-level responsibilities as strong ranking evidence |
| Compensation rules from Job_Requirements.docx | Minimum **$70/hour when disclosed**; undisclosed hourly rate stays eligible | Minimum **$180,000/year when disclosed**; undisclosed salary stays eligible |
| Weekly hours | **Approximately 40 hours/week is the user's expressed preference**, motivated by protected time for AI/other skills. Do not yet implement a rigid overtime or exact-hours exclusion without explicit approval | No new weekly-hours requirement stated |
| Industry interpretation | Deep banking/capital-markets background is useful evidence of qualifications, **not** a requirement that contracts be in finance | Financial-services and transformation leadership are strong matches, but other loosely matching roles remain discoverable |
| Strategic purpose | Good-paying, sustainable contract delivery work **now**, while maintaining room for skill development | Strongly aligned longer-term senior leadership opportunity |

**Confirmed user wording (paraphrased):** The senior financial-services technology / PMO / portfolio-leader characterization is correct **for full-time roles only**. The user is happy to take a contract 40-hour-week project/program manager role now to allow time to expand AI and other skills.

**Do not silently infer** that contract jobs must be low-stress, fully remote, lack leadership duties, be short duration, or be exclusive to financial services. The earlier documented location/onsite alternatives and experience exception for product roles still apply to both tracks until changed.

**Matching implication:** Run and evaluate contract and permanent searches as separate profiles. For contract jobs, scoring should not penalize an otherwise attractive role for lacking VP-level scope. Do not raise or lower either compensation threshold based on this clarification.

## Confirmed Atlanta-area location rule (user clarification, 2026-11-16)

**Decision A confirmed:** An Atlanta-based job may be **100% onsite**. For this rule, **"Atlanta" means within 10 miles of ZIP code 30307**. A posting explicitly labeled **"Atlanta"** remains eligible for **100% onsite work even if the precise office address/location is not specified**. Do not reject an Atlanta-labeled posting just because a street address is unavailable.

| Case | Confirmed treatment | Evidence handling |
|---|---|---|
| Verified job office within **10 miles** of 30307 | Eligible for fully onsite work | Record the located office/distance when available |
| Posting location is "Atlanta", but no specific office address is listed | Eligible for fully onsite work | Record that eligibility came from the **Atlanta location label**, not from verified 10-mile distance |
| Office more than 10 but under 30 miles from 30307 | Prior rule requires remote work on **Mondays and Fridays** | Do not silently extend the Atlanta fully-onsite exception beyond 10 miles |
| Office at or beyond 30 miles from 30307 | Prior rule requires **100% remote** | Exact 30-mile boundary remains to be reconciled if necessary |
| Onsite requirement unspecified, regardless of posted city | **OPEN**: the original source document contains an additional "Onsite requirement not stated" alternative | Do not reinterpret or remove this branch without user clarification |

**Important:** A nearby city label alone does not demonstrate a job is within 10 miles. "Atlanta" without an office address is an explicit user-approved exception, not a geocoding result. The original rule allowing jobs with *no stated onsite requirement* still needs separate clarification about geographical scope.

## Hard eligibility and soft ranking dimensions

| Dimension | Hard rule needing user decision | Soft preference needing user decision | Unknown field problem |
|---|---|---|---|
| Work arrangement | Remote only? Hybrid? Onsite? | Preferred in-office frequency | Unclear "flexible" or hybrid policy |
| Geographic scope | USA remote? Specific metro/commute radius? | Preferred cities | Remote roles restricted to certain states |
| Employment type | Permanent, W2 contract, 1099, part-time? | Preferred contract length | Type not specified |
| Compensation | Absolute minimum annual base or hourly rate | Target pay and tradeoffs | Salary undisclosed or only estimated |
| Travel | Absolute maximum overnight/regular travel | Tolerable occasional visits | "Travel as needed" vague |
| Role responsibilities | Firm exclusions, e.g. explicitly unwanted primary duties | Day-to-day interests and client exposure | Descriptions vague |
| Seniority/scope | Levels truly unacceptable | Desired autonomy/responsibility | Title inconsistent across employers |
| Employer/industry | Explicitly banned companies/sectors | Culture/values/industry affinity | Unknown reputation |
| Qualifications | Confirmed requirements impossible to meet | Stretch roles leveraging transferable skills | Ambiguous wording |
| Hours/schedule | Absolute restrictions | Hours/time zones preference | Posting omits schedule |
| Work authorization/clearance | Requirements relevant to user | None assumed | No evidence |

**Do not use historic resume/search preferences as binding hard rules unless user confirms them for this agent.**

## Three-valued eligibility model (proposed)

- PASS: reliable listing evidence meets all applicable confirmed mandatory rules.
- FAIL: reliable listing evidence clearly violates at least one confirmed mandatory rule.
- UNKNOWN: no explicit violation, but information needed for at least one hard rule is missing or ambiguous.

The user must separately decide whether UNKNOWN jobs appear in recommendations (with warning), in a manual-review bucket, or are excluded. **Never convert missing salary into zero salary.** Never assume estimated salary is guaranteed. Do not treat a rejection of a single employer posting as a global category ban.

## One-question-at-a-time interview sequence

1. Which work arrangements are acceptable — remote, hybrid and/or onsite?
2. What geographic restrictions and hybrid/onsite commuting radius apply?
3. What employment types are eligible?
4. What minimum compensation thresholds apply to each employment type?
5. How should listings with undisclosed compensation be handled?
6. What is the maximum acceptable travel requirement?
7. Which initial role families should sources search? What adjacent families may be explored?
8. Which responsibilities and industries are absolute exclusions rather than negative ranking preferences?
9. Are any seniority levels mandatory disqualifiers?
10. Are there employer-specific exclusions?
11. What job posting age/repost rules should apply?
12. Are there other hard restrictions (shift work, clearance, licensing, authorizations)?

For each answer record: exact user wording, hard-vs-soft classification, effective date, and example PASS/FAIL/UNKNOWN cases. Obtain explicit consolidated approval before implementation.

## Illustrative examples — not user-specific decisions

- If remote-only is confirmed, an onsite-only posting is FAIL.
- If salary floor is confirmed but salary absent, pay eligibility is UNKNOWN, not necessarily FAIL.
- If a role has desirable duties but low pay, mark compensation rejection separately from role interest.
- If a job is within a newly discovered role category, assess it against hard constraints; unfamiliar title alone should not exclude it.

## Sprint 1 acceptance criteria

- [ ] Each mandatory eligibility rule is stated and explicitly approved.
- [ ] Ranking-only preferences are separated from disqualifiers.
- [ ] Unknown salary, arrangement, location and travel policies are documented.
- [ ] Representative test job queries are derived from confirmed target role families.
- [ ] Each mandatory rule has clear PASS, FAIL and UNKNOWN test cases.
- [ ] The final eligibility policy is versioned and signed off before writing production filter code.

## Risks and future enhancements

The greatest eligibility risk is over-filtering good opportunities based on missing or guessed information. Start with few confirmed hard rules and use transparent uncertainty; later tune preferences from approved feedback.
