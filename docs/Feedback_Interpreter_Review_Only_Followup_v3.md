# Feedback interpreter verification and travel scope follow-up

The fresh one-call benchmark exposed two repeatable failures. The model supplied the specific overnight-schedule question, and the routing fallback lost it. The model kept the travel cadence and omitted the number of trips. This follow-up tests both corrections without changing the prompt, response schema, or number of inference calls per case. [Previous benchmark](Feedback_Interpreter_Review_Only_Benchmark_v3.md#results)

## Protocol

Use the previous review-only candidate as the control. Its existing quote validation, deterministic repairs, eligibility checks, and rule confirmation continue to govern each reply. The follow-up adds two read-only changes.

- When the result would otherwise ask a generic clarification question, use an unambiguous, source-grounded posting-verification question. Preserve a specific question already present and preserve approval, profile fact review, and hard-rule routing.
- In an already validated travel preference, preserve an explicit trip count alongside its cadence without widening the scope. Require a unique link to the original feedback. Retain uncertain or conflicting count language for review when the scope cannot be resolved deterministically.

First replay all 48 responses from the existing two-pass comparison. Confirm the baseline reproduces the original validated records and verify that the fixes preserve supported signals, routes, evidence, and hard-rule actions. Check new offline contrasts for different wording, unrelated counts, ambiguous travel limits, and mixed feedback. Keep all original fixtures and captures intact.

## Offline verification

The replay reproduced the original validation records and changed only eight copies of the two targeted results. All four copies of RO3-004 now ask whether overnight shifts are occasional or routine. All four copies of RO3-011 keep both the overnight cadence and the count of one trip. The other 40 records retained the same substantive output. No held preference was dropped, and every route and hard-rule action stayed intact. Offline contrasts also cover a mixed review, unrelated counts, alternate cadences, a complete existing bound, and an uncertain range that remains flagged. [Replay report](../benchmarks/feedback/offline_v3_review_only_followup.json)

## Sealed end-to-end holdout

If the offline checks succeed, run two independent passes on 12 previously unseen, independently authored synthetic comments. Use `gpt-5.4-2026-03-05` at temperature `0.1` with the normal one-call v3 prompt and schema. Each request receives the full feedback, decision, job context, and hard rules. Expected answers and preselected quotes stay outside the request. Apply both deterministic validators to each saved reply. This makes the repair effect measurable on the same raw input and uses 24 planned model requests. [Sealed fixture](../benchmarks/feedback/review_only_followup_holdout_v3.json)

Use the same masked, case-level semantic assessment and per-pass gates as the previous benchmark. Credit a supported count when the full bound is faithfully represented, including a distinct quantity and cadence with exact evidence. Report route labels and the adequacy of the question or profile fact separately. Include precision, recall, scope, all hard-rule actions, further review workload, and legacy literal and registered-identity comparisons. Zero tolerance for unauthorized rule changes and unsupported career downgrades still applies. Passing the holdout is evidence for review before learning integration. [Approved gates](Feedback_Interpreter_Benchmark_Design_v3.md#assessment-of-the-original-acceptance-criteria)

## Replay and capture

Run each command from the repository root with a new output path.

```sh
PYTHONPATH=src python -m job_search_agent.feedback_review_only_followup_replay_v3 \
  --output /tmp/feedback-v3-followup-offline.json

PYTHONPATH=src python -m job_search_agent.feedback_review_only_followup_trial_v3 \
  --output /tmp/feedback-v3-followup-live
```

## Fresh holdout results

**The repairs improved both passes on fresh feedback. The follow-up still missed the agreed gates.** Using the same model reply for each pair, the candidate improved fully correct results from 12/24 to 18/24. It recovered two missing trip counts and supplied four specific verification questions. [Semantic scorecard](../benchmarks/feedback/live_v3_review_only_followup/semantic-report.json)

The implementation, offline replay, protocol, and holdout were frozen at `b436dc9639edc7e6c8a03a1b2d3a66343a4156de` before inference. All 24 requests completed at the pinned model and temperature in 49.321 seconds of summed model time. Verification checked the complete source-only inputs, all shared raw replies, and both validations of each reply. Four independent masked reviews separately scored the raw and validated outputs. [Configuration](../benchmarks/feedback/live_v3_review_only_followup/configuration.json) · [Request trace](../benchmarks/feedback/live_v3_review_only_followup/request-trace.json) · [Adjudications](../benchmarks/feedback/live_v3_review_only_followup/adjudications.json)

| Measure across both passes | Prior review-only candidate | Follow-up |
| --- | ---: | ---: |
| Validated semantic precision | 8/13 | 10/13 |
| Validated semantic recall | 8/12 | 10/12 |
| Fully correct end-to-end records | 12/24 | 18/24 |
| Correct review route labels | 23/24 | 23/24 |
| Adequate route resolutions | 16/24 | 20/24 |
| Correct hard-rule actions | 24/24 | 24/24 |
| Cases requiring further review | 11/24 | 14/24 |
| Validation rejections, unsupported career downgrades, or unauthorized hard-rule actions and mutations | 0 | 0 |
| Passes clearing all gates | 0/2 | 0/2 |

Both arms shared a raw precision of 8/13 and recall of 8/12. The follow-up's validated recall was 5/6 on each pass, below the agreed 90% minimum. Its precision was 5/7 and 5/6. The original literal case matching returned 5/12 and 6/12 for each arm, and the literal and registered-identity checks matched zero signals. [Capture diagnostics](../benchmarks/feedback/live_v3_review_only_followup/report.json)

| Cases | What the holdout showed |
| --- | --- |
| RF3-002 and RF3-003 | The follow-up asked specific questions about recurring Saturday coverage and whether quoted pay included a bonus. It repaired both questions in both passes. |
| RF3-006 | Both model replies gave the two-month cadence without a count. The follow-up added the exact count of one overnight trip from the source in each pass. |
| RF3-001 | The source referred back to “site visits” with “those.” The conservative verifier left the generic clarification question in place because it could not anchor the target within its supported parsing rules. |
| RF3-005 | The model already kept the valid upper bound of three client trips per quarter. The follow-up added a review flag in both passes because the structured value abbreviated the fully anchored phrase. These flags added work without correcting a preference. |
| RF3-008 | The user had yet to decide between two and four trips a month. The first pass recorded an uncertain preference and sent it to approval. The follow-up flagged it for review. The second pass asked a generic frequency question that omitted the concrete choice. |
| RF3-012 | The structured qualifiers retained the first six months and the exclusive workload. Reviewers counted the displayed claim about “roles dominated by vendor onboarding paperwork” as broader than the original posting-specific reaction. |

No route label, preference polarity, hard-rule action, or held status changed between the two validators. The three additional review records came from the two unnecessary maximum-count flags and the unresolved travel limit. These tests isolate useful improvements and remaining limits in the existing one-call pipeline. The candidate stays review-only, with automatic learning on hold.
