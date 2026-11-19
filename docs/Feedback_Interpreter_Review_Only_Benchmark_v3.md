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
