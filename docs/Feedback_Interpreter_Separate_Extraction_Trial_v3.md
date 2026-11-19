# Feedback interpreter separate extraction trial

The last offline replay recovered supported preferences that validation dropped. The remaining omissions include preferences absent from the model's raw proposal. This trial tests whether explicitly collecting evidence before classifying it recovers those preferences. [Offline repair results](Feedback_Interpreter_Validation_Repair_Trial_v3.md)

## Protocol frozen before inference

Compare the normal one-call v3 interpreter with an experimental two-call process. The first call lists verbatim feedback spans and preliminary roles. Code verifies each span against a unique occurrence in the source. The second call receives the original inputs and that inventory, then classifies the reactions using the same output schema as the baseline. Both arms use the same validator, review routing, and hard-rule checks. The inventory is experimental input to the classifier. It has no write or application authority. [Inventory prompt](../benchmarks/feedback/extraction_separate_trial_v3_inventory.txt) · [Classifier handoff](../benchmarks/feedback/extraction_separate_trial_v3_handoff.txt)

Use `gpt-5.4-2026-03-05` at temperature `0.1`. Run two independent passes of the same eight cases. Alternate which arm runs first, reversing the order on the second pass. Each complete pair uses three requests, for a maximum of 48 benchmark requests. Record any stage failure, request count, and elapsed time. Preserve raw inventories, anchored quotes, raw final proposals, and validated outputs. Keep case references outside model inputs.

| Cases | Check |
| --- | --- |
| FI-041, FH3-011 | Recover praise for the particular posting alongside a separate employer or duty objection. |
| FH3-007 | Keep the preferred work scoped to a duty alongside the existing review route. |
| FH3-002 | Preserve the positive duty preference and route the explicit rule request to separate confirmation. |
| FS3-001 to FS3-004 | Independently authored contrasts check that a preference survives a qualification or employer concern and that a neutral mention contributes no extra preference. |

Masked semantic review matches raw and validated signals one to one, using the whole meaning, including polarity, dimension, scope, material qualifiers, and conditions. Score precision, recall, full-case matches, evidence, routes, and advisory hard-rule actions. Inspect first-stage evidence for each missing or recovered target to distinguish inventory omissions, role or scope errors during classification, and validator losses. Count actual model requests and elapsed time by stage. [Fresh trial fixture](../benchmarks/feedback/extraction_separate_trial_cases_v3.json)

The split arm must match every case in both passes, both before and after validation, with grounded evidence, correct routes and hard-rule actions, zero validation rejections, and zero unsupported career downgrades or unauthorized rule changes. It must recover at least one known omission that the contemporaneous baseline misses, and the recovered target must be present as a preference in the first-stage inventory. Report any case where the baseline recovered a previously observed omission. A pass supports a proposal to run the full benchmark with fresh sealed cases. Learning integration remains subject to the full gates.

## Capture command

Run from the repository root with a new output directory.

```sh
PYTHONPATH=src python -m job_search_agent.feedback_separate_extraction_trial_v3 \
  --output /tmp/feedback-v3-separate-extraction
```
