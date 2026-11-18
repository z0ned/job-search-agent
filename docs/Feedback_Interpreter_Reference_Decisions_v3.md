# Feedback interpreter v3 reference decisions

This record applies to future v3 scoring. The source fixture is `1.0-draft` with SHA-256 `fbf6872f847d533871ad2db7d3412a324504171f057f56ae7a8f1f8f48311523`. [Frozen gold cases](../feedback_interpretation_gold_cases_v1.json)

## FI-007

The user approved the project-type interpretation on November 18, 2026. The feedback was “I am not interested in another core-banking replacement transformation.”

| Field | Frozen reference | Approved interpretation for v3 |
| --- | --- | --- |
| Preference | Negative career-category preference for core-banking replacement | Negative preference for core-banking replacement projects |
| Scope | `career_category` with value `core_banking_replacement` | The recurring project type, independent of employer or job title |
| Career-category interest change | Yes | No |

“Another” indicates a recurring kind of project. Apply the preference where the opportunity involves replacing a core-banking system. The quote establishes no preference about banking as an industry, transformation programs generally, or other types of projects. The existing mild strength, pending approval route, and unchanged hard-rule action carry forward. This decision defines the meaning and scope. A machine identifier can be assigned when the v3 taxonomy is approved. [V2 case adjudication](feedback_adjudication_v2/Gold_01_17.md#fi-007)

## Remaining gold cases

On November 18, 2026, the user accepted all 49 case recommendations below. **Keep** carries forward the reference meaning. **Refine** makes a material limit explicit. **Revise** changes the expected signals or route. Reference fields outside these decisions carry forward from the source fixture. This approval covers the reference interpretations.

### FI-001 through FI-017

| Case | Decision | Approved expectation for v3 |
| --- | --- | --- |
| FI-001 | Refine | Record dislike of workdays dominated by creating status decks. Preserve the activity and its share of the workday. |
| FI-002 | Keep | Record two separate positive duties, solving client problems and running AI solution workshops. |
| FI-003 | Keep | Record interest in advisory work and an objection to carrying a sales quota. Scope the quota objection to the duty. |
| FI-004 | Revise | Record one positive preference for delivering concrete transformation milestones on short contracts. Contract length qualifies the activity. |
| FI-005 | Keep | Record a negative career preference for returning to contact-center operations roles. |
| FI-006 | Revise | Record one positive AI enablement career preference. Treat “even if I need training” as willingness to pursue it despite a hurdle. Drop the separate positive training signal. |
| FI-008 | Keep | Record dislike of rotating overnight on-call duty. Preserve rotation and overnight hours. Treat the title comment as acknowledgment. |
| FI-009 | Keep | Record interest in client-facing AI work and a negative reaction to $110/hour C2C for this opportunity. Treat the amount as a quoted rate. |
| FI-010 | Refine | Keep acceptance of $140/hour C2C and a positive reaction to this posting's scope. The feature is the posting's scope as stated. |
| FI-011 | Refine | Keep acceptance of $80/hour W-2 and a negative preference about the onsite schedule for this posting. |
| FI-012 | Keep | Record acceptance of the $190,000 annual base and keep `PENDING_APPROVAL`. Carry the bonus question as a detail to verify. |
| FI-013 | Revise | Route to `PROFILE_FACT_REVIEW` with `REPORT_EXISTING_ELIGIBILITY_VIOLATION` for the $175,000 base below the established minimum. Emit zero preference signals. “This could be fun” is an unspecified positive reaction. |
| FI-014 | Refine | Record concern about months without billable work in this C2C engagement. Preserve the duration and treat the $120/hour rate as context. |
| FI-015 | Keep | Record the objection to employers refusing to disclose base salary. Nondisclosure is the target of the negative preference. |
| FI-016 | Refine | Record the positive reaction to this posting's mission without assigning mission details from its title. Carry the compensation question as a detail to verify. |
| FI-017 | Keep | Record the negative reaction to Northstar Tech, with recent layoffs as the stated reason. |

[Case evidence and saved-pass comparisons](feedback_adjudication_v2/Gold_01_17.md)

### FI-018 through FI-034

| Case | Decision | Approved expectation for v3 |
| --- | --- | --- |
| FI-018 | Keep | Record a strong negative preference for the tobacco industry. Handle formal exclusions through separate rule authorization. |
| FI-019 | Refine | Record a positive mission preference for helping small nonprofits apply AI. Preserve “small” as a qualitative limit. |
| FI-020 | Refine | Record dislike of pervasive micromanagement. Use “micromanages every decision” as evidence of the degree of control. |
| FI-021 | Refine | Keep the positive reaction to Verity Labs and the positive impression of its thoughtful, collaborative technical team. Link the team impression to the employer reaction it explains. |
| FI-022 | Keep | Record the objection to Ridgetop Bank. Willingness to do this job at another firm contextualizes the employer-specific rejection. |
| FI-023 | Keep | Route to `PROFILE_FACT_REVIEW` with `REPORT_EXISTING_ELIGIBILITY_VIOLATION` for three onsite days at 45 miles. Emit zero preference signals. |
| FI-024 | Revise | Record one positive preference for fully remote work. Preserve the ability to focus on client work as a stated benefit of remote work. Drop the independent client-facing preference. |
| FI-025 | Keep | Record dislike of required night and weekend coverage. Preserve both time periods. |
| FI-026 | Keep | Record one positive preference for hybrid work at this nearby office. Use six miles to describe the opportunity. |
| FI-027 | Keep | Record dislike of weekly flights and acceptance of occasional business trips. Preserve travel mode and frequency. |
| FI-028 | Keep | Route to `PROFILE_FACT_REVIEW` with `REPORT_EXISTING_ELIGIBILITY_VIOLATION` for required onsite Mondays and Fridays at 20 miles. Emit zero preference signals. |
| FI-029 | Keep | Use `NEEDS_CLARIFICATION` and ask what makes the commute a problem. |
| FI-030 | Keep | Record attraction to trusted hands-on expert work and the limitation on managing a large team. Leave small-team management open. |
| FI-031 | Refine | Record the objection to directly managing 20 people. Preserve that team size and leave any general cutoff open. |
| FI-032 | Keep | Record interest in owning a larger AI transformation portfolio. The preference concerns the level of ownership. |
| FI-033 | Keep | Record one negative preference for very little decision-making autonomy. “Too junior” summarizes that concern. |
| FI-034 | Keep | Use `NEEDS_CLARIFICATION` and ask what feels too senior. The comment gives no specific preference or checkable qualification claim. |

[Case evidence and saved-pass comparisons](feedback_adjudication_v2/Gold_18_34.md)

### FI-035 through FI-050

| Case | Decision | Approved expectation for v3 |
| --- | --- | --- |
| FI-035 | Revise | Record one strong positive AI solution architecture career preference and keep `PENDING_APPROVAL`. Learning the tooling is a prospective hurdle. Drop the separate training preference. |
| FI-036 | Keep | Use `PROFILE_FACT_REVIEW` for the self-reported gap in hands-on SAP integration experience for this contract. Emit zero preference signals. |
| FI-037 | Refine | Record dislike of writing Python for most of the workday. Preserve the language, workload share, and daily cadence. |
| FI-038 | Keep | Use `PROFILE_FACT_REVIEW` for the claim of having delivered these migrations. Emit zero preference signals. |
| FI-039 | Keep | Record a strong positive career preference for AI evangelism. |
| FI-040 | Keep | Record a strong negative career preference for quota-carrying sales. The captured wording identifies the same scoped category. |
| FI-041 | Revise | Keep two independent signals. Scope positive interest to this AI advisor posting as a whole and record distrust of the current employer separately. |
| FI-042 | Refine | Keep the positive AI product leadership career preference. Scope the negative reaction to Omega Health to that career context. |
| FI-043 | Keep | Record strong interest in AI strategy consulting as a line of work and a separate objection to the $105/hour C2C rate for this opportunity. |
| FI-044 | Keep | Use `NEEDS_CLARIFICATION` and ask what looks promising. Emit zero preference signals. |
| FI-045 | Keep | Use `NEEDS_CLARIFICATION` and ask what did not fit. Emit zero preference signals. |
| FI-046 | Keep | Use `NEEDS_CLARIFICATION` and ask what specifically felt off about the culture. Emit zero preference signals. |
| FI-047 | Refine | Keep acceptance of this job's pay and the objection that the role offers too little seniority for the responsibility sought. Preserve that relationship in the scope. |
| FI-048 | Refine | Record dislike of work with a strong sales emphasis. Anchor the proposal to both the posting's “must love sales” wording and the user's reaction. |
| FI-049 | Keep | Use `NEEDS_CLARIFICATION` for what feels wrong about this posting and retain the independently supported positive consulting career preference for review. |
| FI-050 | Revise | Use `PROFILE_FACT_REVIEW` with `REQUIRES_SEPARATE_EXPLICIT_RULE_CONFIRMATION`. Record the tentative $165,000 base exception if the role is exceptional in the rule-review item. Drop the inferred duty preference. |

[Case evidence and saved-pass comparisons](feedback_adjudication_v2/Gold_35_50.md)
