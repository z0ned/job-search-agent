# Live feedback interpreter benchmark v2 report

The v2 prompt improved gold-suite route accuracy from 44/50 to 48/50 in each pass. Canonical recall on the same 57 reference signals fell from 21/57 to 17/57 and 16/57. Both live suites missed the quality gates, so the interpreter should remain in review-only use. [Specification](Feedback_Interpreter_Benchmark_Spec_v2.md) · [Case-level analysis](Feedback_Interpreter_Failure_Analysis_v2.md)

## Runs and provenance

All live runs used `gpt-5.4-2026-03-05` at temperature `0.1` with independent requests to the OpenAI Responses API. The gold fixture remained `1.0-draft`, SHA-256 `fbf6872f847d533871ad2db7d3412a324504171f057f56ae7a8f1f8f48311523`. The 12-case holdout was authored without access to model predictions and frozen before the prompt changes. [Frozen gold suite](../feedback_interpretation_gold_cases_v1.json) · [Holdout suite](../benchmarks/feedback/holdout_cases_v2.json)

The original v1 report is preserved byte for byte. It contains the literal scores and individual failure classifications. The original runner did not serialize proposals, so a separate two-pass v1 run with the same configuration captured them. Its predictions were replayed through the v2 evaluator to isolate the scoring change from the prompt change. The replay reproduced the rerun's legacy literal report metrics and failure records. [Original report](../benchmarks/feedback/live_v1_original_report.json) · [Captured v1 rerun](../benchmarks/feedback/live_v1_capture.json)

The v2 live run completed 100 gold requests in 215.1 seconds and 24 holdout requests in 52.9 seconds. No API or validation errors occurred. Both reports include case-level correct, missed, extra, incorrectly scoped, and incorrectly conditioned signals. Every case has a raw proposal and corresponding validated prediction. [Gold v2 report](../benchmarks/feedback/live_v2_gold/report.json) · [Holdout v2 report](../benchmarks/feedback/live_v2_holdout/report.json) · [Capture index](../benchmarks/feedback/README.md)

## Gold suite results

Each pair is pass 1 / pass 2. The original run has no canonical scores because the individual proposals from that run are unavailable.

| Measure | Original v1 live | Captured v1 rerun, scored with v2 | v2 live |
| --- | --- | --- | --- |
| Literal exact cases | 4/50 · 4/50 | 4/50 · 4/50 | 7/50 · 7/50 |
| Literal signal recall | 1/57 · 1/57 | 1/57 · 1/57 | 1/57 · 1/57 |
| Literal signal precision | 1/68 · 1/69 | 1/70 · 1/69 | 1/57 · 1/58 |
| Literal clear-case dimension and scope | 7/39 · 7/39 | 6/39 · 7/39 | 5/39 · 4/39 |
| Canonical signal recall | — | 21/57 · 21/57 | 17/57 · 16/57 |
| Canonical signal precision | — | 21/70 · 21/69 | 17/57 · 16/58 |
| Canonical clear-case dimension and scope | — | 14/39 · 15/39 | 13/39 · 13/39 |
| Review routing | 44/50 · 44/50 | 44/50 · 44/50 | 48/50 · 48/50 |
| Safe routing on ambiguity and profile-fact cases | 6/11 · 6/11 | 6/11 · 6/11 | 9/11 · 9/11 |
| Authorized hard-rule actions | — | 50/50 · 50/50 | 50/50 · 50/50 |
| Cases clear of canonical downgrade flags | — | 50/50 · 50/50 | 49/50 · 49/50 |
| Verbatim evidence | 68/68 · 69/69 | 70/70 · 69/69 | 57/57 · 58/58 |

Both v2 gold passes failed the canonical recall, clear-case dimension and scope, safe-routing, and downgrade gates. Both incorrectly routed FI-028 and FI-044. FI-040's downgrade flag was an alias coverage issue. All 100 proposals preserved hard rules and used the expected hard-rule actions. The gold v2 passes agreed on 38/50 cases under the literal consistency check and 39/50 under the canonical check. [Gold failure analysis](Feedback_Interpreter_Failure_Analysis_v2.md#gold-suite-findings-from-both-v2-passes)

## Holdout results

| Measure | Pass 1 | Pass 2 |
| --- | --- | --- |
| Literal exact cases | 3/12 | 3/12 |
| Literal and canonical signal recall | 0/11 | 0/11 |
| Literal and canonical signal precision | 0/12 | 0/12 |
| Literal and canonical clear-case dimension and scope | 4/8 | 5/8 |
| Review routing | 11/12 | 11/12 |
| Safe ambiguity and profile-fact routing | 4/4 | 4/4 |
| Authorized hard-rule actions and non-mutation | 12/12 | 12/12 |
| Cases clear of canonical downgrade flags | 11/12 | 11/12 |
| Verbatim evidence | 12/12 | 12/12 |

Both holdout passes failed canonical scope, recall, and downgrade gates. The passes agreed on 9/12 cases under both consistency checks. The zero automated signal score reflects how the scorer treats unregistered terms. The manual review found clear examples of successful extraction with unseen labels and confirmed that FH-005's quote explicitly supports the flagged procurement operations downgrade. It also found genuine errors in preserving frequency and rate qualifiers, avoiding duplicate conditional signals, and routing a request to verify a posting detail. [Holdout failure analysis](Feedback_Interpreter_Failure_Analysis_v2.md#holdout-findings-from-both-v2-passes)

## Readiness recommendation

**Hold learning-engine integration.** The hard-rule safeguards passed, while genuine routing, scope, and grounding problems remained across both suites. Review the proposed gold annotations, establish a review process for equivalent unseen labels, and investigate the remaining failures with the two disputed downgrade flags visible. Require two clean passing runs on both an approved gold suite and an independent holdout before reconsidering integration. [Gold review proposals](Feedback_Interpreter_Gold_Review_v2.md)
