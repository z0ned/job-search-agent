# Feedback interpreter v2 semantic adjudication

The manual review finds substantially more faithful interpretations than the automated scores. It also identifies material errors that survive both passes. The v3 recommendation is to preserve the extraction evidence and scope constraints in the output contract, then derive routing and validate safety in code. [Architecture and Benchmark v3 recommendation](../Feedback_Interpreter_Benchmark_Design_v3.md) · [Canonical taxonomy proposal](../Feedback_Interpreter_Taxonomy_Proposal_v3.md)

## Evidence and review scope

Commit `10e3e4fe024e1794cb377c5f5ccece33333e7751` contains the completed v2 implementation, the frozen 50-case gold and 12-case holdout fixtures, and the existing raw and validated captures and reports. The gold fixture hash is `fbf6872f847d533871ad2db7d3412a324504171f057f56ae7a8f1f8f48311523` and the holdout hash is `c38ff4c44d7cd0110e198b0682833da8f7c70c15e1cfd04489075858ef099393`. All tracked benchmark artifacts match that commit. Each raw and validated pass covers the same case IDs and matches its recorded SHA-256. The two saved v2 passes use `gpt-5.4-2026-03-05`, temperature `0.1`, and prompt `feedback-interpretation-v2.0`. This review uses the saved outputs. [Archive index](../../benchmarks/feedback/README.md) · [Original automated v2 report](../Feedback_Interpreter_Benchmark_Report_v2.md)

Review each statement in the original feedback before aligning expected and emitted signals. Job context can identify a referent. A preference requires a reaction attributable to the user. Compare dimension, referent, polarity, scope, qualifiers, and conditions. An evidence quote also has to support what the structured record claims. Treat strength and quote-span differences as separate diagnostics unless they change the interpretation. Compare route and advisory action independently. Keep each signal in one primary accounting category.

| Category | Meaning |
| --- | --- |
| Equivalent | One expected and one emitted signal express the same preference and material applicability. Formatting and wording can differ. |
| Material mismatch | A related one-to-one counterpart changes meaning or loses a material qualifier in the machine scope, such as changing weekly flights to all weekly travel. |
| Missing | An independently supported reference signal has no emitted counterpart. |
| Unsupported extra | An emission has no independently supported counterpart in the feedback, including a condition emitted as an additional preference. |
| Contested | The reference's breadth, independence, or applicability requires a human decision. The totals show each contested reference and each contested emission. A material difference against a contested reference boundary can also be called out in the notes. |

Equivalent counts are descriptive review judgments over the full denominators. They do not revise the official scores or exclude contested items. External reviewers can resolve those judgments before accepting a new scoring rubric. [Existing gold annotation review](../Feedback_Interpreter_Gold_Review_v2.md)

## Results

| Suite and pass | Expected | Emitted | Equivalent pairs | Material pairs | Missing | Unsupported extras | Contested expected | Contested emitted | Route agreement | Rule action agreement |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Gold 1 | 57 | 57 | 33 | 15 | 1 | 4 | 8 | 5 | 48/50 | 50/50 |
| Gold 2 | 57 | 58 | 34 | 14 | 1 | 4 | 8 | 6 | 48/50 | 50/50 |
| Holdout 1 | 11 | 12 | 9 | 2 | 0 | 1 | 0 | 0 | 11/12 | 12/12 |
| Holdout 2 | 11 | 12 | 9 | 2 | 0 | 1 | 0 | 0 | 11/12 | 12/12 |

The frozen evaluator recorded 17 and 16 canonical matches on the gold suite and zero on both holdout passes. Manual review found 33 and 34 gold equivalents and nine holdout equivalents per pass. The holdout still has two material mismatches and one unsupported extra each pass. Its full-denominator review equivalents are 9/11 of expected signals and 9/12 of emitted signals. [Gold automated report](../../benchmarks/feedback/live_v2_gold/report.json) · [Holdout automated report](../../benchmarks/feedback/live_v2_holdout/report.json)

- **Routing.** FI-028 turns an existing eligibility conflict into a weekday preference and routes it to approval. FI-044 invents a purpose from a vague positive reaction. FH-007 escalates a request to verify posting language while retaining the independently supported accessibility preference. All three recur in both passes. FI-013's frozen route also deserves review because the positive reaction is underspecified.
- **Dimensions, scope, and conditions.** FI-032 and FI-043 explain why positive enthusiasm alone cannot identify a growth-purpose signal. FI-027 loses air travel from a frequency scope. FH-006 loses a most-of-each-day limit. FH-010 replaces a conditional C2C rate objection with an equipment objection. FI-015 keeps the negative polarity field and reverses its meaning by selecting disclosed salary as the target instead of nondisclosure.
- **Missing and extra signals.** FI-041 omits the positive reaction to the AI advisor role while retaining employer distrust. FI-013, FI-026, FI-028, and FI-044 produce unsupported gold extras in both passes. FH-011 emits a second preference from the condition on an otherwise faithful workshop signal.
- **Safety and reference ambiguities.** All emitted negative career categories have direct support in these captures. The automated flags on FI-040 and FH-005 are vocabulary misses with complete evidence. FI-007's distinction between recurring project type and career category remains debatable. FI-006 and FI-035 do not clearly express separate training preferences. FI-050 describes a hypothetical compensation exception without naming a responsibility. These and the other contested cases need a recorded reviewer decision before they can inform an updated reference version.

## Case-by-case review

- [Gold FI-001 through FI-017](Gold_01_17.md)
- [Gold FI-018 through FI-034](Gold_18_34.md)
- [Gold FI-035 through FI-050](Gold_35_50.md)
- [Holdout FH-001 through FH-012](Holdout.md)
