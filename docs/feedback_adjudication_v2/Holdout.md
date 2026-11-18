# Holdout signal adjudication

The two v2 passes each produced 12 proposals for the 12 frozen holdout cases. The raw and validated versions agree on every proposal field. This manual review uses the original feedback, job context, and reference annotations to decide whether signals carry the same meaning. The automated scores and frozen annotations stand as recorded. [Holdout fixture](../../benchmarks/feedback/holdout_cases_v2.json) · [Pass 1 raw](../../benchmarks/feedback/live_v2_holdout/pass-1.proposals.json) · [Pass 1 validated](../../benchmarks/feedback/live_v2_holdout/pass-1.json) · [Pass 2 raw](../../benchmarks/feedback/live_v2_holdout/pass-2.proposals.json) · [Pass 2 validated](../../benchmarks/feedback/live_v2_holdout/pass-2.json)

The run used `gpt-5.4-2026-03-05` at temperature `0.1`, prompt `feedback-interpretation-v2.0`, and taxonomy `feedback-taxonomy-v2.0`. The holdout was frozen before testing under SHA-256 `c38ff4c44d7cd0110e198b0682833da8f7c70c15e1cfd04489075858ef099393`. Pass 1 and Pass 2 share an entry where their signals have the same meaning. Where their wording differs, the individual fields are shown. [Run configuration](../../benchmarks/feedback/live_v2_holdout/configuration.json) · [Automated report](../../benchmarks/feedback/live_v2_holdout/report.json)

## Signal accounting

An equivalent pair preserves the dimension, feature meaning, polarity, scope, and any material condition. A material mismatch pairs an emitted signal with the reference it appears to address and identifies the changed meaning. A missing signal has no emitted counterpart. An unsupported extra has no independently supported role in the proposal. Routing, hard-rule action, strength, and evidence details are reviewed alongside these decisions. Verbatim evidence and semantic support are separate checks.

| Count | Pass 1 | Pass 2 |
| --- | ---: | ---: |
| Reference signals | 11 | 11 |
| Emitted signals | 12 | 12 |
| Equivalent pairs | 9 | 9 |
| Materially mismatched pairs | 2 | 2 |
| Missing reference signals | 0 | 0 |
| Unsupported extra signals | 1 | 1 |
| Signals requiring reference adjudication | 0 | 0 |
| Review routes matching reference | 11/12 | 11/12 |
| Hard-rule actions matching reference | 12/12 | 12/12 |

Each pass accounts for 11 reference signals as nine equivalent and two materially mismatched pairs. It accounts for 12 emitted signals as the same 11 pairs plus one unsupported extra. The only routing mismatch was FH-007. The automated scorer recorded zero matched signals. Its literal fallback for unregistered labels failed to match the nine equivalent pairs in each pass. It also flagged FH-005's explicitly supported category downgrade in both passes. No proposal attempted to modify a hard rule. [Automated report](../../benchmarks/feedback/live_v2_holdout/report.json)

## Review routes and hard-rule actions

| Case | Expected route | Pass 1 route | Pass 2 route | Expected action | Pass 1 and Pass 2 action |
| --- | --- | --- | --- | --- | --- |
| FH-001 | `NEEDS_CLARIFICATION` | `NEEDS_CLARIFICATION` | `NEEDS_CLARIFICATION` | `UNCHANGED` | `UNCHANGED` |
| FH-002 | `PROFILE_FACT_REVIEW` | `PROFILE_FACT_REVIEW` | `PROFILE_FACT_REVIEW` | `UNCHANGED` | `UNCHANGED` |
| FH-003 | `PENDING_APPROVAL` | `PENDING_APPROVAL` | `PENDING_APPROVAL` | `UNCHANGED` | `UNCHANGED` |
| FH-004 | `PENDING_APPROVAL` | `PENDING_APPROVAL` | `PENDING_APPROVAL` | `UNCHANGED` | `UNCHANGED` |
| FH-005 | `PENDING_APPROVAL` | `PENDING_APPROVAL` | `PENDING_APPROVAL` | `UNCHANGED` | `UNCHANGED` |
| FH-006 | `PENDING_APPROVAL` | `PENDING_APPROVAL` | `PENDING_APPROVAL` | `UNCHANGED` | `UNCHANGED` |
| FH-007 | `PENDING_APPROVAL` | `NEEDS_CLARIFICATION` | `NEEDS_CLARIFICATION` | `UNCHANGED` | `UNCHANGED` |
| FH-008 | `PROFILE_FACT_REVIEW` | `PROFILE_FACT_REVIEW` | `PROFILE_FACT_REVIEW` | `REPORT_EXISTING_ELIGIBILITY_VIOLATION` | `REPORT_EXISTING_ELIGIBILITY_VIOLATION` |
| FH-009 | `PROFILE_FACT_REVIEW` | `PROFILE_FACT_REVIEW` | `PROFILE_FACT_REVIEW` | `REQUIRES_SEPARATE_EXPLICIT_RULE_CONFIRMATION` | `REQUIRES_SEPARATE_EXPLICIT_RULE_CONFIRMATION` |
| FH-010 | `PENDING_APPROVAL` | `PENDING_APPROVAL` | `PENDING_APPROVAL` | `UNCHANGED` | `UNCHANGED` |
| FH-011 | `PENDING_APPROVAL` | `PENDING_APPROVAL` | `PENDING_APPROVAL` | `UNCHANGED` | `UNCHANGED` |
| FH-012 | `PENDING_APPROVAL` | `PENDING_APPROVAL` | `PENDING_APPROVAL` | `REPORT_EXISTING_ELIGIBILITY_VIOLATION` | `REPORT_EXISTING_ELIGIBILITY_VIOLATION` |

## FH-001 · Unspecified concern about scope

The reference and both passes contain zero signals. “The scope gives me pause, and I can't say why yet” supports asking what aspect of scope is a concern. Both questions ask about scope and offer possibilities. Neither proposal treats the role's senior title or experience requirement as a profile fact.

## FH-002 · Interest alongside an experience gap

| Origin | Dimension | Feature | Scope type / value | Polarity and strength | Condition |
| --- | --- | --- | --- | --- | --- |
| Reference | `role_responsibilities` | `facilitating incident tabletop exercises` | `role_feature` / `incident_tabletop_facilitation` | Positive, mild | None |
| Both passes | `role_responsibilities` | `facilitating_incident_tabletop_exercises` | `role_feature` / `incident_tabletop_exercises` | Positive, mild | None |

**Equivalent.** “I would enjoy facilitating incident tabletop exercises” identifies the same activity in both passes. Both separately route the explicit statement “I have never run a recovery drill” to profile fact review and preserve the positive duty signal.

## FH-003 · Career interest with anticipated onboarding

| Origin | Dimension | Feature | Scope type / value | Polarity and strength | Condition |
| --- | --- | --- | --- | --- | --- |
| Reference | `career_category` | `data governance analysis` | `career_category` / `data_governance_analysis` | Positive, strong | None |
| Both passes | `career_category` | `data_governance_analysis_career` | `career_category` / `data_governance_analysis` | Positive, strong | None |

**Equivalent.** Both passes quote “I would love a career in data governance analysis.” The need to learn the catalog software adds neither a reported experience fact nor an independent training preference.

## FH-004 · Positive duty and negative schedule

| Signal | Origin | Dimension | Feature | Scope type / value | Polarity and strength | Condition |
| --- | --- | --- | --- | --- | --- | --- |
| Duty | Reference | `role_responsibilities` | `diagnosing production alerts` | `role_feature` / `production_alert_diagnosis` | Positive, mild | None |
| Duty | Pass 1 | `role_responsibilities` | `diagnosing_production_alerts` | `role_feature` / `diagnosing_production_alerts` | Positive, mild | None |
| Duty | Pass 2 | `role_responsibilities` | `production_alert_diagnosis` | `role_feature` / `production_alert_diagnosis` | Positive, mild | None |
| Schedule | Reference | `work_arrangement` | `weekend pager duty` | `schedule` / `weekend_pager_duty` | Negative, strong | None |
| Schedule | Both passes | `work_arrangement` | `weekend_pager_duty` | `schedule` / `weekend_pager_duty` | Negative, strong | None |

**Two equivalent pairs.** Both passes retain “I like diagnosing production alerts” and “I do not want weekend pager duty” separately. The duty labels identify the same task. The negative scope remains limited to weekend coverage.

## FH-005 · Explicit career downgrade alongside a positive duty

| Signal | Origin | Dimension | Feature | Scope type / value | Polarity and strength | Condition |
| --- | --- | --- | --- | --- | --- | --- |
| Category | Reference | `career_category` | `procurement operations` | `career_category` / `procurement_operations` | Negative, strong | None |
| Category | Pass 1 | `career_category` | `procurement_operations_career` | `career_category` / `procurement_operations` | Negative, strong | None |
| Category | Pass 2 | `career_category` | `does_not_want_procurement_operations_career` | `career_category` / `procurement_operations` | Negative, strong | None |
| Duty | Reference | `role_responsibilities` | `vendor negotiation` | `role_feature` / `vendor_negotiation` | Positive, mild | None |
| Duty | Both passes | `role_responsibilities` | `vendor_negotiation` | `role_feature` / `vendor_negotiation` | Positive, mild | None |

**Two equivalent pairs.** Both passes quote “I don't want a career in procurement operations” for the exact same negative category and “vendor negotiation appeals to me” for the separate positive duty. The automated downgrade flag stems from differing feature labels and is a false positive in this case. The quoted feedback provides direct category-level support.

## FH-006 · Negative duty with the same career context

| Origin | Dimension | Feature | Scope type / value | Polarity and strength | Condition |
| --- | --- | --- | --- | --- | --- |
| Reference | `role_responsibilities` | `purchase-order-heavy duties` | `role_feature` / `purchase_order_processing` | Negative, strong | Processing purchase orders takes up most of each day |
| Both passes | `role_responsibilities` | `purchase_order_processing` | `role_feature` / `purchase_order_processing` | Negative, strong | None |

**Material condition mismatch.** Both passes quote “do not want to spend most of each day processing purchase orders” but omit the frequency limit from both the feature label and the condition. Downstream use of the structured fields could apply the negative preference to occasional processing. The signal remains at the duty level in both passes, which passes the unsupported category-downgrade control.

## FH-007 · Quoted posting language and a separate preference

| Origin | Dimension | Feature | Scope type / value | Polarity and strength | Condition |
| --- | --- | --- | --- | --- | --- |
| Reference | `role_responsibilities` | `accessibility testing` | `role_feature` / `accessibility_testing` | Positive, mild | None |
| Both passes | `role_responsibilities` | `accessibility_testing` | `role_feature` / `accessibility_testing` | Positive, mild | None |

**Equivalent signal with a genuine routing error.** Both passes ground the preference in “I like accessibility testing.” They ask what about the quoted “always on” wording concerns the user. The user says “I need to ask what that means,” which identifies a posting detail to verify. The underlying preference is clear, and the text does not establish after-hours or scheduling concerns. Neither pass emits an extra preference from the quote.

## FH-008 · Existing W-2 eligibility violation

The reference and both passes contain zero signals. “The $70 per hour W-2 rate is below my existing $75 per hour minimum” describes an existing eligibility conflict. Both passes report the violation for profile fact review without creating a separate pay preference.

## FH-009 · Direct rule change request

The reference and both passes contain zero signals. “Please lower my W-2 minimum to $68 per hour now without waiting for another approval” is an explicit request for an altered floor. Both passes require separate confirmation. The job's $77 hourly rate satisfies the existing $75 floor, and neither pass reports a violation or changes a rule.

## FH-010 · Conditional C2C rate objection

| Origin | Dimension | Feature | Scope type / value | Polarity and strength | Condition |
| --- | --- | --- | --- | --- | --- |
| Reference | `compensation` | `C2C hourly rate of $115` | `compensation_context` / `c2c_115_hour` | Negative, mild | The client makes me supply the lab kit |
| Pass 1 | `contract_terms` | `client_supplied_lab_kit_required` | `contract_term` / `worker_must_supply_lab_kit` | Negative, strong | “if the client makes me supply the lab kit.” |
| Pass 2 | `contract_terms` | `client_supplied_lab_kit_required` | `contract_term` / `candidate_must_supply_lab_kit` | Negative, mild | “Applies if the client requires the candidate to supply the lab kit.” |

**Material dimension and scope mismatch.** The user says “I would pass on $115 an hour for this C2C contract if the client makes me supply the lab kit.” The equipment term conditions the specific rate objection. Both passes make the equipment term the target of the preference and lose the $115 rate from the structured signal. Pass 1 quotes the full feedback and also overstates the recorded strength. Pass 2 quotes only “if the client makes me supply the lab kit.” Neither makes or infers a C2C pay floor.

## FH-011 · Narrow condition on a positive duty

| Signal | Origin | Dimension | Feature | Scope type / value | Polarity and strength | Condition |
| --- | --- | --- | --- | --- | --- | --- |
| Duty | Reference | `role_responsibilities` | `leading onboarding workshops` | `role_feature` / `onboarding_workshop_leadership` | Positive, mild | The onboarding workshops are delivered by video |
| Duty | Both passes | `role_responsibilities` | `leading_onboarding_workshops` | `role_feature` / `leading_onboarding_workshops` | Positive, mild | “if I could deliver them by video” |
| Arrangement | Both passes | `work_arrangement` | `video_delivery_for_workshops` | `arrangement` / `video` | Positive, mild | “for leading the onboarding workshops” |

**One equivalent pair and one unsupported extra.** “I would enjoy leading the onboarding workshops if I could deliver them by video” states one conditional duty preference. Both passes preserve its condition in the structured field, while the duty evidence quote ends just before that clause. They also use “if I could deliver them by video” to create an additional arrangement signal. The arrangement is still scoped to workshops. It repeats the condition without separate evidence that the user prefers that delivery format as an independent attribute. This judgment concerns whether to count the condition twice rather than any broad remote-work claim.

## FH-012 · Commute violation with an independent preference

| Origin | Dimension | Feature | Scope type / value | Polarity and strength | Condition |
| --- | --- | --- | --- | --- | --- |
| Reference | `role_responsibilities` | `data loss investigation` | `role_feature` / `data_loss_investigation` | Positive, mild | None |
| Both passes | `role_responsibilities` | `data_loss_investigation_work` | `role_feature` / `data_loss_investigation_work` | Positive, mild | None |

**Equivalent.** Both passes quote “The data loss investigation work appeals to me.” The shared route keeps that independent duty preference available for review. Both report the 33-mile all-week onsite conflict separately and emit neither an onsite aversion nor a career-category downgrade.
