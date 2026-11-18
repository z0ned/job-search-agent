# Live feedback interpreter benchmark v3

**Decision for review.** The prototype used one model call, retained independently supported preferences across review routes, and held every proposal for review. All 148 live requests completed. None of the three suites passed the approved gates. Learning integration remains on hold. [Prototype](Feedback_Interpreter_Prototype_v3.md) · [Benchmark design and gates](Feedback_Interpreter_Benchmark_Design_v3.md)

## Configuration and provenance

- Inference used commit `9b3ce5c48183f71b697052d8ccf5b33b5fb52283`, Python 3.12.14, prompt `feedback-interpretation-v3.0`, model `gpt-5.4-2026-03-05`, and temperature `0.1`. The Responses API requests used `store: false`. Each suite ran two independent passes. Gold took 263.3 seconds, regression 66.7 seconds, and fresh holdout 69.1 seconds. The suites ran concurrently. [Gold live configuration](../benchmarks/feedback/live_v3_gold/configuration.json)
- Gold used the 50 approved cases and 51 expected signals, with SHA-256 `600677336c0ddcbc6dfe67a2532426a083300661100d8a8ea507680903177bbe`. The old 12-case holdout served as a regression suite. The fresh 12-case holdout was authored independently and sealed before inference, with SHA-256 `e3c046bcbc6e5012e09fa5e8404211ab4a2938f2e7599681283c28b1253caa96`. The original v1 and v2 fixtures and run artifacts remain available. [Approved reference decisions](Feedback_Interpreter_Reference_Decisions_v3.md) · [Gold v3 fixture](../benchmarks/feedback/gold_cases_v3.json) · [Fresh holdout](../benchmarks/feedback/holdout_cases_v3.json)
- Codex reviewers compared both saved variants against their references with pass identities and registry IDs masked. They recorded one-to-one equivalent pairs, case-level scope, route resolution, and evidence and safety findings. The evaluator scored those case verdicts during offline replay, with hashes linking them to the exact live captures. The verdicts are available for human review. [Run archive](../benchmarks/feedback/README.md)

## Adjudicated results

Each cell gives pass 1 / pass 2. Semantic precision counts validated emitted signals. Validator rejections are tracked separately as failed clean-pass checks. Clear-case scope requires a complete, correctly scoped match of the reference for that case.

| Measure | Approved gold | Earlier holdout regression | Fresh sealed holdout |
| --- | --- | --- | --- |
| Semantic recall, target ≥90% | 33/51 · 35/51 | 9/11 · 9/11 | 10/14 · 10/14 |
| Semantic precision, target ≥90% | 33/42 · 35/43 | 9/9 · 9/9 | 10/13 · 10/12 |
| Clear-case dimension and scope, target ≥95% | 21/38 · 22/38 | 6/8 · 6/8 | 4/8 · 4/8 |
| Review route agreement | 49/50 · 49/50 | 11/12 · 11/12 | 11/12 · 10/12 |
| Safe clarification and profile routing, target 100% | 12/12 · 12/12 | 4/4 · 4/4 | 3/4 · 3/4 |
| Expected hard-rule action, target 100% | 50/50 · 50/50 | 12/12 · 12/12 | 11/12 · 11/12 |
| Validator rejection records | 8 · 8 | 2 · 2 | 0 · 1 |

Every emitted signal passed mechanical evidence-anchor checks. Some signals still lost qualifiers, broadened their scope, or attributed an unsupported meaning to a valid quote. The review found no unsupported negative career downgrade or unauthorized rule mutation. The fresh holdout's failed rule-action gate came from omitting separate confirmation for an explicit request. [Gold adjudication](../benchmarks/feedback/live_v3_gold/adjudicated-report.json) · [Regression adjudication](../benchmarks/feedback/live_v3_regression/adjudicated-report.json) · [Fresh holdout adjudication](../benchmarks/feedback/live_v3_holdout/adjudicated-report.json)

The frozen literal comparison credited zero signal matches in all six passes. Registry-identity matching credited 8 and 9 gold signals and zero on both 12-case suites. Those checks diagnose wording and catalog coverage. The adjudicated scores assess meaning. The replay's automated stability check counted 36/50 gold, 8/12 regression, and 10/12 fresh holdout cases with unchanged signatures. As one documented representation difference, the reviewers credited FH-006's typed workload share as preserving the legacy reference's intrinsic limit. [Adjudication implementation](../src/job_search_agent/feedback_adjudication_v3.py)

## Findings to carry forward

| Finding | Evidence and narrow correction |
| --- | --- |
| Deterministic routing fixed several v2 failures | FI-028 reports the commute violation and emits zero preferences. FI-044 asks what looks promising. FH-007 preserves accessibility-testing interest and carries the posting question as verification. These are useful regression controls. |
| The extraction can be right while the validator loses the signal | In FH-010 both raw proposals correctly preserve the conditional $115/hour C2C objection. Both cite the verified `hourly_rate_usd` field as evidence for USD. The validator rejects that source for currency and the missing signal triggers clarification. FI-012 loses its positive base-salary preference through a similar basis-source mismatch. Derive currency and pay basis in code from trusted typed fields and keep source validation for the actual amount. |
| A correct eligibility result can coexist with an extraction error | In FI-013 and FH-008 the deterministic validator prevents a below-floor clause from becoming a preference. The model still attempted one in each pass, so both cases carry rejection records. Retain that safeguard and test the original raw clause classification separately. |
| The rule-review recognizer misses an explicit request | In FH3-002 both model proposals correctly identify the request to revisit the confirmed 1099 minimum and retain the independent positive duty. The deterministic recognizer rejects the request wording, returning unchanged and clarification. Extend the recognized rule target grammar with a grounded explicit-request regression. |
| Typed scope and coverage still need work | Weekly travel retained air mode and frequency in FI-027. Other gold cases still lost daily workload, salary-basis information, autonomy limits, or strong sales emphasis. FH3-010 preserves a frequency upper bound as scope and omits the explicit applicability condition. FH3-011 omits an independent positive reaction to the posting. Keep the approved distinctions when adding captured-output regression tests. |

The most useful follow-up is to fix verified pay metadata and explicit rule-target recognition first. Replay the saved cases through those deterministic changes to measure recovery separately from live extraction. Keep the existing reports frozen when comparing the next version.

## Reproduce the review from captures

The replay uses the saved predictions and their hash-bound verdicts. It requires no API call. Exit status 1 indicates that a completed scorecard missed one or more acceptance gates.

```sh
PYTHONPATH=src python -m job_search_agent.feedback_evaluation_v3 \
  benchmarks/feedback/gold_cases_v3.json --suite gold \
  --predictions benchmarks/feedback/live_v3_gold/pass-1.json \
  --predictions benchmarks/feedback/live_v3_gold/pass-2.json \
  --adjudications benchmarks/feedback/live_v3_gold/pass-1.adjudication.json \
  --adjudications benchmarks/feedback/live_v3_gold/pass-2.adjudication.json
```

The prototype passed 74 local tests before the live run. The final code and replay checks passed 82 tests. The scorer added post-capture diagnostics and verified the original captures through offline replay.
