# Job Search Agent — Feedback Interpretation Taxonomy & Gold Test Suite v1.0

**Status:** Proposed for design review, not approved and not yet run against an AI model.  
**Date:** November 17, 2026  
**Scope:** Interpretation behavior, not job search integration, profile mutation, or coding.

## Executive summary

The MVP should turn each mandatory written Interested/Rejected explanation into **atomic, evidence-backed, context-scoped signals**, then route those signals through clarification and batch approval. AI never changes hard rules or learned preferences directly. A companion JSON file contains 50 annotated reference scenarios.

## Confirmed design constraints used

- Interested means "would seriously consider applying"; both decisions require a written free-form explanation.
- Save decisions immediately; interpretation and separate batch review happen afterward.
- Preserve raw feedback, assessments, corrections, approval records, and model/profile versions.
- Interpret duties, employer, industry, compensation, arrangement, seniority and career category independently.
- Ambiguous signals require clarification. No unsupported attribute or broad-category inferences.
- Explicit hard requirements (e.g., permanent base $180,000, W-2 $75/hr, 1099 $100/hr) cannot change through ordinary feedback learning.
- No C2C hourly minimum has been selected; it must **not** be fabricated from feedback.
- Approved feedback can be held during frozen phases. Baseline jobs 1–50, then one approved update and frozen comparison jobs 51–100.
- Five eligible lower-ranked jobs are reviewed blindly each week; audits never count in primary Precision@10.

## 1. Controlled attribute taxonomy

| ID / dimension | What it describes | Examples | Narrowest allowable scope | Ranking connection |
|---|---|---|---|---|
| `role_responsibilities` — Duties and activities | One narrowly stated preference or context | client-facing workshops; sales quotas; programming-heavy work | role_feature; optionally career_category only if explicitly mentioned | Role attractiveness |
| `career_category` — Broad role families and new career paths | One narrowly stated preference or context | AI evangelism; contact-center operations | career_category; explicit category evidence only | Career alignment / Career Map |
| `employer` — A particular organization | One narrowly stated preference or context | Northstar Tech; Omega Health | employer only unless separate industry evidence | Employer fit |
| `industry` — Industry or sector explicitly discussed | One narrowly stated preference or context | tobacco industry; banking | industry only; not all employers | Employer fit |
| `compensation` — Pay, structure, transparency | One narrowly stated preference or context | W-2 hourly; C2C; salary disclosure | employment type + job pay context | Compensation fit |
| `work_arrangement` — Location, schedule, travel, remote/onsite | One narrowly stated preference or context | overnight on-call; nearby hybrid; weekly flights | arrangement + location/schedule/travel context | Work arrangement |
| `seniority_scope` — Autonomy, accountability, management | One narrowly stated preference or context | direct reports; portfolio ownership | specific scope/role level | Seniority fit |
| `qualifications_fit` — Skills or credentials user states they possess or lack | One narrowly stated preference or context | SAP integration; migration experience | profile fact candidate; NOT automatic preference | Qualifications fit |
| `culture_environment` — Workplace environment and values | One narrowly stated preference or context | micromanagement; collaborative colleagues | culture feature; employer only if explicit | Employer / Role fit |
| `contract_terms` — Engagement structure beyond rate | One narrowly stated preference or context | duration; nonbillable gaps; C2C obligations | contract type and term | Work arrangement / Compensation |
| `growth_purpose` — Learning, mission, growth potential | One narrowly stated preference or context | learning AI tools; nonprofit impact | specific growth/mission feature | Career alignment |

### Signal representation

One signal records: `dimension`, `feature`, `polarity` (`positive`/`negative`/`uncertain`), `strength` (`mild`/`strong`), `scope` (`type` + `value`), verbatim `evidence_quote`, optional `condition`, source decision/assessment/version, interpretation model/prompt version, and user review state. The signal must be supported by the user’s actual words; job descriptions may provide context but cannot masquerade as user preferences.

**Evidence standard:** exact support span exists in original feedback; a valid classification cannot rely solely on job facts, job title, model prior, or the Interested/Rejected label. **Strength standard:** explicit emphatic language ("love", "hate", "never", "exactly the stretch I want") is strong; ordinary positive/negative wording is mild. A particular job decision does not itself establish an attribute preference.

**Scope rule:** emit the narrowest interpretation supported by feedback. Broader employer/industry/career-category changes require direct wording referring to that level. Do not infer that salary, travel, employer, seniority or qualification objections reject a career category.

**Hard-rule rule:** report potential rule changes to a *separate explicit confirmation workflow*. A statement in job feedback cannot silently modify hard constraints; an eligibility error should be reported as a defect rather than preference training.

## 2. Deterministic gates and statuses

1. **Store decision:** require nonblank written rationale; preserve assessment snapshot and timestamps.
2. **AI proposes:** extract zero or more evidence-backed atomic signals; no automatic profile mutation.
3. **Validate:** controlled dimensions and scope types, exact evidence spans, no contradictory polarity on the same span/context without clarification, no hard-rule edits.
4. **Route:** `PENDING_APPROVAL` for clear proposals, `NEEDS_CLARIFICATION` for ambiguous motivations, `PROFILE_FACT_REVIEW` for qualifications claims, hard-rule proposals, and eligibility defects.
5. **Human review:** support correct/dismiss/clarify, then explicit bulk approval; preserve the original output.
6. **Phase gate:** approved evidence is **HELD** during freezes; later applied transactionally and idempotently when learning is enabled.
7. **Learn:** bounded, versioned preference changes confined to matching features/contexts; no category change unless approved evidence explicitly indicates category interest.
8. **Measure:** compare 50+50 frozen phases and use rolling 50-job precision and five-job weekly blind audits.

## 3. Gold test suite — 50 cases

All entries below are **synthetic examples**, not records of real job reviews. They are expected outputs to check against an AI interpreter. Full job context, expected atomic signals (with evidence quotes), prohibited inferences, and clarification questions are in the JSON companion.

| Case | Area | Decision | Feedback | Expected route |
|---|---|---|---|---|
| FI-001 | Responsibilities | Rejected | I would spend my days creating status decks. That is not the work I want. | `PENDING_APPROVAL` |
| FI-002 | Responsibilities | Interested | I love solving client problems and running AI solution workshops. | `PENDING_APPROVAL` |
| FI-003 | Responsibilities | Rejected | The advisory work appeals to me, but I do not want a sales quota. | `PENDING_APPROVAL` |
| FI-004 | Responsibilities | Interested | I enjoy delivering concrete transformation milestones on short contracts. | `PENDING_APPROVAL` |
| FI-005 | Responsibilities | Rejected | I do not want to return to contact-center operations roles. | `PENDING_APPROVAL` |
| FI-006 | Responsibilities | Interested | AI enablement is a career direction I would love to explore, even if I need training. | `PENDING_APPROVAL` |
| FI-007 | Responsibilities | Rejected | I am not interested in another core-banking replacement transformation. | `PENDING_APPROVAL` |
| FI-008 | Responsibilities | Rejected | The title sounds fine, but rotating overnight on-call duties would be draining. | `PENDING_APPROVAL` |
| FI-009 | Compensation | Rejected | I like the client-facing AI work, but $110/hour is too low for this C2C job. | `PENDING_APPROVAL` |
| FI-010 | Compensation | Interested | The $140/hour C2C rate works for this opportunity and the scope is attractive. | `PENDING_APPROVAL` |
| FI-011 | Compensation | Rejected | The $80/hour rate is fine. I only dislike the onsite schedule. | `PENDING_APPROVAL` |
| FI-012 | Compensation | Interested | The $190,000 base salary is acceptable; I would need details on the bonus. | `PENDING_APPROVAL` |
| FI-013 | Compensation | Rejected | This could be fun, but $175,000 base is below my established minimum. | `PENDING_APPROVAL` |
| FI-014 | Compensation | Rejected | At $120/hour I still worry about months without billable work. | `PENDING_APPROVAL` |
| FI-015 | Compensation | Rejected | I do not want to invest time with employers who refuse to disclose base salary. | `PENDING_APPROVAL` |
| FI-016 | Compensation | Interested | The mission really resonates with me. I would need to confirm compensation. | `PENDING_APPROVAL` |
| FI-017 | Employer and industry | Rejected | I am uncomfortable with Northstar Tech after its recent layoffs. | `PENDING_APPROVAL` |
| FI-018 | Employer and industry | Rejected | I do not want to work in the tobacco industry. | `PENDING_APPROVAL` |
| FI-019 | Employer and industry | Interested | Helping small nonprofits apply AI would be meaningful to me. | `PENDING_APPROVAL` |
| FI-020 | Employer and industry | Rejected | I would hate a manager who micromanages every decision. | `PENDING_APPROVAL` |
| FI-021 | Employer and industry | Interested | I admire Verity Labs because the technical team seems thoughtful and collaborative. | `PENDING_APPROVAL` |
| FI-022 | Employer and industry | Rejected | I would do this job for a different firm, but not for Ridgetop Bank. | `PENDING_APPROVAL` |
| FI-023 | Work arrangement | Rejected | The three-days-in-office arrangement 45 miles away breaks my distance rule. | `PROFILE_FACT_REVIEW` |
| FI-024 | Work arrangement | Interested | I like being fully remote and could focus on the client work. | `PENDING_APPROVAL` |
| FI-025 | Work arrangement | Rejected | The required night and weekend coverage would interfere with my personal time. | `PENDING_APPROVAL` |
| FI-026 | Work arrangement | Interested | Hybrid is appealing at this nearby office, only six miles from home. | `PENDING_APPROVAL` |
| FI-027 | Work arrangement | Rejected | Flying every week would wear me out, though occasional trips are okay. | `PENDING_APPROVAL` |
| FI-028 | Work arrangement | Rejected | I would have to be onsite Mondays and Fridays, and it is 20 miles away. | `PROFILE_FACT_REVIEW` |
| FI-029 | Work arrangement | Rejected | The commute is a problem. | `NEEDS_CLARIFICATION` |
| FI-030 | Seniority and scope | Interested | I like being the trusted hands-on expert without managing a large team. | `PENDING_APPROVAL` |
| FI-031 | Seniority and scope | Rejected | Directly managing 20 people is not what I want to spend my time doing. | `PENDING_APPROVAL` |
| FI-032 | Seniority and scope | Interested | Owning a larger AI transformation portfolio is exactly the stretch I want. | `PENDING_APPROVAL` |
| FI-033 | Seniority and scope | Rejected | This is too junior; I would have almost no decision-making autonomy. | `PENDING_APPROVAL` |
| FI-034 | Seniority and scope | Rejected | The role seems too senior for me. | `NEEDS_CLARIFICATION` |
| FI-035 | Qualifications | Interested | I want to move into AI solution architecture, even though I would need to learn the tooling. | `PENDING_APPROVAL` |
| FI-036 | Qualifications | Rejected | I do not have the hands-on SAP integration experience this contract needs. | `PROFILE_FACT_REVIEW` |
| FI-037 | Qualifications | Rejected | I do not want my daily work to consist mostly of writing Python code. | `PENDING_APPROVAL` |
| FI-038 | Qualifications | Interested | I could do this project; I have already delivered these migrations. | `PROFILE_FACT_REVIEW` |
| FI-039 | Career category | Interested | AI evangelist roles genuinely excite me as a career direction. | `PENDING_APPROVAL` |
| FI-040 | Career category | Rejected | I do not want a career in quota-carrying sales. | `PENDING_APPROVAL` |
| FI-041 | Career category | Rejected | This is a terrific AI advisor role, but I do not trust the employer. | `PENDING_APPROVAL` |
| FI-042 | Career category | Rejected | I would love an AI product leadership career, just not at Omega Health. | `PENDING_APPROVAL` |
| FI-043 | Career category | Rejected | I love AI strategy consulting; this $105/hour C2C rate is not worthwhile. | `PENDING_APPROVAL` |
| FI-044 | Career category | Interested | This looks promising to me. | `NEEDS_CLARIFICATION` |
| FI-045 | Ambiguity and safeguards | Rejected | Not my thing. | `NEEDS_CLARIFICATION` |
| FI-046 | Ambiguity and safeguards | Rejected | The culture feels off. | `NEEDS_CLARIFICATION` |
| FI-047 | Ambiguity and safeguards | Rejected | The pay is fine, but it is not senior enough for the responsibility I want. | `PENDING_APPROVAL` |
| FI-048 | Ambiguity and safeguards | Rejected | The posting says 'must love sales'; that's exactly what I want to avoid. | `PENDING_APPROVAL` |
| FI-049 | Ambiguity and safeguards | Rejected | I like consulting as a career, but something about this opportunity feels wrong. | `NEEDS_CLARIFICATION` |
| FI-050 | Ambiguity and safeguards | Interested | I might take $165,000 base if the job were amazing; I want to reconsider my minimum. | `PROFILE_FACT_REVIEW` |

## 4. Quality bar for the first interpreter benchmark

These are **proposed acceptance thresholds**, not established results: (a) 100% prevention of hard-constraint mutation and unsupported career-category downgrades; (b) at least 95% correct dimension + context scope on clear-reference cases; (c) at least 90% recall of explicit atomic signals; (d) all ambiguity and profile-fact cases routed safely; and (e) all produced signals quote words present in the original feedback. Run the whole set at least twice at low randomness to look for inconsistent interpretations. With only 50 cases, this is a product gate, not statistical proof.

### Evaluation protocol

- Freeze this gold file and record its version. Do not adjust expected outputs to fit a model response without explicit test-case review.
- Run the proposed structured-output prompt over all 50 cases using the same model/prompt version. The AI must not see the expected answers.
- Compare emitted signals using exact feature + polarity + scope, allowing reviewed synonyms mapped to the controlled vocabulary.
- Record false positives, missed signals, unsupported evidence, overgeneralizations, and wrong clarification routes separately.
- Review each failure and either correct the prompt/ontology or make an explicitly approved gold-case change.
- Rerun the entire suite after every prompt/model/schema change. Preserve earlier run reports.

## 5. Recommendations, tradeoffs and risks

**MVP option:** an AI structured-output interpreter plus deterministic validators and immutable approval records. **Alternatives:** naive label-based preference updates (unsafe), hand-written NLP rules only (too brittle), or fine-tuning/training (unnecessary complexity).

**Risks:** self-referential test examples, ambiguous real-life language, conflicting signals across jobs, leakage of job facts into asserted preferences, salary thresholds inferred from isolated rejections, and overly broad category dislikes. Countermeasures are evidence spans, controlled scopes, human correction, a 50-case regression suite, and separate hard-rule workflows.

## 6. Next implementation-facing step

After human review of this gold set, define the exact Pydantic interpretation schema and prompt; run a genuine model benchmark using this JSON fixture; review failures before implementing the learning calculation. Do **not** claim interpretation accuracy until the model has actually been run and scored.

## 7. Future enhancements

Extend the gold suite with anonymized real feedback, paired contradictory examples, multilingual comments, calibrated confidence measures, and dataset-driven synonym/feature matching. Do not permit any of these enhancements to bypass explicit approval.
