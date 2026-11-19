# Feedback interpreter signal-independence trial

The response-schema trial exposed a semantic error that the stricter schema could accept. In FI-033, the model proposed a separate seniority objection from “This is too junior” alongside the specific objection about decision-making autonomy. The approved reference treats the first phrase as a summary of the second. This comparison tests whether an instruction to verify independent support removes that extra signal while retaining preferences that express distinct claims. [Prior schema trial](Feedback_Interpreter_Schema_Trial_v3.md#results)

## Protocol frozen before inference

Run one request per case per arm with `gpt-5.4-2026-03-05` at temperature `0.1`. Alternate which arm goes first. Both arms use the stricter schema, the existing validator and routing, and explicit condition recovery. The treatment appends the signal-independence instruction. Each pair uses the same input and configuration otherwise. [Treatment instruction](../benchmarks/feedback/extraction_trial_v3_independent_signals.txt)

| Cases | Input and purpose |
| --- | --- |
| FI-033, FI-048, FI-041, FT-002, FT-004, FT-005 | Repeat the six known evidence-review inputs with their archived proposal and offline findings. Test removal of the FI-033 extra and preservation of scope, intensity, route, and genuinely independent preferences. |
| Four new synthetic contrast cases | Extract directly from feedback, decision, posting context, and approved hard rules. Each pair tests whether a small change in what the user actually says warrants a different interpretation. Freeze these references before inference. |

The model receives source inputs and, for the known cases only, the archived proposal and offline findings. Reviewers receive the approved or frozen reference and both arms' raw and validated records with arm identity masked. Match signals one-to-one by meaning, dimension, scope, polarity, conditions, and explicit qualifiers. Report missing, extra, and incorrectly scoped signals by case. Count a missing signal and an extra signal when an output fails a required attribute of its intended match. Score signal precision as matches divided by emitted signals and recall as matches divided by expected signals. Check evidence, routes, and hard-rule actions separately. [Synthetic contrast fixture](../benchmarks/feedback/extraction_independence_trial_cases_v3.json)

The treatment passes the targeted gate only if all ten raw responses are schema-conformant and semantically complete, all ten validated cases preserve every supported signal and its evidence with zero extras or validator rejections, and all routes and hard-rule actions are correct. FI-033 must retain just the anchored near-zero decision-making autonomy objection. FI-048 must retain the anchored `strong` sales-emphasis limit. The synthetic contrasts must retain their genuinely independent signals. Zero-tolerance checks cover unsupported career downgrades, unauthorized hard-rule actions or mutations, and unresolved blocking evidence findings. The control must also complete all ten requests for the comparison to be interpretable. A pass supports recommending a separately reviewed larger benchmark with a fresh holdout.

Report control and treatment scores separately for the six known cases and the four new cases. One request per arm measures the paired outcomes. If the control also corrects FI-033, report that this run did not demonstrate a treatment-specific improvement on FI-033.

## Capture command

Use a new output directory.

```sh
PYTHONPATH=src python -m job_search_agent.feedback_extraction_independence_trial_v3 \
  --archive benchmarks/feedback/live_v3_extraction_trial \
  --replay benchmarks/feedback/offline_v3_extraction_evidence \
  --output /tmp/feedback-v3-independence-trial
```
