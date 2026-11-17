# Sprint 1 — Consolidated Remaining Decisions Questionnaire

**Date:** 2026-11-17
**Status:** QUESTIONS OPEN — no unapproved defaults activated
**Purpose:** Finish eligibility and job-source feasibility requirements in one batch rather than continuing one-question-at-a-time interviewing.

## Already confirmed — DO NOT ask again

- Two search tracks: practical execution-focused contract PM/Program Manager (approximately 40 hours/week preferred to leave time for AI/other learning), and senior PMO/portfolio/financial-services technology leadership full-time.
- Contract $70/hour minimum when disclosed; full-time $180,000/year minimum when disclosed; missing compensation does not exclude.
- Contract W-2 and 1099 both eligible; W-2 preferred; unspecified contract classification included with verification note.
- Overnight travel flexible with no fixed maximum in **both** tracks (Option D).
- Local commuting distance measured **by driving/road miles from the user's private street address** in 30307 (do not commit exact private address).
- 0–10 miles allows 100% onsite; explicitly "Atlanta" with office unspecified allows onsite; over 10 and under 30 requires remote Monday and Friday; at least 30 requires 100% remote.
- Posting missing onsite requirements is eligible with explicit "Work arrangement not specified — verification required" flag (Option C).
- Initial required-experience language: more than five years for related roles; any experience for Product Manager, Product Owner, or similar roles. Exact five-year and loose-match edge cases remain open.
- AI feedback learning approval, archive, weekly blind audit, baseline/comparison evaluation phases are already confirmed elsewhere. No application tracking.

## Questions that still materially affect Sprint 1

Reply with numbered answers. **Suggested research defaults are offered, not confirmed decisions**. "Accept suggested answers except #..." is an explicit way to approve them if desired. Mark any question "undecided" to leave it open.

### A. Priority and eligibility boundaries

1. **Relative search effort:** For initial job-source validation, what share of searches should target contract vs full-time? **Suggested: 70% contract / 30% full-time** since contract work is the immediate practical priority. Other: 50/50, 80/20, specify.
2. **Remote geography:** Should remote opportunities be limited to employers explicitly hiring in Georgia/the United States, or also include foreign employers willing to hire a US-based worker? **Suggested: US/Georgia-eligible employment only**; do not assume remote means work-from-anywhere.
3. **Relocation or extended onsite assignments:** Would you consider relocating or working temporarily at a distant office even when a posting is not remote? **Suggested: No relocation, but ordinary business travel remains flexible** under the confirmed travel rule.
4. **Hybrid ambiguity at 10–30 driving miles:** If posting says "hybrid" without confirming **both Mondays and Fridays remote**, should it stay eligible **with verification flag**, or be excluded until the schedule is confirmed? **Suggested: Include with a verification flag.**
5. **Remote plus occasional office trips at 30+ miles:** If the role is home-based remote but requires periodic travel to company offices or client sites, should it count as remote under the 30-mile rule? **Suggested: Yes, if no regular office commute is required**, with travel disclosed. User's flexible travel policy remains separate.

### B. Employment and compensation

6. **Contract duration:** Accept short projects of any length, set minimum duration (e.g. three/six months), or favor longer projects without a hard minimum? **Suggested: Any duration eligible; prefer stable six-plus-month engagements.**
7. **Other contract arrangements:** Include contract-to-hire, corp-to-corp (C2C) through an entity, and temporary staffing assignments? May answer separately for each. W-2 and 1099 are already accepted. **Suggested: Contract-to-hire yes; temporary staffing yes if 40-hour roles; C2C requires explicit confirmation.**
8. **Hours:** For contract jobs explicitly advertising routine 45–55-hour weeks, exclude them, or keep them with a significant ranking penalty given your desire to develop AI skills? **Suggested: Keep but rank lower; 40-hour week remains preferred.**
9. **Full-time pay definition:** Does the $180k floor mean annual **base salary**, guaranteed cash (base + guaranteed bonuses), or expected total compensation including variable bonus/equity? **Suggested: Base salary**; treat discretionary bonus/equity separately.
10. **Salary ranges spanning the floor:** If a role advertises $60–$85/hour or $160k–$210k/year, include it because the high end reaches the threshold, or require the low end to meet it? **Suggested: Include if the high end meets the minimum; flag that minimum is not guaranteed.**

### C. Jobs and qualifications

11. **Years-of-experience boundary:** Does "more than five years required" literally exclude a related non-product PM job asking for 5 years, or is it intended to exclude junior work while allowing a substantial 5+ year role? The Product Manager/Product Owner exception stays intact. **Suggested: Treat 5+ substantial roles as eligible rather than exclude on exact numeric wording; confirm.**
12. **Unmet job qualifications:** When a listing says a particular degree, certification or security clearance is **required** and evidence of your eligibility is not in the profile, should we exclude only if demonstrably impossible, or hold for verification? **Suggested: Include with an explicit qualification gap unless definitively ineligible.**
13. **Absolute exclusions:** Are there any employers, industries, primary job duties (e.g. direct sales or contact-center operations), schedules or other conditions that should be **hard disqualifiers**? Distinguish dislikes (soft preferences) from non-negotiable exclusions. **Suggested: No new hard bans without explicit names/reasons.**
14. **Additional career families for initial sample searches:** Beyond the confirmed tracks, should we test adjacent AI implementation/product ownership, technology business relationship, consulting/client engagement without sales quotas, regulatory technology, and general enterprise transformation? **Suggested: Yes, exploratory searches, but do not allow them to displace main contract PM or full-time senior PMO searches.**
15. **Source-testing employer list:** Any must-include firms or sectors for direct Greenhouse/Ashby/Lever boards? Otherwise may I select a balanced initial set of employers in finance, enterprise technology and consulting based on which boards actually expose relevant data? **Suggested: Select a representative mix; user can name exceptions.**

### D. Source feasibility and posting freshness

16. **External data service budget/access:** Is job-data API spending limited to **$0/month**, or is a small monthly amount acceptable if needed (specify cap)? Are you willing to register for a free Adzuna developer key if the API requires it? **Suggested: Free-first, evaluate a low paid tier only with explicit approval; user may need to provision key.**
17. **First-run job age:** When the agent first starts, should it surface currently open jobs posted within **14 days, 30 days, or any age**? After that, should the daily digest include jobs that are newly *discovered* even if their original posting date predates our scan? **Suggested: First run last 30 days; subsequent newly discovered eligible jobs included but show age, with no repeated alerts for the same requisition.**
18. **Reposts:** If an old listing reappears or the employer refreshes its date but its requisition is unchanged, should it count as "new" for email? **Suggested: No; only a genuinely distinct requisition or explicit approved exception.**

## Still not required to answer during Sprint 1

Detailed dashboard interaction patterns, daily email size/time, model selection/scoring weights, exact metric-regression pause threshold, automated scheduling specifics, and optional v2 features should be addressed after source access and eligibility are validated.

## Sprint 1 acceptance

- Capture the user's answers as explicit hard-vs-soft rules with exact provenance; unanswered items stay OPEN.
- Derive representative search queries from approved tracks and locations.
- Validate actual provider responses and relevance before selecting production adapters.
- No Python database or application implementation is authorized by this questionnaire.
