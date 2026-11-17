# Feedback interpreter benchmark artifacts

## Original live v1 report

[Original two-pass live report](live_v1_original_report.json) preserves the evaluator's JSON output byte for byte. The benchmark ran on November 17, 2026, using commit `154b9428367f29e50dbabe4bcca496ce2904dff9`, Python 3.12.14, prompt `feedback-interpretation-v1.0`, the OpenAI Responses API, model `gpt-5.4-2026-03-05`, and temperature `0.1`. It ran two sequential passes over the same 50 frozen gold cases. The report includes the suite fingerprint, per-case failures, literal metrics, and consistency results.

The v1 CLI serialized scores and failure classifications. Its per-case proposals existed in process memory and the API requests used `store: false`, so individual proposals from that execution are unavailable. Any separately captured rerun has its own provenance.

From the v1 commit, the command was:

```sh
PYTHONPATH=src python -m job_search_agent.feedback_evaluation \
  feedback_interpretation_gold_cases_v1.json \
  --model gpt-5.4-2026-03-05 --temperature 0.1
```

## Live v1 capture

[Same-configuration baseline rerun](live_v1_capture.json) records a separate live run using the same source commit, model, prompt, temperature, and fixture. It includes a raw structured proposal and a validated prediction for each of the 100 requests, plus the v1 report with literal metrics and per-case failure classifications. The proposals in this file belong to this rerun. The capture records the prompt and response schema fingerprints and preserves the original hard-rule inputs.

For a v2 replay, export each capture entry's `passes[].cases` as a JSON object keyed by case ID with its `validated_prediction` as the value. Pass the two exported files with repeated `--predictions` arguments. [Benchmark specification](../../docs/Feedback_Interpreter_Benchmark_Spec_v2.md)
