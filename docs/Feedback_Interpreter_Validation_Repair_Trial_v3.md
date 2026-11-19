# Feedback interpreter validation and scope repair trial

**The offline trial recovered four supported preferences and corrected two review routes. The previously unseen suite still falls short of the acceptance criteria.** The trial reproduced 180 saved validation records before applying the experimental changes. It used the three two-pass benchmark suites and both arms of the response-schema and signal-independence trials. The replay used zero benchmark API requests. [Case-level replay](../benchmarks/feedback/offline_v3_validation_repair/report.json)

## What the saved proposals showed

| Case | Original failure | Offline result |
| --- | --- | --- |
| FI-042 in both gold passes | “Just not at Omega Health” explicitly limits the adjacent positive career statement. The employer signal cited the career phrase for that limit, although its preference quote started after the phrase. Validation dropped the employer objection. | Extend the employer evidence to the exact contiguous career phrase and employer exception. The existing validator then preserves the career interest and the distinct, career-limited employer objection, with zero validation issues and the same route. |
| FT-002 in schema control and independence treatment | Two original phrases supported the same `dominant` intensity. Validation rejected the repeated qualifier and asked for clarification. | Retain one intensity qualifier and both individually validated anchors. The preference stays limited to work centered on giving safety briefings, and the expected approval route is restored in both records. |
| FT-004 in independence treatment | The employer distrust claim attached a career qualifier drawn from a separate sentence praising the specific posting. | The exact source and adjacency checks leave the unrelated qualifier rejected. |
| FI-033 in both gold passes | The accepted autonomy objection omitted the explicit near-zero limit from its machine-readable scope. | Flag the missing limit with its original wording and keep the proposed signal visible. |
| FI-048 in both gold passes and all four targeted outputs | The sales proposal took “must love sales” as evidence about the amount or centrality of sales work. The quote states an expectation of enthusiasm. | Flag the proposed workload reading for review while keeping the reaction and source wording visible. Independent evidence of the same duty's centrality satisfies this check. |

The employer repair requires one unambiguous adjacent source span and a direct comma-linked exception. The repeated-intensity repair requires all qualifier anchors to pass existing validation, identical controlled levels, and an unchanged recovered condition. Conflicting values and cross-claim evidence remain subject to strict validation. The two scope checks produce review findings and preserve signals, scope values, and routing. The changes run through an isolated replay with the existing interpreter and leave its normal entry point intact.

## Measured changes

| Archived records | Count |
| --- | ---: |
| Validation baselines reproduced | 180 |
| Records identical after the experimental changes | 168 |
| Supported signals recovered | 4 |
| Correct review routes restored | 2 |
| Additional scope review findings | 8 |
| Changes to hard-rule actions or negative career signals | 0 |
| Changes on the previous 12-case fresh holdout, counting both passes | 0/24 |

Every replayed preference stayed held for review. The original gold and holdout fixtures, benchmark configurations, proposals, and outputs are preserved.

## Readiness

The earlier deterministic fixes brought the previous fresh holdout to 10/14 and 11/14 semantic matches. Passing recall requires at least 13/14 on each pass. These corrections leave that shortfall in place. The existing condition recovery could recover one more case in each saved pass. The holdout still includes omitted posting praise and a duty classified as a growth goal. [Prior full-suite replay](Feedback_Interpreter_Offline_Repair_v3.md#results) · [Acceptance criteria](Feedback_Interpreter_Benchmark_Design_v3.md#assessment-of-the-original-acceptance-criteria)

The archived full-suite review identified 13 omissions before validation. FI-011, FI-021, FI-041, FI-047, FH-005, and FH3-011 each omitted an independent reaction in both passes. FI-030 omitted one in the first pass.

The next candidate needs to recover independently expressed reactions missing from the raw proposal and put the right scope on the reactions already captured. Test those changes on focused contrasts before a full two-pass run with a fresh holdout. Learning-engine integration remains gated.

## Reproduce

Run from the repository root with an unused output file. The report verifies source capture hashes and compares each result against its saved validation baseline before showing the changed fields.

```sh
PYTHONPATH=src python -m job_search_agent.feedback_validation_repair_trial_v3 \
  --output /tmp/feedback-v3-validation-repair.json
```
