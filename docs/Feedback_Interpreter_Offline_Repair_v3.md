# Feedback interpreter v3 offline repair

Both deterministic repairs were evaluated on the 148 original v3 proposals. The replay recovered 11 validated signals and corrected seven review routes and two hard-rule actions. All expected routes and hard-rule actions match across the replay. Scope still fell short of the approved gate in every suite. [Original live benchmark](Feedback_Interpreter_Benchmark_Report_v3.md)

## What changed

- The validator can now use a submitted qualifier's exact structured posting field to establish USD and hourly or annual pay basis. It requires a verified nonnegative numeric amount and checks that the requested pay basis agrees with the field. The output preserves the original source key and value along with the feedback evidence and condition.
- An anchored request to revisit a confirmed minimum can include a continuation such as “and consider lowering it.” The route remains an advisory review with separate confirmation. Independent preferences remain held for review alongside the request.
- The offline runner verifies the archived raw proposals, original predictions, configuration, and expected case IDs against their recorded fingerprints. It validates saved proposals without making API requests and writes new captures outside the archive. The repair revision is `6fe516af1ef511261f1ee61c14fc242e23398448`. [Prototype](Feedback_Interpreter_Prototype_v3.md)

## Results

The original interpreter reproduced every archived validated record before the repair. The repairs changed 13 records, including two records whose only change was their 1099 review routing and action. Codex reviewers rechecked the changed records with pass identities masked. The offline score reused the archived verdict for each of the 135 identical records.

Each cell gives pass 1 / pass 2. Precision counts validated signals. A validator rejection is tracked separately from a semantic miss so a blocked unsupported attempt remains visible.

| Suite | Metric | Original v3 | Offline repair |
| --- | --- | --- | --- |
| Gold | Semantic recall | 33/51 · 35/51 | 36/51 · 38/51 |
| Gold | Semantic precision | 33/42 · 35/43 | 36/46 · 38/47 |
| Gold | Clear-case scope | 21/38 · 22/38 | 24/38 · 25/38 |
| Gold | Review route agreement | 49/50 · 49/50 | 50/50 · 50/50 |
| Earlier holdout regression | Semantic recall | 9/11 · 9/11 | 10/11 · 10/11 |
| Earlier holdout regression | Semantic precision | 9/9 · 9/9 | 10/10 · 10/10 |
| Earlier holdout regression | Clear-case scope | 6/8 · 6/8 | 7/8 · 7/8 |
| Earlier holdout regression | Review route agreement | 11/12 · 11/12 | 12/12 · 12/12 |
| V3 holdout | Semantic recall | 10/14 · 10/14 | 10/14 · 11/14 |
| V3 holdout | Semantic precision | 10/13 · 10/12 | 10/13 · 11/13 |
| V3 holdout | Clear-case scope | 4/8 · 4/8 | 4/8 · 5/8 |
| V3 holdout | Review route agreement | 11/12 · 10/12 | 12/12 · 12/12 |

Hard-rule action agreement improved from 146/148 to 148/148. Validator rejection records fell from 21 to 10. Every rule stayed unchanged and every accepted signal remained held for review. The archived outputs and references are preserved. [Gold replay](../benchmarks/feedback/offline_v3_gold/adjudicated-report.json) · [Regression replay](../benchmarks/feedback/offline_v3_regression/adjudicated-report.json) · [V3 holdout replay](../benchmarks/feedback/offline_v3_holdout/adjudicated-report.json)

## Recovered behavior and remaining failures

| Cases | Finding |
| --- | --- |
| FI-009, FI-010, FI-043 | Both passes recover the verified C2C pay qualifiers and fully match the pay signal. |
| FI-012 | Both passes recover the positive $190,000 annual USD base signal and the approval route. The proposals omit the permanent-employment qualifier, so neither receives full semantic credit. |
| FH-010 | Both passes retain $115/hour USD on C2C and the condition that the client requires the candidate to supply the lab kit. The case returns to the approval route. |
| FH3-002 | Both passes retain interest in resolving vendor clauses. The tentative $92 hourly 1099 request now routes to profile review for separate confirmation. |
| FH3-009 | Pass 2 retains $94/hour USD on W-2 with agency-paid certification as its condition. Pass 1 still lacks a structured currency claim. |
| FI-033, FI-048, FH3-010 | Structured scope still loses the autonomy level, the intensity of sales work, or the explicit applicability condition. These need focused scope and condition tests. |
| FI-021, FI-041, FH-005, FH3-011 | The raw proposals omit an independent preference. These cases need extraction coverage. |

The remaining misses include issues outside these two fixes. The approved gates still hold learning integration. The archived v3 holdout now serves as regression evidence for the repair. A later live comparison should use a newly sealed holdout.

## Reproduce the offline replay

Use a new output directory outside the archive. An API key is unnecessary. The runner's report includes a case-level comparison against the original validated pass. The adjudicated report adds the hash-bound semantic verdicts.

```sh
PYTHONPATH=src python -m job_search_agent.feedback_replay_v3 \
  benchmarks/feedback/gold_cases_v3.json --suite gold \
  --archive benchmarks/feedback/live_v3_gold --output /tmp/feedback-v3-gold-repair
```

Use `--suite regression` with `holdout_cases_v2.json` and `live_v3_regression`. Use `--suite holdout` with `holdout_cases_v3.json` and `live_v3_holdout`. All 88 unit tests passed, including replay checksum verification and assurance that replay never constructs a live provider.
