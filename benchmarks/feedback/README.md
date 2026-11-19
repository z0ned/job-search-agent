# Feedback interpreter benchmark artifacts

## Original live v1 report

[Original two-pass live report](live_v1_original_report.json) preserves the evaluator's JSON output byte for byte. The benchmark ran on November 17, 2026, using commit `154b9428367f29e50dbabe4bcca496ce2904dff9`, Python 3.12.14, prompt `feedback-interpretation-v1.0`, the OpenAI Responses API, model `gpt-5.4-2026-03-05`, and temperature `0.1`. It ran two sequential passes over the same 50 frozen gold cases. The report includes the suite fingerprint, per-case failures, literal metrics, and consistency results.

The v1 CLI serialized scores and failure classifications. Its per-case proposals existed in process memory and the API requests used `store: false`, so individual proposals from that execution are unavailable. Any separately captured rerun has its own provenance.

Run the v1 command from the baseline commit.

```sh
PYTHONPATH=src python -m job_search_agent.feedback_evaluation \
  feedback_interpretation_gold_cases_v1.json \
  --model gpt-5.4-2026-03-05 --temperature 0.1
```

## Live v1 capture

[Same-configuration baseline rerun](live_v1_capture.json) records a separate live run using the same source commit, model, prompt, temperature, and fixture. It includes a raw structured proposal and a validated prediction for each of the 100 requests, plus the v1 report with literal metrics and per-case failure classifications. The proposals in this file belong to this rerun. The capture records the prompt and response schema fingerprints and preserves the original hard-rule inputs.

For a v2 replay, export each capture entry's `passes[].cases` as a JSON object keyed by case ID with its `validated_prediction` as the value. Pass the two exported files with repeated `--predictions` arguments. [Benchmark specification](../../docs/Feedback_Interpreter_Benchmark_Spec_v2.md)

## Live v2 captures

The v2 captures ran on November 17, 2026 with Python 3.12.14, the OpenAI Responses API with `store: false`, model `gpt-5.4-2026-03-05`, prompt `feedback-interpretation-v2.0`, temperature `0.1`, and taxonomy `feedback-taxonomy-v2.0`. The prompt and response schema are in commit `b696794aff8e33576f1d00413c1e41d8d65e36ec`. The command started before metadata-only capture updates in that commit. The final evaluator reproduced both the literal and canonical scores from the saved predictions.

Each run directory contains the original live configuration, complete report, two raw proposal files, and two validated prediction files. The report binds the captures to each pass with SHA-256 fingerprints. The two suites were run independently with the same configuration. The unseen fixture was frozen before the prompt changes. [Gold report](live_v2_gold/report.json) · [Holdout report](live_v2_holdout/report.json) · [Holdout fixture](holdout_cases_v2.json)

## Live v3 captures

The v3 prototype ran on November 18, 2026 with model `gpt-5.4-2026-03-05`, temperature `0.1`, and prompt `feedback-interpretation-v3.0`. The inference revision was `9b3ce5c48183f71b697052d8ccf5b33b5fb52283`. The 50-case approved gold fixture, earlier 12-case holdout regression, and fresh 12-case holdout each ran two independent live passes.

Each v3 directory contains the configuration, live automated report, both raw proposals and validated predictions, two hash-bound case adjudications, and the offline replay report. The live report records the automated results at capture time. The replay report adds adjudicated scores and cross-pass diagnostics while preserving inference outputs. [Gold captures](live_v3_gold/adjudicated-report.json) · [Regression captures](live_v3_regression/adjudicated-report.json) · [Fresh holdout captures](live_v3_holdout/adjudicated-report.json) · [Summary](../../docs/Feedback_Interpreter_Benchmark_Report_v3.md)

## Offline v3 repair replay

The deterministic repair replayed all 148 original raw proposals without API requests. The replay directories contain a provenance configuration, validated outputs, comparison report, and hash-bound adjudications. Raw proposals remain in the live archives. [Gold replay](offline_v3_gold/adjudicated-report.json) · [Earlier holdout replay](offline_v3_regression/adjudicated-report.json) · [V3 holdout replay](offline_v3_holdout/adjudicated-report.json) · [Offline repair findings](../../docs/Feedback_Interpreter_Offline_Repair_v3.md)

## Targeted v3 extraction trial

The trial compared the current v3 instructions with one candidate across five known failures and five independently written cases. It used 20 live requests with matched model settings, schema, validation, routing, and case inputs. The archive contains both arms' raw and validated outputs, input fingerprints, and masked adjudication. [Trial protocol and findings](../../docs/Feedback_Interpreter_Extraction_Trial_v3.md) · [Semantic scorecard](live_v3_extraction_trial/semantic-report.json)

## V3 evidence replay and follow-up

An offline replay of the 20 extraction-trial proposals restored explicit conditions in both arms. Six separate live evidence-review requests tested the remaining target cases and controls. The archive includes replay provenance, raw and validated follow-up captures, masked verdicts, and the combined scorecard. [Evidence review findings](../../docs/Feedback_Interpreter_Evidence_Review_v3.md) · [Offline replay](offline_v3_extraction_evidence/report.json) · [Semantic scorecard](live_v3_extraction_followup/semantic-report.json)

## V3 response-schema trial

The isolated trial compared the current schema with compatible dimension and scope pairs and controlled intensity values. It used one request per arm on each of six known evidence-review inputs with identical instructions, inputs, model settings, validator, and routing. The captures include exact hashes, paired traces, and masked semantic verdicts. [Schema trial protocol and results](../../docs/Feedback_Interpreter_Schema_Trial_v3.md) · [Semantic scorecard](live_v3_extraction_schema_trial/semantic-report.json)

## V3 signal-independence trial

The paired trial tested an instruction to verify independent support for each signal on six known evidence-review inputs and four frozen synthetic contrasts. Both arms used the stricter schema, the same source inputs within each pair, and the same validator and routing. The archive preserves 20 requests’ raw proposals and validated records, paired traces, and blinded case-level adjudication. [Trial protocol and findings](../../docs/Feedback_Interpreter_Independence_Trial_v3.md) · [Semantic scorecard](live_v3_extraction_independence_trial/semantic-report.json)

## Offline v3 claim-review replay

Two source-only reviewers assigned claim dispositions to the 20 saved validated records from the signal-independence trial. The replay applies the consensus decisions by signal index and preserves the original capture and routing. Its comparison reports supported signals held for review separately from explanatory extras. [Replay protocol and findings](../../docs/Feedback_Interpreter_Claim_Review_Replay_v3.md) · [Case-level comparison](offline_v3_claim_review/comparison.json)

## Offline v3 claim independence and scope trial

Separate blinded reviewers judged claim relationships and proposed scopes on the same 20 validated records. The archived projection keeps flagged claims visible and retains each signal's original evidence and review authority through its capture and index. The scorecard reports visible and unflagged lists separately against the frozen adjudications. [Trial protocol and findings](../../docs/Feedback_Interpreter_Claim_Scope_Trial_v3.md) · [Case-level scorecard](offline_v3_claim_scope_review/comparison.json)

The follow-up uses the recorded disputed explanation links to flag both implicated claims. Its decisions, projection, and case-level comparison preserve the source hashes and the results of the targeted checks. [Follow-up results](../../docs/Feedback_Interpreter_Claim_Scope_Trial_v3.md#follow-up-on-disputed-relationships) · [Case-level scorecard](offline_v3_disputed_claim_review/comparison.json)
