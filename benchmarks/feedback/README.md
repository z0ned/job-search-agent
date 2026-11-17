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
