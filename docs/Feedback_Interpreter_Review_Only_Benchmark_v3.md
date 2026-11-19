# Feedback interpreter review-only benchmark

This comparison tests the interpreter on full comments with no supplied quote inventory. The previous focused experiments identified specific failure modes. Their cases and captures remain regression evidence. [Prior focused results](Feedback_Interpreter_Focused_Context_Trial_v3.md#results) · [Offline validation repairs](Feedback_Interpreter_Validation_Repair_Trial_v3.md)

## Protocol frozen before inference

The baseline is the current one-call v3 interpreter. The candidate runs the same model request, then applies the verified deterministic repairs for contiguous employer exceptions, redundant anchored intensity qualifiers, and explicit applicability conditions. It retains the validated scope and omission findings for human review. Both arms use the same existing quote validation, review routing, and hard-rule checks. Every accepted signal stays held for review. The benchmark entry point is isolated from the default interpreter. [Candidate repair implementation](../src/job_search_agent/feedback_validation_repair_trial_v3.py) · [Condition recovery](Feedback_Interpreter_Evidence_Review_v3.md#offline-evidence)

Run both arms twice on 12 independently authored realistic synthetic comments. Freeze the case references, high-risk case IDs, protocol, and source revision before inference. The comments cover explicit and mixed preferences, vague feedback, profile facts and verification, policy and pay requests, explicit scope limits, and examples where a posting fact or a duty supplies no career-level preference. The model receives the full original comment, decision, posting context, and approved hard rules. It receives no selected quotes, references, or other predictions. [Fresh holdout](../benchmarks/feedback/review_only_holdout_v3.json)

Use `gpt-5.4-2026-03-05` at temperature `0.1`. Alternate which arm runs first and reverse the order in the second pass. Use one request per arm and case in each pass, for 48 planned requests. Keep prompts and response schemas identical. Capture the parsed raw responses, validated outputs, repair diagnostics, trace, and run configuration. Revalidate the saved proposals with both deterministic paths offline to distinguish changes caused by the repairs from sampling differences between independent requests.

## Evaluation

Score both passes separately under the agreed v3 criteria. Match full preference meaning including polarity, dimension, scope, material qualifiers, and conditions. Use separate masked reviews of the raw and validated outputs. Keep literal and registered-identity metrics for comparison. Record missing and extra preferences, evidence support, validation rejections, routing and whether the question or fact is specific enough, and authorized advisory hard-rule actions. [Approved benchmark criteria](Feedback_Interpreter_Benchmark_Design_v3.md#assessment-of-the-original-acceptance-criteria)

The candidate must meet the agreed ≥90% semantic precision and recall and ≥95% clear-case dimension and scope on each pass. Require complete runs, adequately resolved ambiguous and profile-review cases, correct high-risk controls, grounded evidence, clean validation, and zero unsupported career downgrades or unauthorized hard-rule actions or mutations. Report any unsafe raw proposals separately. Count clarification, profile review, separate rule confirmation, and evidence or validator flags to show additional review workload. Every proposal already requires routine approval. Additional review counts describe the work a reviewer might see and do not measure actual reviewer time.

## Pre-inference regression checks

The candidate recovered the two previously dropped signals and the two explicit conditions in the saved repair controls. It preserved the neutral, career, and rule-confirmation controls and rejected the unsupported cross-clause qualifier. The saved vague-approval misclassification still reproduces with both validators. These results verify the repair paths and identify known evidence that the fresh trial must evaluate independently. [Archived regression replay](../benchmarks/feedback/offline_v3_review_only_regressions.json)

## Capture command

Run from the repository root with a new output directory.

```sh
PYTHONPATH=src python -m job_search_agent.feedback_review_only_trial_v3 \
  --output /tmp/feedback-v3-review-only
```

## Results

**The candidate and baseline tied on both fresh passes, and both missed the agreed gates.** Each had 11/12 for semantic precision and recall on each pass. The two failures were a generic clarification question and a missing limit in a travel preference. The deterministic repairs produced no material output changes when applied to each of the 48 captured proposals. [Semantic scorecard](../benchmarks/feedback/live_v3_review_only_trial/semantic-report.json) · [Same-proposal replay](../benchmarks/feedback/live_v3_review_only_trial/deterministic-replay.json)

The model settings, case references, protocol, and candidate were frozen at `001a8db78df18aa2fa3fefcebea0a831b68e7447` before inference. All 48 requests completed without API or execution errors in 107.18 seconds of summed model time. Request traces confirmed that the two arms used identical source, prompt, and schema. Four independent reviewers scored the raw and validated outputs with arm identity masked. One grounding disagreement for the identical travel output was reconciled against the original scope in both passes. The source evidence and original reviewer judgments are retained. [Configuration](../benchmarks/feedback/live_v3_review_only_trial/configuration.json) · [Request trace](../benchmarks/feedback/live_v3_review_only_trial/request-trace.json) · [Adjudications](../benchmarks/feedback/live_v3_review_only_trial/adjudications.json) · [Reconciliation](../benchmarks/feedback/live_v3_review_only_trial/review-reconciliation.json)

| Measure across both passes | Baseline | Candidate |
| --- | ---: | ---: |
| Raw and validated semantic precision | 22/24 | 22/24 |
| Raw and validated semantic recall | 22/24 | 22/24 |
| Missed reference signals | 2 | 2 |
| Extra signals outside the reference match | 2 | 2 |
| Clear cases with all dimension and scope details correct | 10/12 | 10/12 |
| Fully correct end-to-end records | 20/24 | 20/24 |
| Correct route labels | 24/24 | 24/24 |
| Adequate route resolutions | 22/24 | 22/24 |
| Correct hard-rule actions | 24/24 | 24/24 |
| Cases requiring further review | 12/24 | 12/24 |
| Validation rejections, unsupported career downgrades, or unauthorized hard-rule actions and mutations | 0 | 0 |
| Passes clearing all gates | 0/2 | 0/2 |

The two misses and two extras per arm come from two instances of the same incomplete travel scope. Each instance is a missed exact semantic match and an extra, broader proposal. Each arm sent six records to clarification and six to profile or fact review, including two separate rule confirmations. The remaining 12 records went to routine approval, and all proposals stayed held. Exact-string case matching returned 4/12 each pass. Literal and registered-identity matching each credited zero signals. The independent semantic review is the accuracy measure for the agreed gates. [Capture diagnostics](../benchmarks/feedback/live_v3_review_only_trial/report.json)

| Case | Failure in each arm and pass |
| --- | --- |
| RO3-004 | The model identified a posting verification about whether overnight work was occasional or the usual schedule. The validator kept that detail. The routing fallback asked what had influenced the user's reaction, losing the specific question. This failed the special-route and high-risk resolution criteria. |
| RO3-011 | “One overnight trip a quarter works for me” became an acceptance of overnight travel with `frequency: a quarter`. The exact source quote remained attached. The proposal omitted the one-trip limit, so it failed the semantic and clear-scope match. The separate weekly overnight objection was correct. |

The fresh benchmark supports keeping the interpreter review-only. It provides specific evidence about two boundaries of the existing pipeline. Passing a source-grounded verification question to the review route would address the first. Preserving quantity alongside frequency needs a separate scope check. The tested deterministic repairs remain useful on their archived controls. This trial provides no fresh evidence that they improve end-to-end results, and automatic learning remains on hold.
