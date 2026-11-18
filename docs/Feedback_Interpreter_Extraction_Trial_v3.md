# Feedback interpretation extraction trial

This 10-case trial compares the current v3 extraction instructions with one revision. The same v3 output schema, provider, validator, taxonomy, and routing code serve both arms. Run one request per case and arm with `gpt-5.4-2026-03-05` at temperature `0.1`. Interleave and counterbalance arm order. Send only the original feedback, decision, verified posting context, and supplied hard rules. [Offline repair findings](Feedback_Interpreter_Offline_Repair_v3.md)

## Cases and evaluation

| Known case | What the trial checks |
| --- | --- |
| FI-033 | Dislike of almost no decision-making autonomy stays qualified by the low amount of autonomy. |
| FI-048 | The negative preference applies to work with a strong sales emphasis. |
| FH3-010 | Interest in the activity applies under the explicit upper bound of one shift per week. |
| FI-041 | Praise of this role and distrust of this employer survive as two independent preferences. |
| FH-005 | The career-category objection and the separately favorable duty remain distinct. |

Five independently authored examples test these distinctions with different wording and include cases where a second phrase only qualifies or explains a preference. Freeze the examples, references, candidate instructions, and evaluation criteria before requesting either arm. Existing gold and holdout references provide the known cases. [Fresh trial cases](../benchmarks/feedback/extraction_trial_v3_novel.json) · [Candidate instructions](../benchmarks/feedback/extraction_trial_v3_candidate.txt)

An arm earns a case match when its output preserves all reference preferences and their material scope, polarity, dimension, qualifiers, and conditions, with no unsupported additional preference. Equivalent wording and a faithful structured description receive credit. A material limit visible only in the evidence quote receives no scope credit. Confirm that explicitly conditional feedback retains an applicability condition. Score the raw proposals and validated signals separately. Check validated route, hard-rule action, and evidence support independently. All signals remain held for review.

Mask prompt identity during semantic review. Record per-case matches, misses, extras, and likely failure stage. Advance to a full benchmark if the candidate produces complete raw and validated preferences on all ten cases, recovers at least one known miss from the current-prompt arm, and preserves routing and safety. One request per case and arm provides a targeted comparison. Repeated-run stability belongs in the later full benchmark with two passes and a fresh sealed holdout.

## Capture command

```sh
PYTHONPATH=src python -m job_search_agent.feedback_extraction_trial_v3 \
  --novel benchmarks/feedback/extraction_trial_v3_novel.json \
  --candidate benchmarks/feedback/extraction_trial_v3_candidate.txt \
  --model gpt-5.4-2026-03-05 --temperature 0.1 \
  --output /tmp/feedback-v3-extraction-trial
```

Use a new output directory. The configuration records the paired cases, input and instruction fingerprints, and arm order. Each arm has a raw proposal file and a validated prediction file.

## Trial results

**Decision for review.** The candidate improved validated case matches from **3/10 to 6/10**. It missed the frozen promotion criteria, so keep it experimental and defer the full benchmark. [Semantic scorecard](../benchmarks/feedback/live_v3_extraction_trial/semantic-report.json)

The fixtures, candidate instructions, and trial protocol were committed in `068ea41abe8bd3553df9c637fb795b5134f5de8a` before inference. All 20 requests completed in 51.0 seconds of summed request time with zero API errors. Masked Codex reviewers scored knowledge of the original case wording, raw proposals, and validated records against the same references. They reviewed each variant separately from its prompt identity. [Configuration](../benchmarks/feedback/live_v3_extraction_trial/configuration.json) · [Masked review verdicts](../benchmarks/feedback/live_v3_extraction_trial/adjudications.json)

| Measure | Current prompt | Candidate |
| --- | ---: | ---: |
| Full raw case matches | 3/10 | 5/10 |
| Full validated case matches | 3/10 | 6/10 |
| Known validated case matches | 0/5 | 2/5 |
| Novel validated case matches | 3/5 | 4/5 |
| Validated semantic recall | 5/13 | 9/13 |
| Validated semantic precision | 5/10 | 9/12 |
| Expected review routes | 10/10 | 10/10 |
| Expected hard-rule actions | 10/10 | 10/10 |
| Rejected raw signal records | 1 | 1 |

Both arms held every accepted signal for review. The adjudication found no unsupported career downgrade or unauthorized hard-rule action. Each arm had one invalid scope record on FI-033. Every case in this trial expects `PENDING_APPROVAL` and an unchanged hard-rule action. The routing comparison covers that tested scope. [Live diagnostics](../benchmarks/feedback/live_v3_extraction_trial/report.json)

### What improved

- **FI-033.** The candidate grounds the objection in **almost no decision-making autonomy** and preserves the limit in machine scope. Its extra posting-level signal fails validation, so the case matches only after validation.
- **FH-005.** The candidate preserves the positive vendor-negotiation duty alongside the explicit negative procurement-operations career preference in both raw and validated output.
- **FT-004.** The candidate retains posting-specific praise and employer distrust as two separately scoped reactions.
- **FT-005.** Both arms keep the career objection and treat its explanation as context. This guards against creating a second preference merely because a phrase accompanies the first.

### What remains

| Case | Finding in both arms |
| --- | --- |
| FI-048 | The scope is generic sales. Strong sales emphasis appears in display text and evidence only. |
| FH3-010 | The bound of one shift per week appears as a scope qualifier. The explicit applicability condition is absent. |
| FI-041 | The independent positive reaction to the specific posting is omitted during extraction. |
| FT-003 | The new conditional example also preserves its frequency bound and omits its applicability condition. |

The raw proposals locate these four remaining misses in extraction. The next comparison should verify explicit condition fields and independently evaluated targets before another full run. Learning integration remains on hold.
