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
