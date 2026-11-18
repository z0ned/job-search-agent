# Evidence review after the v3 extraction trial

The first stage revalidates the 20 saved A/B proposals. With evidence recovery disabled, both arms must reproduce their archived predictions byte for byte. With recovery enabled, a direct preference followed by a clearly attached applicability clause can move an already anchored workload cap into the condition field. The check preserves exact text and offsets. Existing conditions and ordinary intrinsic workload limits stay in their original fields. [Original A/B trial](Feedback_Interpreter_Extraction_Trial_v3.md)

Evidence checks also flag machine scope that loses a supported duty emphasis and an identified posting evaluation that appears as context alongside an independent employer objection. These findings guide review. They leave preferences, routes, and hard-rule actions under the existing validator and routing rules.

## Live follow-up protocol

Use the candidate arm's saved proposals and offline findings as input to a separate experimental evidence-review request. Use the original decision, feedback, posting context, and rules, the existing v3 response schema, and the original model `gpt-5.4-2026-03-05` at temperature `0.1`. Supply no reference expectations, adjudication, or example solutions. Return a complete proposal for the existing validator. The normal interpreter continues to use one request. [Evidence review instructions](../benchmarks/feedback/extraction_trial_v3_evidence_review.txt)

| Case | Check |
| --- | --- |
| FI-033 | Keep the near-zero autonomy objection as one signal and avoid the second incompatible posting-level signal. |
| FI-048 | Retain strong sales emphasis in machine scope. |
| FI-041 | Keep independent posting praise and employer distrust. |
| FT-002 | Preserve the already correct duty-emphasis limit. |
| FT-004 | Preserve both already correct independent reactions. |
| FT-005 | Keep the supporting explanation as context. |

Run one follow-up request for each of these six cases. Compare raw proposals, accepted signals, and review routes with the same references and the candidate's offline result. Require three recovered target cases, three preserved controls, correct routes and actions, supported evidence, and zero new validation rejections or unsafe proposals for the follow-up to support a full benchmark. The two repaired condition cases use the offline results. This is a targeted test on known inputs.

## Reproduce the captures

Use new output directories for both commands.

```sh
PYTHONPATH=src python -m job_search_agent.feedback_extraction_trial_replay_v3 \
  --archive benchmarks/feedback/live_v3_extraction_trial \
  --output /tmp/feedback-v3-evidence-replay

PYTHONPATH=src python -m job_search_agent.feedback_extraction_followup_v3 \
  --archive benchmarks/feedback/live_v3_extraction_trial \
  --replay /tmp/feedback-v3-evidence-replay \
  --output /tmp/feedback-v3-evidence-followup
```

Use `--no-recover-explicit-conditions` on the offline command to verify byte-exact reproduction of the original validated files.
