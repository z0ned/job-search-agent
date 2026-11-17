# Feedback interpreter benchmark

## Exploratory blinded runs

Two independent Codex session runs each interpreted all 50 original scenarios. Each run used two batches of 25 inputs. The inference sessions received the prototype instructions, proposal schema, job context, written feedback, and benchmark hard-rule assumptions. Gold labels were reserved for scoring. The prototype validator processed every model proposal. Sampling controls were unavailable for this run type. The live OpenAI Responses API benchmark is pending credential configuration.

The fixture version was `1.0-draft` and its SHA-256 was `fbf6872f847d533871ad2db7d3412a324504171f057f56ae7a8f1f8f48311523`. The prompt version was `feedback-interpretation-v1.0`. [Original design](../feedback_interpretation_design_v1.md) · [Original fixture](../feedback_interpretation_gold_cases_v1.json)

| Measure | Pass 1 | Pass 2 | Design target |
| --- | ---: | ---: | ---: |
| Exact case matches | 9/50 (18%) | 9/50 (18%) | |
| Review route accuracy | 49/50 (98%) | 49/50 (98%) | |
| Ambiguity and profile fact cases routed safely | 11/11 | 11/11 | 100% |
| Clear-case exact dimension and context scope | 5/39 (12.8%) | 5/39 (12.8%) | ≥95% |
| Clear-case dimension and scope type only | 29/39 (74.4%) | 30/39 (76.9%) | Diagnostic |
| Exact atomic signal recall | 2/57 (3.5%) | 0/57 (0%) | ≥90% |
| Exact atomic signal precision | 2/53 (3.8%) | 0/53 (0%) | |
| Expected hard-rule action | 50/50 | 50/50 | |
| No hard-rule mutation | 50/50 | 50/50 | 100% |
| Verbatim evidence on emitted signals | 53/53 | 53/53 | 100% |

The evaluator recorded 55 missing and 51 extra exact signals in pass 1, and 57 missing and 53 extra exact signals in pass 2. The exact comparison uses the literal feature label, polarity, scope type, and scope value. It counts a changed label as both a miss and an extra. Eleven cases kept the same route, rule action, and signal classifications across both runs. All 100 proposals passed deterministic validation. Both runs missed the design's strict scope and signal-recall targets.

### Representative failures

- FI-013 was incorrectly sent to profile fact review in pass 1. Pass 2 retained a role signal but marked it uncertain. Both passes correctly flagged the eligibility issue.
- FI-035 was sent to profile fact review in pass 2 after the user said they would need to learn the tooling. The fixture expects a preference proposal that keeps the career interest and training opportunity distinct.
- Both passes categorized FI-007 as duties instead of a career category. Both omitted the client-work signal in FI-024 and the conditional role interest in FI-050.
- FI-001 and FI-027 illustrate different labels for equivalent concepts. In FI-040 the strict downgrade check flagged `quota_carrying_sales` against `quota_sales` in both passes. The user explicitly disapproved of a career in quota-carrying sales, so the flagged category and polarity had direct support.
- Both passes added conditional willingness to perform FI-022's duties at another employer. The reference captures only the employer objection. This is a candidate for label review.

### Recommendations before approval

1. Define stable feature and context labels and review synonyms independently from the model outputs. Keep literal and adjudicated scores visible so wording differences and missed meanings can be tracked independently.
2. Clarify the distinction between confirmed qualification claims and willingness to learn. Require the interpreter to preserve independent preferences alongside eligibility problems and rule-change requests.
3. Run two low-temperature passes with the intended OpenAI model and review the per-case failures before enabling downstream use.

### Case-level exact mismatches

The counts below use literal signal matching. A zero count can still have an exact-case mismatch in a route, evidence span, or another signal field.

| Case | Pass 1 | Pass 2 |
| --- | --- | --- |
| FI-001 | 1 missing, 1 extra (feature, scope, evidence_quote) | 1 missing, 1 extra (feature, scope, evidence_quote) |
| FI-002 | 2 missing, 2 extra (feature, scope, evidence_quote) | 2 missing, 2 extra (feature, scope, evidence_quote) |
| FI-003 | 2 missing, 2 extra (feature, scope, evidence_quote) | 2 missing, 2 extra (feature, scope, evidence_quote) |
| FI-004 | 2 missing, 2 extra (feature, strength, scope, condition, evidence_quote) | 2 missing, 1 extra (dimension, feature, polarity, strength, scope, condition, evidence_quote) |
| FI-005 | 1 missing, 1 extra (feature, evidence_quote) | 1 missing, 1 extra (feature, evidence_quote) |
| FI-006 | 2 missing, 1 extra (dimension, feature, polarity, strength, scope, condition, evidence_quote) | 2 missing, 1 extra (dimension, feature, polarity, strength, scope, condition, evidence_quote) |
| FI-007 | 1 missing, 1 extra (dimension, feature, strength, scope, evidence_quote) | 1 missing, 1 extra (dimension, feature, strength, scope, evidence_quote) |
| FI-008 | 1 missing, 1 extra (feature, strength, scope) | 1 missing, 1 extra (feature, strength, scope) |
| FI-009 | 2 missing, 2 extra (feature, strength, scope, evidence_quote) | 2 missing, 2 extra (feature, strength, scope, evidence_quote) |
| FI-010 | 2 missing, 2 extra (feature, scope, evidence_quote) | 2 missing, 2 extra (feature, scope, evidence_quote) |
| FI-011 | 2 missing, 2 extra (feature, scope, evidence_quote) | 2 missing, 2 extra (feature, scope, evidence_quote) |
| FI-012 | 1 missing, 1 extra (feature, scope, evidence_quote) | 1 missing, 1 extra (feature, scope, evidence_quote) |
| FI-013 | 1 missing, 0 extra, wrong route (dimension, feature, polarity, strength, scope, condition, evidence_quote) | 1 missing, 1 extra (feature, polarity, scope) |
| FI-014 | 1 missing, 1 extra (feature, strength, scope, evidence_quote) | 1 missing, 1 extra (feature, strength, scope, evidence_quote) |
| FI-015 | 1 missing, 1 extra (feature, scope, evidence_quote) | 1 missing, 1 extra (feature, scope, evidence_quote) |
| FI-016 | 1 missing, 1 extra (feature, scope, evidence_quote) | 1 missing, 1 extra (feature, scope, evidence_quote) |
| FI-017 | 1 missing, 1 extra (feature, evidence_quote) | 1 missing, 1 extra (feature, evidence_quote) |
| FI-018 | 1 missing, 1 extra (feature, evidence_quote) | 1 missing, 1 extra (feature, evidence_quote) |
| FI-019 | 1 missing, 1 extra (feature, strength, scope) | 1 missing, 1 extra (feature, strength, scope) |
| FI-020 | 1 missing, 1 extra (feature, scope, evidence_quote) | 1 missing, 1 extra (feature, scope, evidence_quote) |
| FI-021 | 1 missing, 1 extra (feature, scope, evidence_quote) | 2 missing, 2 extra (feature, strength, scope, evidence_quote) |
| FI-022 | 1 missing, 2 extra (dimension, feature, polarity, strength, scope, condition, evidence_quote) | 1 missing, 2 extra (dimension, feature, polarity, strength, scope, condition, evidence_quote) |
| FI-024 | 2 missing, 1 extra (dimension, feature, polarity, strength, scope, condition, evidence_quote) | 2 missing, 1 extra (dimension, feature, polarity, strength, scope, condition, evidence_quote) |
| FI-025 | 1 missing, 1 extra (feature, strength, scope, evidence_quote) | 1 missing, 1 extra (feature, strength, scope, evidence_quote) |
| FI-026 | 1 missing, 1 extra (feature, scope, condition, evidence_quote) | 1 missing, 1 extra (feature, scope, evidence_quote) |
| FI-027 | 2 missing, 2 extra (feature, strength, scope) | 2 missing, 2 extra (feature, strength, scope) |
| FI-030 | 2 missing, 2 extra (feature, strength, scope, condition, evidence_quote) | 2 missing, 2 extra (feature, strength, scope, condition, evidence_quote) |
| FI-031 | 1 missing, 1 extra (feature, scope, evidence_quote) | 1 missing, 1 extra (feature, scope, evidence_quote) |
| FI-032 | 1 missing, 1 extra (feature, scope, evidence_quote) | 1 missing, 1 extra (feature, scope, evidence_quote) |
| FI-033 | 1 missing, 1 extra (feature, scope, evidence_quote) | 1 missing, 1 extra (feature, scope, evidence_quote) |
| FI-035 | 2 missing, 1 extra (dimension, feature, polarity, strength, scope, condition, evidence_quote) | 2 missing, 1 extra, wrong route (dimension, feature, polarity, strength, scope, condition, evidence_quote) |
| FI-037 | 1 missing, 1 extra (feature, scope, evidence_quote) | 1 missing, 1 extra (feature, scope, evidence_quote) |
| FI-039 | 1 missing, 1 extra (feature, scope, evidence_quote) | 1 missing, 1 extra (feature, scope) |
| FI-040 | 1 missing, 1 extra (feature, scope, evidence_quote) | 1 missing, 1 extra (feature, scope, evidence_quote) |
| FI-041 | 2 missing, 2 extra (feature, strength, scope, evidence_quote) | 2 missing, 2 extra (feature, strength, scope, evidence_quote) |
| FI-042 | 2 missing, 2 extra (feature, strength, evidence_quote) | 2 missing, 2 extra (feature, strength, evidence_quote) |
| FI-043 | 1 missing, 1 extra (feature, evidence_quote) | 2 missing, 2 extra (feature, evidence_quote) |
| FI-047 | 2 missing, 2 extra (feature, strength, scope, evidence_quote) | 2 missing, 2 extra (feature, scope, evidence_quote) |
| FI-048 | 1 missing, 1 extra (feature, scope, evidence_quote) | 1 missing, 1 extra (feature, scope, evidence_quote) |
| FI-049 | 1 missing, 1 extra (feature, evidence_quote) | 1 missing, 1 extra (feature, evidence_quote) |
| FI-050 | 1 missing, 0 extra (dimension, feature, polarity, strength, scope, condition, evidence_quote) | 1 missing, 0 extra (dimension, feature, polarity, strength, scope, condition, evidence_quote) |
