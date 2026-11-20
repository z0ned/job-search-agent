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
