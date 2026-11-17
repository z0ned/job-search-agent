# Feedback interpreter benchmark v2 specification

The benchmark measures whether the interpreter can propose evidence-grounded, appropriately scoped feedback for human review. Use the frozen `1.0-draft` gold fixture for longitudinal comparison and the separate holdout for examples developed without seeing model predictions. Neither route enables the learning engine. [Frozen gold cases](../feedback_interpretation_gold_cases_v1.json) · [Holdout fixtures and artifacts](../benchmarks/feedback/README.md)

## Inference and capture

- Pin the model snapshot, temperature, prompt version, input file hash, and number of passes. The evaluation configuration for this iteration is `gpt-5.4-2026-03-05` at `0.1`, with two independent, stateless passes per suite.
- Send the original feedback, decision, job context, and confirmed hard-rule assumptions to the interpreter. Expected routes, reference signals, and their taxonomy spellings stay with the evaluator. Requests to the Responses API set `store: false`.
- Capture raw structured provider proposals and validated predictions by case ID for every pass. Keep execution failures in the case record. Retain the original literal report, revised reports, input fingerprints, and the model/prompt configuration. Score captured predictions again with the replay option when testing evaluator changes.
- Validate the entire frozen gold suite and all prediction IDs before comparing passes. A completed benchmark can fail its quality gates. A failed API call or validator rejection prevents the affected pass from qualifying as a clean pass.

## Scoring

| Measure | Comparison |
| --- | --- |
| Literal signal precision and recall | Exact feature label, polarity, scope type, and scope value, using the original v1 matching rules. A changed label or scope counts as a miss and an extra. |
| Literal exact-case agreement | Original v1 signal fields, including strength, condition, and evidence span, plus expected route, expected rule action, and the existing case checks. |
| Canonical signal precision and recall | One-to-one matches on dimension, canonical feature ID, polarity, typed canonical scope ID, and condition. Explicit, dimension-aware aliases normalize equivalent labels and context IDs. Condition text still matches literally. |
| Incorrectly scoped signals | Unmatched signals with the same feature identity, dimension, polarity, and condition that differ on typed scope. These receive no match credit in precision or recall. |
| Incorrectly conditioned signals | Remaining unmatched signals with the same dimension, feature identity, polarity, and typed scope that differ on condition text. These also receive no match credit. |
| Clear-case dimension and scope | Agreement on the multiset of dimensions and typed canonical scopes for cases expected to route to approval. |
| Cross-pass stability | Literal stability compares route, rule action, and signal fields other than evidence span. Canonical stability compares route, rule action, canonical signal identity, condition, and strength. |

Count each expected and emitted signal once. Compute precision over emitted signals and recall over reference signals across the full pass. Case-level diagnostics keep the original display labels and canonical identifiers visible. Read scope errors alongside missed and extra signals so a semantically related pair with the wrong scope cannot disappear into an alias. Unmapped values retain their literal identity. A taxonomy alias must identify the same concept at the same scope and level of specificity. [Canonical taxonomy](Feedback_Interpreter_Taxonomy_v2.md)

## Gates and review

The acceptance targets are at least 95% clear-case canonical dimension and scope agreement, at least 90% canonical signal recall, correct routing of every clarification and profile-fact reference case, and grounded verbatim evidence on every emitted signal. The evaluator records the literal gate results for continuity. Both clean passes must meet the gates before this benchmark can support a readiness recommendation.

A case that proposes a negative career category without a narrowly matching reference category and the complete frozen evidence span fails the downgrade gate. A case that changes or cannot confirm preservation of hard rules fails the non-mutation gate. The authorization gate requires the expected rule action and a schema-conforming record. A separate-confirmation action also requires the profile-fact review route. Read verbatim grounding and semantic entailment separately during case review. A verbatim quote can still fail to support the feature, polarity, or breadth of a proposal.

Freeze the holdout's expected results before prompt changes and trace any annotation concerns in the review document. A reviewer must approve a new version before any change to gold expectations. Run both passes on the original fixture and the holdout with the same model configuration, and review case-level disagreements before approving any learning-engine integration or merge to `main`. [Proposed annotation review](Feedback_Interpreter_Gold_Review_v2.md)

## Commands

Use Python 3.12 or later with an environment-configured `OPENAI_API_KEY`. Run the test suite and the two live evaluations from the repository root. Use a new directory for each capture.

```sh
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python -m job_search_agent.feedback_evaluation \
  feedback_interpretation_gold_cases_v1.json \
  --model gpt-5.4-2026-03-05 --temperature 0.1 --runs 2 \
  --save-predictions gold-v2-capture > gold-v2-report.json
PYTHONPATH=src python -m job_search_agent.feedback_evaluation \
  benchmarks/feedback/holdout_cases_v2.json --expected-count 12 \
  --model gpt-5.4-2026-03-05 --temperature 0.1 --runs 2 \
  --save-predictions holdout-v2-capture > holdout-v2-report.json
```

Replay a pair of captures by supplying their validated `pass-1.json` and `pass-2.json` files with repeated `--predictions` options. Use the same suite path and case count.
