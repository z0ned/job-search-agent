# Feedback interpretation prototype

The prototype converts a written Interested or Rejected decision into evidence-backed, scoped proposals for review. It preserves the original comment and returns one of three review routes.

| Route | What the result contains |
| --- | --- |
| `PENDING_APPROVAL` | One or more clear, independently supported preference signals |
| `NEEDS_CLARIFICATION` | A focused follow-up question and any independently supported signals held for review |
| `PROFILE_FACT_REVIEW` | A candidate fact, eligibility defect, or explicit rule-change request for separate review |

The service checks the controlled taxonomy, dimension and scope compatibility, verbatim evidence, conflicting signals, and route requirements. Each result carries the configured model and prompt version. The interpreter exposes advisory actions only and has no access to profile, rule, or ranking storage. The proposal schema uses standard-library types and JSON Schema. Human review is required to judge whether a quote actually supports a proposed preference. [Feedback interpretation design](../feedback_interpretation_design_v1.md)

## Run the interpreter

Use Python 3.12 or later. Set `OPENAI_API_KEY` in your shell and use `--model` or `OPENAI_FEEDBACK_MODEL` to select a model that supports Structured Outputs. The CLI accepts a JSON object on standard input. Supply `decision`, `feedback`, and optionally `job_context` and `hard_rules` objects with grounded facts. The OpenAI request includes those inputs and sets `store` to `false`. Keep personal feedback files outside the public repository.

```bash
export PYTHONPATH=src
python -m job_search_agent.feedback < feedback.json
```

## Run the tests and benchmark

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m job_search_agent.feedback_evaluation \
  feedback_interpretation_gold_cases_v1.json --temperature 0.1 > feedback-results.json
```

In PowerShell, set `$env:PYTHONPATH = "src"` before running the Python commands. Select a model that supports the temperature setting or let it use its default sampling configuration.

The benchmark defaults to two runs. It sends inputs and grounding rules to the interpreter and uses the original annotations for scoring. It records the suite version and file hash, exact signal recall and precision, dimension and scope agreement, routing, evidence, hard-rule actions, category differences, and changes between runs. Exact matching includes the free-form feature and scope labels, so reviewers should check apparent misses for valid synonyms before changing the taxonomy or labels. The reported mutation gate checks that proposals cannot apply rule changes. The gold suite's compensation assumptions are evaluation inputs. [Gold-standard fixture](../feedback_interpretation_gold_cases_v1.json)
