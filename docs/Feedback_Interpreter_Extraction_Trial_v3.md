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
