# Feedback interpreter reaction accounting trial

The separate extraction trial identified the AI advisor posting praise in both inventories. The classifier relabeled it as context in both final proposals. This follow-up tests whether the classifier can explicitly account for every extracted reaction and preserve the known misses. [Separate extraction results](Feedback_Interpreter_Separate_Extraction_Trial_v3.md#results)

## Protocol frozen before inference

Derive a stable ID for each verified quote from its source text and offsets. Record a disposition for each item whose preliminary role is a preference. A disposition links the quote to a single final signal, gives an evidence-backed reason it is context, or explains what needs review. Keep unresolved or reclassified source quotes visible. Check declared links against the raw proposal and the validated output. A signal dropped by validation still requires review. Positional or partial overlap alone provides insufficient evidence of a link.

First apply the accounting checks to the 16 saved split-arm proposals with zero API requests. Infer links only from uniquely grounded original spans. The offline gate requires the AI advisor praise to be flagged in both rounds and the neutral controls to remain outside the preference list. The replay preserves validated outputs and review metadata.

After the offline check, rerun only the classifier at `gpt-5.4-2026-03-05`, temperature `0.1`, on the eight cases in each of the two saved rounds. Keep the source, verified quotes and roles, existing classifier instructions, and normal validator and routing. Supply stable IDs and an additional disposition contract for the experimental response. Strip that contract from the proposal passed to the validator and preserve the complete model response in the archive. Record 16 planned requests and keep references outside the request. Compare against the earlier split classifier as a historical control. This design reuses identical inventories and measures the receipt and instruction change together. [Classifier instructions](../benchmarks/feedback/extraction_reaction_accounting_v3.txt)

Run masked semantic review on raw and validated classifications. The trial passes only if every expected signal matches in both rounds, including the AI advisor praise and the notebook-digitizing duty, with zero invented preferences, incomplete accounting, validator rejections, unsafe career downgrades, or unauthorized hard-rule changes. Every expected review route and advisory action must remain correct. A visible review flag exposes an unresolved claim and leaves it out of the recovered-signal count. Successful targeted results warrant review before a full benchmark on a fresh holdout.

## Replay and capture commands

Use two unused output directories from the repository root.

```sh
PYTHONPATH=src python -m job_search_agent.feedback_reaction_accounting_trial_v3 \
  --offline --output /tmp/feedback-v3-accounting-offline

PYTHONPATH=src python -m job_search_agent.feedback_reaction_accounting_trial_v3 \
  --output /tmp/feedback-v3-accounting-live
```

## Results

**The accounting check exposed the dropped praise and the live classifier corrected the notebook duty. The trial still missed its gate.** In both rounds the classifier treated the AI advisor praise as context. The exact quote and its reason remain visible with a review flag. [Case-level scorecard](../benchmarks/feedback/live_v3_reaction_accounting_trial/semantic-report.json)

The protocol and instruction changes were frozen at `189283e9237b69d13e3196d7ed61cad79919d75a`. Offline replay and live inference ran from `4c0c4b32e085e22c38397958880bbf7a663ce9ec`. The offline run reproduced the saved raw and validated outputs byte for byte. It found exactly two omitted reactions, both the AI advisor praise, and kept the neutral qualification and employer controls intact. It made zero API requests. [Offline capture report](../benchmarks/feedback/offline_v3_reaction_accounting/report.json) · [First-pass audit](../benchmarks/feedback/offline_v3_reaction_accounting/pass-1/accounting.audit.json) · [Second-pass audit](../benchmarks/feedback/offline_v3_reaction_accounting/pass-2/accounting.audit.json)

All 16 classifier-only requests completed without transport or execution errors, in 47.984 seconds of summed request time. Removing the added IDs from each input reproduces the earlier classifier's input fingerprint for that round. Each raw response contains the final proposal and its dispositions. The interpreter validated the standard proposal and the audit verified every link separately. No extraction requests were made. [Configuration](../benchmarks/feedback/live_v3_reaction_accounting_trial/configuration.json) · [Request trace](../benchmarks/feedback/live_v3_reaction_accounting_trial/request-trace.json) · [Masked adjudications](../benchmarks/feedback/live_v3_reaction_accounting_trial/adjudications.json)

| Measure across both rounds | Archived split classifier | Live accounting classifier |
| --- | ---: | ---: |
| Raw and validated semantic recall | 15/20 | 16/20 |
| Raw and validated semantic precision | 15/18 | 16/18 |
| Fully correct cases | 12/16 | 14/16 |
| Correct review routes | 16/16 | 16/16 |
| Correct hard-rule actions | 16/16 | 16/16 |
| Validator rejections | 0 | 0 |
| Reactions flagged for review | 2 | 2 |
| Missing or structurally invalid accounting entries | 2 | 0 |

| Case or check | Finding |
| --- | --- |
| FI-041 posting praise | Both responses explicitly called the praise context because it accompanies employer distrust. Both audits retained it as reviewable source evidence. The reference requires a separate posting-level preference, so the live result earns no credit for it. |
| FI-041 employer distrust | Both live responses classified the employer objection under culture. The reference assigns that claim to the employer dimension. The archived classifier got this dimension right in its second pass. |
| FH3-007 notebook digitizing | Both archived proposals attributed the stated interest to a growth goal. Both live proposals correctly treated it as a duty and preserved the route. |
| Neutral and mixed-intent controls | Both rounds preserved the explicit positive posting reaction alongside the qualification review, kept neutral mentions outside the preference list, and retained the rule request's separate confirmation route. |
| Dispositions | All 20 inventory preferences received explicit dispositions. Eighteen linked to a validated signal. The two `context` dispositions both stayed flagged, with their exact quote and explanation. No dispositions were missing or structurally invalid. |

The receipt and prompt change made the omission inspectable and improved duty classification on these saved cases. The historical comparator used the same saved evidence and ran earlier. The result measures the combined prompt, ID, and response-contract change. The full fresh benchmark and learning integration remain on hold.
