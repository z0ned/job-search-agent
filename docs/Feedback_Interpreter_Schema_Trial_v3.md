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
