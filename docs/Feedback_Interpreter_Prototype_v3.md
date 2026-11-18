# Feedback interpreter v3 prototype

The v3 interpreter makes one Responses API request. The request extracts original-feedback clauses and proposes a scoped signal for each independently supported preference. Python anchors those clauses and qualifiers to verbatim source spans, checks the representation, and computes the review route and advisory hard-rule action. The input is the decision, the feedback, verified posting context, and confirmed rules. [Architecture and gates](Feedback_Interpreter_Benchmark_Design_v3.md) · [Approved reference decisions](Feedback_Interpreter_Reference_Decisions_v3.md)

The interpreter keeps accepted signals on profile and clarification routes. It returns posting verification requests as evidence-linked clauses. Structured eligibility findings come from known posting facts and supported confirmed policies. A request for a different hard rule can produce a separate confirmation item. All proposals remain held for human review. The module has no write path to rules, listings, profiles, or ranking.

V3 separates display text from feature identity. A known feature and compatible scope can resolve to a stable ID in code. Unfamiliar concepts have a null feature ID and a candidate status. Evidence records use zero-based, half-open character spans in the exact feedback and retain the original proof text. Structured posting evidence has its own source. Negative career proposals carry a career-evidence review field. The cue is a review aid and provides no authority to apply a proposal. [Taxonomy proposal](Feedback_Interpreter_Taxonomy_Proposal_v3.md)

## Run locally

Use Python 3.12 or later and provide `OPENAI_API_KEY` from the environment for live inference. The checked-in unit suite uses controlled providers.

```sh
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python -m job_search_agent.feedback_v3 \
  --model gpt-5.4-2026-03-05 --temperature 0.1 < feedback-input.json
```

The input JSON has `decision` and `feedback`, with optional `job_context` and `hard_rules`. The output includes the raw feedback, accepted clauses and preference records, route, review details, advisory rule action, and any rejected record diagnostics. Uniquely anchored quotes keep repeated phrases from being assigned to the wrong part of the feedback. Capture both model proposals and validated output when benchmarking.

## Evaluate v3

Benchmark the approved 50-case reference revision, the earlier 12 unseen-at-v2 cases as a regression suite, and the fresh sealed v3 holdout. Use separate output directories for each evaluation. The live scorer keeps the original cases and artifacts available through the v2 module. [Benchmark archive](../benchmarks/feedback/README.md)

```sh
PYTHONPATH=src python -m job_search_agent.feedback_evaluation_v3 \
  benchmarks/feedback/gold_cases_v3.json --suite gold \
  --model gpt-5.4-2026-03-05 --temperature 0.1 \
  --save-predictions /tmp/feedback-v3-gold
```

The benchmark defaults to two passes. Use `--suite regression` with `benchmarks/feedback/holdout_cases_v2.json` and `--suite holdout` with `benchmarks/feedback/holdout_cases_v3.json`. Report the frozen literal and canonical diagnostics alongside adjudicated correctness. Learning integration remains gated on reviewed benchmark performance.
