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
