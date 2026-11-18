# Feedback interpreter response-schema trial

This trial compares the current v3 response schema with a stricter experimental schema. Both arms use the same original six evidence-review inputs, same instructions including the intensity guidance, same model and temperature, and the same validator and routing. The existing interpreter remains the production entry point. [Prior evidence review](Feedback_Interpreter_Evidence_Review_v3.md) · [Shared intensity guidance](../benchmarks/feedback/extraction_trial_v3_schema_guidance.txt)

The experimental schema keeps the same JSON fields. Nested alternatives require each dimension to use one of its compatible scope types. A separate schema alternative limits `intensity` to the controlled values in the guidance. The original qualifier quote remains part of every record. Model evidence and meaning still require validation and review. [Experimental schema](../src/job_search_agent/feedback_extraction_schema_v3.py)

## Protocol frozen before inference

Run one request per case per arm with `gpt-5.4-2026-03-05` at temperature `0.1`. Alternate which arm goes first. Both arms receive the same saved candidate proposal and evidence findings, with the original feedback, decision, posting context, and supplied hard rules. References and adjudications stay outside the requests.

| Cases | Check |
| --- | --- |
| FI-033 | Preserve the near-zero autonomy objection with compatible dimension and scope and no independent duplicate for the lead-in. |
| FI-048 | Preserve the sales-emphasis limit as a controlled intensity qualifier supported by its original wording. |
| FI-041, FT-004 | Retain independent posting praise and employer distrust. |
| FT-002 | Preserve the already supported duty-emphasis limit. |
| FT-005 | Keep the explanation as context and preserve the narrow career objection. |

Record raw schema violations, validated outputs, and grounded semantic judgments separately. Mask arm identity for semantic review. The stricter contract supports moving to a full benchmark only if all six trials complete, raw proposals conform and match their references, validation accepts complete grounded signals without rejections, and routes and hard-rule actions remain correct. The two targeted intensity cases must retain the relevant controlled qualifiers and exact evidence. A later full benchmark would use a fresh sealed holdout.

## Capture command

Use a new output directory.

```sh
PYTHONPATH=src python -m job_search_agent.feedback_extraction_schema_trial_v3 \
  --archive benchmarks/feedback/live_v3_extraction_trial \
  --replay benchmarks/feedback/offline_v3_extraction_evidence \
  --output /tmp/feedback-v3-schema-trial
```

## Results

**The stricter schema passed structural checks and still missed the semantic gate.** It eliminated the incompatible dimension and scope pair and retained all eight expected signals after validation. It also let one schema-valid duplicate through. Both arms finished with five of six complete validated cases. The full benchmark remains on hold. [Semantic scorecard](../benchmarks/feedback/live_v3_extraction_schema_trial/semantic-report.json)

The protocol and inputs were frozen at `7acab15a25a73739d5a517aa92aa45ea0aae32f6`. All 12 live requests completed without API or execution errors. The traces confirm identical per-case model inputs, identical instructions, and different schema fingerprints. Masked Codex review compared every raw and validated signal with its reference. [Configuration](../benchmarks/feedback/live_v3_extraction_schema_trial/configuration.json) · [Capture report](../benchmarks/feedback/live_v3_extraction_schema_trial/report.json) · [Masked adjudications](../benchmarks/feedback/live_v3_extraction_schema_trial/adjudications.json)

| Measure | Current schema | Stricter schema |
| --- | ---: | ---: |
| Raw records violating the tested schema constraints | 1 | 0 |
| Validator rejections | 2 | 0 |
| Complete raw cases by semantic review | 5/6 | 5/6 |
| Complete validated cases | 5/6 | 5/6 |
| Validated semantic recall | 7/8 | 8/8 |
| Validated semantic precision | 7/7 | 8/9 |
| Correct review routes | 5/6 | 6/6 |
| Correct hard-rule actions | 6/6 | 6/6 |
| Target cases with anchored controlled intensity | 2/2 | 2/2 |

### Findings

- **FI-033.** The current schema emitted an invalid `seniority_scope` and `posting_role` pair for “This is too junior.” Validation removed the extra. The stricter schema emitted the lead-in as a separate `seniority_scope` and `seniority_feature` signal, which is structurally valid. The reference treats it as a summary of the near-zero autonomy objection. Both arms emitted that grounded objection with `intensity: near_zero`. The stricter arm kept the unsupported extra after validation.
- **FI-048.** Both arms used `intensity: strong` on the sales-emphasis objection and retained “must love sales” as evidence. Neither triggered the earlier emphasis finding. This result followed the shared guidance in both arms.
- **FT-002.** The current schema put the same `dominant` intensity in two qualifiers. Validation rejected the whole signal and routed the case to clarification. The stricter arm returned a single grounded qualifier and retained the correct route.
- **FI-041, FT-004, and FT-005.** Both arms preserved the independent posting and employer reactions or the contextual explanation as expected. All proposals remained held for review. The reviewers found no unsupported career downgrade or unauthorized hard-rule action.

The stricter contract blocks incompatible field combinations. The remaining promotion criterion is semantic independence. A lead-in that summarizes a narrower reason can still be expressed as a second schema-valid signal. Learning integration remains on hold.
