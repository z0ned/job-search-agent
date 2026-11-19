# Feedback interpreter offline claim-review replay

The live signal-independence trial left schema-valid extra claims in the validated output. This replay tests a separate disposition step on those saved outputs. It measures what a review step can preserve, demote to context, or hold for judgment. [Prior live trial](Feedback_Interpreter_Independence_Trial_v3.md#results)

## Review protocol

Use both validated arms of the ten-case signal-independence trial, including the records with no validated signals. Two Codex reviewers independently read the original feedback, decision, posting context, and the evidence and scope attached to each saved signal. Mask case IDs and arm labels and withhold reference expectations and earlier adjudications. Each proposed signal receives one disposition with a rationale.

- `independent` means the evidence supports a distinct preference. Separate claims can share a subject, polarity, sentence, or evidence.
- `explanatory` means the claim summarizes, explains, or restates another preference without adding an independent evaluation. It must link to a retained independent signal in the same record.
- `unresolved` means the evidence leaves a materially different reading open or the reviewers disagree. Keep the claim and its evidence available for review.

Accept an agreed disposition only if both reviewers also agree on the linked signal for an explanation. Hold disagreements and explanations without an agreed independent target as unresolved. Apply decisions to exactly the hashed saved predictions. Keep the original saved records, including review route, profile fact, validation findings, hard-rule action, and evidence. The replay writes an index projection and has no inference or application path. It cannot restore a signal rejected before this stage.

After decisions are sealed, compare their projections with the prior signal-level adjudications. Report the original matches, unsupported extras demoted as explanations, correctly matched signals lost or held, unresolved claims, dimension and scope disagreements, and continuing validator losses. Show semantic precision and recall for independent signals alongside the full unresolved count. Treat unresolved cases as incomplete even when the retained signal list matches. These are diagnostic comparisons of manual dispositions on saved cases. Measuring an automated judge and generalization requires a separate evaluation.

## Results

**The replay made review decisions traceable and left the promotion gate unmet.** Reviewers agreed on 22 of 26 dispositions across 20 saved records. They demoted two instances of the same synthetic extra to context, held four reference-matched proposals for review, and retained the broader FI-033 claim that the approved reference scores as an extra. No model API requests were made. [Individual decisions](../benchmarks/feedback/offline_v3_claim_review/reviews.json) · [Consensus decisions](../benchmarks/feedback/offline_v3_claim_review/decisions.json) · [Comparison](../benchmarks/feedback/offline_v3_claim_review/comparison.json)

| Measure | Control before | Control replay | Treatment before | Treatment replay |
| --- | ---: | ---: | ---: | ---: |
| Semantic precision of listed preferences | 11/14 | 9/11 | 9/12 | 7/9 |
| Semantic recall of listed preferences | 11/12 | 9/12 | 9/12 | 7/12 |
| Complete signal cases with no unresolved claims | 7/10 | 7/10 | 5/10 | 5/10 |
| Correct archived review routes | 10/10 | 10/10 | 9/10 | 9/10 |
| Correct archived hard-rule actions | 10/10 | 10/10 | 10/10 | 10/10 |

Replay precision and recall use the independent list. The four unresolved signals remain linked to their original evidence and count as missed in that list. The two demotions affected only unsupported extras. Both arms use the same source feedback, so the 20 records cover ten distinct cases. [Replay projection](../benchmarks/feedback/offline_v3_claim_review/replay.json)

| Case | What the source-only review found |
| --- | --- |
| FI-033 | Both reviewers accepted “too junior” as the primary evaluated claim. One treated the near-zero autonomy clause as its reason. The other considered an independent autonomy objection plausible but unresolved. The replay retained the broader claim and held the narrower one. The approved reference scores only the specific autonomy objection. That mismatch remains open for review and the reference stays frozen. |
| FI-048 | One reviewer accepted the strong sales-emphasis objection. The other questioned whether “must love sales” supports that scope or only an objection to the required enthusiasm. The replay held the proposal in both arms. The approved reference scores the anchored sales-emphasis objection. |
| FI3X-001 | Both reviewers used “Specifically” to link the broad authority reaction to the concrete objection about inspection order. The replay kept the near-zero autonomy claim and retained the broad wording as context in both arms. |
| FI3X-002 | Both reviewers preserved the independent inspection-order and budget objections. The archived budget classification differs from the frozen reference and remains a dimension and scope disagreement. |
| FI3X-003 and FI3X-004 | The profile-review examples preserved the absence of a preference in the first case and retained the positive debrief preference alongside the stated qualification gap in the second. |
| FT-002 and FT-004 | The treatment's original validator losses remain. The replay had no validated safety-briefing preference to review in FT-002, and no validated employer signal to review in FT-004. |

All archived routes, profile-review details, validation diagnostics, and hard-rule actions were preserved. Neither arm contains an unsupported career downgrade or a hard-rule mutation. The replay reads validated proposals only and keeps every archived signal available through its original index and file hash.

## Recommendation

Keep the existing full-benchmark and learning-integration gates. The replay supports explicit review dispositions as a way to surface disagreements. FI-033 shows why an automated rule that always prefers the broad verdict or the narrow reason would be unreliable. FI-048 shows why a reviewer needs to distinguish the existence of a reaction from the evidence for its exact scope. Evaluate scope uncertainty and claim independence as separate judgments before considering automatic suppression. Keep duplicate qualifier handling as a separate validator question. [Acceptance criteria](Feedback_Interpreter_Benchmark_Design_v3.md#assessment-of-the-original-acceptance-criteria)

## Reproduce the projection

Run from the repository root with an unused output file.

```sh
PYTHONPATH=src python -m job_search_agent.feedback_claim_review_v3 \
  --archive benchmarks/feedback/live_v3_extraction_independence_trial \
  --decisions benchmarks/feedback/offline_v3_claim_review/decisions.json \
  --output /tmp/feedback-v3-claim-review.json
```
