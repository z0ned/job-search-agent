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

## Results

**Validated coverage improved. The full benchmark gate remains unmet.** The condition repair recovered both missed conditions in each arm. The separate six-request follow-up completed every validated case on the frozen examples. One raw proposal still contained an incompatible dimension and scope, and a conservative evidence finding remained open. [Semantic scorecard](../benchmarks/feedback/live_v3_extraction_followup/semantic-report.json)

The trial froze the recovery code, fixtures, protocol, and follow-up inputs at `7b01ecdcaaa3b9753dfc040c92b8e1a3f9881173`. The disabled replay reproduced both archived validated files byte for byte. The enabled replay used all 20 proposals with zero API requests. It changed interpretations only for FH3-010 and FT-003 in each arm. Review routes, hard-rule actions, and the original validator rejections were identical across the offline replay. [Baseline verification](../benchmarks/feedback/offline_v3_extraction_evidence/baseline-verification.json) · [Offline replay](../benchmarks/feedback/offline_v3_extraction_evidence/report.json)

| Stage | Complete validated cases | Semantic recall | Semantic precision |
| --- | ---: | ---: | ---: |
| Original current prompt | 3/10 | 5/13 | 5/10 |
| Current prompt with offline recovery | 5/10 | 7/13 | 7/10 |
| Original candidate | 6/10 | 9/13 | 9/12 |
| Candidate with offline recovery | 8/10 | 11/13 | 11/12 |
| Candidate with offline recovery and six reviewed substitutions | 10/10 | 13/13 | 13/13 |

### Offline evidence

- FH3-010 preserves “provided it takes at most one shift per week” as its own condition.
- FT-003 preserves “as long as I had to do them no more than twice per month” as its own condition.
- Both arms flag FI-048's broad machine scope and FI-041's posting praise in context. The current-prompt arm also flags the omission in FT-004. Every finding points to the original evidence. The checks emit no replacement preferences. [Offline candidate](../benchmarks/feedback/offline_v3_extraction_evidence/candidate.json) · [Offline current prompt](../benchmarks/feedback/offline_v3_extraction_evidence/baseline.json)

### Follow-up evidence

All six live requests completed without API or execution errors. Masked Codex review matched **five of six raw proposals** and **six of six validated cases**, with 8/8 expected signals retained after validation. The three controls passed. All six routes and hard-rule actions matched the reference. No unsupported career downgrade or unauthorized rule action was found. [Follow-up diagnostics](../benchmarks/feedback/live_v3_extraction_followup/report.json) · [Follow-up adjudications](../benchmarks/feedback/live_v3_extraction_followup/adjudications.json)

| Case | Follow-up result |
| --- | --- |
| FI-033 | The near-zero autonomy objection survives. The review still emits the “too junior” lead-in separately with `seniority_scope` and `posting_role`. The validator rejects this incompatible pair. |
| FI-048 | The review supplies `intensity: must love` with its original anchor. The masked reviewer accepts the sales-emphasis meaning. The automated check still flags the phrase because its intensity vocabulary does not recognize it. |
| FI-041 | Posting-specific praise and employer distrust both survive as independently scoped signals. |
| FT-002, FT-004, FT-005 | The work-emphasis limit, the two independent reactions, and the context-only explanation remain intact. |

The combined 10/10 score uses the same ten cases that informed the follow-up. It identifies recoverable behavior and leaves the predeclared raw and validation gates failed. The current schema permits the dimension and scope fields independently, which explains how FI-033 can produce an invalid pair before validation. A stricter response contract and a consistent machine representation for emphasis are the remaining design decisions. The full benchmark and learning integration stay on hold.
