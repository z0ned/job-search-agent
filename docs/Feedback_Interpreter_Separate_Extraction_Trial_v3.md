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

## Results

**The separate extraction stage found all 20 expected preferences across the two passes. The final classifier still omitted the same known preference in both passes.** The two-call arm completed 12 of 16 cases, compared with 10 of 16 for the one-call arm. It fell short of the targeted gate. [Semantic scorecard](../benchmarks/feedback/live_v3_separate_extraction_trial/semantic-report.json)

The inputs and scoring criteria were frozen at `2bb080a1b1c3c10d3d80d22b11689a2139cc1a24`. Inference ran from `012ff361bae4c1b8b8701104f381bc7c41288409`. All 48 requests completed without API or execution errors. Trace verification matched the two arms' original inputs and final response schemas and bound each response to its captured proposal. Separate masked reviewers scored each round's raw and validated outputs. A third reviewer independently scored the inventory spans. [Configuration](../benchmarks/feedback/live_v3_separate_extraction_trial/configuration.json) · [Request trace](../benchmarks/feedback/live_v3_separate_extraction_trial/request-trace.json) · [Masked adjudications](../benchmarks/feedback/live_v3_separate_extraction_trial/adjudications.json)

| Measure over both passes | One call | Separate extraction |
| --- | ---: | ---: |
| Complete raw cases | 10/16 | 12/16 |
| Complete validated cases | 10/16 | 12/16 |
| Complete validated cases on fresh examples | 6/8 | 8/8 |
| Validated recall on known cases | 8/12 | 7/12 |
| Raw semantic precision | 14/18 | 15/18 |
| Validated semantic precision | 14/16 | 15/18 |
| Validated semantic recall | 14/20 | 15/20 |
| Correct review routes | 16/16 | 16/16 |
| Correct hard-rule actions | 16/16 | 16/16 |
| Validator rejections | 2 | 0 |
| Live requests | 16 | 32 |
| Summed request time | 43.671 s | 66.302 s |

Validated recall was 7/10 in both baseline passes and 7/10 and 8/10 in the separate arm. The 16 inventory requests took 25.863 seconds summed. All 20 inventoried preference spans had exact source anchors and matched the references. Both arms held every accepted preference for review and produced zero unsupported career downgrades or unauthorized hard-rule actions. [Capture diagnostics](../benchmarks/feedback/live_v3_separate_extraction_trial/report.json)

| Case | Finding |
| --- | --- |
| FI-041 | Both inventories correctly identified “This is a terrific AI advisor role” as a preference. Both final classifiers in the split arm relabeled it as context, and the baseline also omitted it. In the first pass the split classifier also put employer distrust in the culture dimension. The reference assigns it to the employer dimension. |
| FH3-011 | Both arms kept the positive reaction to this specific opening and the negative reaction to the project type on both passes. The contemporaneous baseline recovered the previously missed posting praise without the inventory. |
| FH3-007 | Both arms classified digitizing handwritten field notebooks as a growth goal. The reference classifies the activity as a duty. The inventory tagged the prospective training expectation as a profile fact. The final classifier corrected that preliminary role and preserved the expected route in both passes. |
| FS3-001 | Both baseline proposals anchored the posting praise and classified it with incompatible career and posting fields. Validation dropped it. The split arm correctly classified the praise as applying to this opening and preserved it alongside profile review in both passes. |
| FH3-002 and FS3-002–004 | Both arms preserved the independently supported preferences, distinguished neutral source mentions, and kept the expected review routes and hard-rule actions. |

The first stage showed that the missing praise can be found in the source. The handoff still allows a grounded reaction to disappear during classification. The next targeted change is to give each inventoried reaction a stable link and require the classifier to account for it as a signal or record why it needs review. Keep the stage-one roles provisional so a mistaken profile-fact label does not determine routing. The full live benchmark and learning integration remain gated.
