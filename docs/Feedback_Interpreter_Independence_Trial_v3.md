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

## Results

**The treatment missed the targeted gate.** It kept the unsupported second signal in FI-033 and repeated the same kind of error on a new synthetic case. After validation, the treatment was fully correct on five of ten cases and the control on seven. [Semantic scorecard](../benchmarks/feedback/live_v3_extraction_independence_trial/semantic-report.json)

The protocol, prompt, runner, and synthetic fixture were frozen at `9435b281c7653edc378031e2635e7b021fec3c57`. All 20 live requests completed without API or execution errors. All ten paired input hashes matched. The six known inputs and the control instructions for those cases also matched the stricter arm of the prior schema trial. Independent Codex reviewers compared the raw and validated records with their references with the arm identity masked. [Configuration](../benchmarks/feedback/live_v3_extraction_independence_trial/configuration.json) · [Capture diagnostics](../benchmarks/feedback/live_v3_extraction_independence_trial/report.json) · [Case-level adjudications](../benchmarks/feedback/live_v3_extraction_independence_trial/adjudications.json)

| Measure | Control | Independence instruction |
| --- | ---: | ---: |
| Raw schema violations | 0 | 0 |
| Validator rejections | 0 | 2 |
| Complete raw cases | 7/10 | 6/10 |
| Complete validated cases | 7/10 | 5/10 |
| Complete validated cases on known inputs | 5/6 | 3/6 |
| Complete validated cases on new synthetic inputs | 2/4 | 2/4 |
| Raw semantic precision | 11/14 | 10/14 |
| Raw semantic recall | 11/12 | 10/12 |
| Validated semantic precision | 11/14 | 9/12 |
| Validated semantic recall | 11/12 | 9/12 |
| Correct review routes | 10/10 | 9/10 |
| Correct hard-rule actions | 10/10 | 10/10 |
| Target cases with anchored controlled intensity | 2/2 | 2/2 |

Neither arm proposed an unsupported career downgrade or an unauthorized hard-rule action. A complete raw case requires exact signal count, semantic matches, and evidence support. Validator rejections and review routes are assessed independently. One request per arm and case establishes the observed paired outcomes. Repeatability and the frequency of each regression remain unmeasured.

### Case findings

| Case | Masked assessment after unmasking |
| --- | --- |
| FI-033 | Both arms kept the anchored near-zero autonomy objection and added a separate junior-level objection. Validation retained both proposals. The approved reference treats the broad phrase as a summary. |
| FI-048 | Both arms kept the sales-emphasis objection with `intensity: strong` anchored to “must love sales.” |
| FI-041 | Both arms kept posting-specific praise and independent employer distrust. |
| FT-002 | Both raw proposals captured the objection to jobs centered on safety briefings. The treatment repeated the same `dominant` qualifier with two anchors. Validation dropped the whole signal and routed to clarification. The control used one qualifier and kept the expected route. |
| FT-004 | Both retained the posting praise. The treatment attached an unsupported Collection Analyst career-context qualifier to employer distrust using a quote outside the distrust clause. Validation dropped the employer signal. The control retained both signals. |
| FT-005 | Both preserved the explicit warehouse-operations career objection and kept inventory reconciliation as explanatory context. |
| FI3X-001 | Both kept the objection to near-zero say over inspection order and promoted “limited authority” into a second, broader objection. “Specifically” connects the broad reaction to the narrower reason. |
| FI3X-002 | Both preserved the separate inspection-order and budget objections. Both classified the budget statement as a duty. The frozen reference classifies the magnitude of budget responsibility as seniority scope. The duty reading is plausible. Scoring that one disagreement differently would leave the two unsupported extras and the treatment's two validator rejections. |
| FI3X-003 | Both routed the stated experience gap to profile review and treated the posting’s mention of debrief facilitation as context. |
| FI3X-004 | Both kept the independently expressed debrief preference alongside the accurate profile fact and used the profile-review route. |

### Recommendation

Keep the existing acceptance criteria and hold the full benchmark and learning-engine integration. The shared strict schema constrained valid field combinations, and every unsupported umbrella signal had a verbatim anchor. The missing check is whether that span, read with the surrounding feedback, adds a preference. The two regressions also demonstrate that collapsing all qualifier failures into signal rejection can lose a supported preference.

Start with an offline evaluation of the saved proposals. Test an explicit decision for potentially overlapping claims about whether each is independent, explanatory, or unresolved. Preserve distinct claims and keep unresolved cases available for review. Evaluate identical grounded qualifier deduplication separately from missing or conflicting evidence. Treat the unsupported qualifier in FT-004 as a separate provenance failure. Keep the profile-review cases and both kinds of synthetic contrasts in the evaluation so a change cannot improve precision by suppressing valid distinct signals. [Benchmark design and acceptance criteria](Feedback_Interpreter_Benchmark_Design_v3.md#assessment-of-the-original-acceptance-criteria)
