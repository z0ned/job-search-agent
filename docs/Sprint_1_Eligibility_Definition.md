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

## Confirmed contract classification and preference (2026-11-17)

- **Eligible contract arrangements:** Both **W-2 contract** and **1099 independent-contractor** opportunities.
- **Preference:** W-2 contract is preferred; this is a **soft ranking preference**, not a mandatory eligibility filter. Do not reject an otherwise eligible 1099 role solely because it is 1099.
- **Compensation:** Preserve the previously confirmed **$70/hour minimum when disclosed**, or include when the rate is unspecified, for both arrangements. Do not silently change the minimum to account for tax, benefits or overhead differences; those factors may be displayed separately and revisited later.
- **Unknown classification:** A posting labeled only "contract" without W-2/1099 details stays eligible on this dimension, with engagement arrangement unverified. Do not silently classify it as W-2 or 1099.
- **Workload context:** The approximate 40-hour-week preference remains a separate soft criterion intended to preserve time for AI and other skill development.

## Confirmed contract travel policy (2026-11-17)

**User selection: Option D — travel requirements are flexible for contract roles.**

- No maximum overnight travel percentage or number of nights has been established for **contract** opportunities.
- Do **not** exclude contract jobs based solely on stated overnight travel expectations or invent a 10% or 25% cap.
- Display advertised travel requirements when available. Mark absent or vague travel details as **not specified**, rather than inventing a commitment.
- Keep the approximately 40-hour workweek as a **separate expressed preference** for practical PM/program-management contract roles; flexible travel does not imply approval of unlimited weekly work hours.
- **Full-time-role travel expectations remain OPEN** and should be elicited separately.

## Confirmed location and onsite rules (user clarifications through 2026-11-17)

**Confirmed commute origin and method (2026-11-17):** Driving distance (actual road miles) from the user's **specified street address in ZIP 30307**, **not** straight-line radius and **not** the ZIP centroid. The precise origin address is private and MUST NOT be committed to this public GitHub repository, printed in logs, or embedded in exported reports. Store it later in a local untracked setting or protected secrets store, e.g. `JSA_COMMUTE_ORIGIN_ADDRESS`; this documentation intentionally omits it. Reconcile address geocoding and road-routing capability during the source/eligibility feasibility phase, without building a production adapter now.

**Confirmed Atlanta onsite exception:** A job whose listed office is **within 10 driving miles** of the private origin is eligible even if **100% onsite**. A job explicitly labeled **"Atlanta"** but without a more specific office address is also eligible for 100% onsite work by user-approved exception; this **does not** mean a road distance has been verified. When an exact office address is known, evaluate the actual driving distance rather than assuming a broad "Atlanta" city label guarantees proximity.

| Case | Confirmed eligibility treatment | Evidence / display requirement |
|---|---|---|
| Office **0–10 driving miles**, inclusive, from private origin | 100% onsite acceptable | Save road mileage and routing provider/method when available |
| Listing says **"Atlanta"** but gives no exact office | 100% onsite acceptable | Flag distance as unverified; eligible via the user's explicit Atlanta-label exception |
| Office **over 10 but under 30 driving miles** | Eligible only if **both Mondays and Fridays are remote** | Verify the particular weekdays, not just generic "hybrid" |
| Office **30 or more driving miles** | Eligible if **100% remote** | Do not equate generic hybrid with fully remote |
| **No onsite requirement stated**, wherever the listed job is based | **Include, with verification flag (Option C)** | Display: "Work arrangement not specified — verification required"; do not label as remote |
| Office or route cannot be resolved, but specific onsite attendance is required | Location/commute eligibility is **UNKNOWN** until distance can be verified | Never invent road miles or silently declare a pass/fail |

**Decision priority:** A specific advertised work arrangement and verifiable office location control distance-based evaluation; the Atlanta-without-office exception and absent-onsite-requirement exception are separate user-approved paths to initial eligibility. An omitted onsite requirement keeps a posting in discovery with an explicit verification flag; it is not proof of remote work. All other employment, pay, experience and role rules still apply.

**Feasibility caveat:** Road miles require a routable origin and destination. A city centroid, ZIP centroid or straight-line estimate may help triage candidates but must never be presented as a verified 10/30-driving-mile result. Provider, route type and possible usage cost are open design choices.

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
