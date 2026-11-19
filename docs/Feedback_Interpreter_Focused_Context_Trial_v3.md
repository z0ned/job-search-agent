# Feedback interpreter focused context check

The classifier previously saw the AI advisor posting praise and gave an explicit reason for treating it as context. This trial tests whether a focused check of each quoted passage, using the original comment, evaluates that decision accurately. [Reaction accounting results](Feedback_Interpreter_Reaction_Accounting_Trial_v3.md#results)

## Protocol frozen before inference

Run `gpt-5.4-2026-03-05` at temperature `0.1` for two independent passes. Each request receives one exact focus quote and the original feedback, decision, posting context, and hard rules. Prior proposals, explanations, role labels, and expected answers stay outside the request. The model returns one clause role and at most one typed preference. Code attaches the exact quote, combines the responses for the case, and runs the existing validator and routing. A malformed or inconsistent response remains visible in the capture and fails the case. [Focused instructions](../benchmarks/feedback/focused_context_trial_v3.txt)

| Case | What the check must preserve |
| --- | --- |
| FI-041 | Explicit praise of the particular AI advisor posting and the separate objection to the employer. |
| FH3-002 | The clear duty preference and the explicit request about a confirmed pay rule. Keep separate confirmation and every rule value. |
| FC3-001 and FC3-002 | A paired contrast between an evaluation of a specific opening and a neutral mention of the same opening, alongside the same independently expressed employer objection. |
| FC3-003 | One independent preference and a supporting reason that contributes no second preference. |
| FC3-004 | Vague approval produces a focused clarification request and zero preference signals. |

Run the 11 preselected quotes in each pass, for 22 requests. Use the saved verified spans for the two benchmark cases and freeze the independently authored spans and references for the four contrast cases before inference. The trial measures decisions about supplied evidence. A later full benchmark must also test whether the interpreter finds that evidence on its own. [Fresh contrast fixture](../benchmarks/feedback/focused_context_trial_cases_v3.json)

Review quotes and final outputs against the frozen references. Match complete preference meaning, including scope, polarity, material limits, and conditions, separately in raw and validated outputs. The check passes only if all 12 case records and all 22 quote roles match, including both FI-041 preferences and all neutral and supporting controls in each pass. All review routes and advisory hard-rule actions must be correct. Require grounded evidence, zero validator rejections or unsupported extras, no unsupported career downgrades, and no unauthorized rule changes. Keep all accepted proposals held for review. A pass supports review of the approach and a larger test with fresh inputs.

## Capture command

Run from the repository root with a new output directory.

```sh
PYTHONPATH=src python -m job_search_agent.feedback_focused_context_trial_v3 \
  --output /tmp/feedback-v3-focused-context
```

## Results

**The focused check recovered both AI advisor preferences in both passes. The trial missed its gate because it also turned vague approval into an unsupported posting preference in both passes.** [Semantic scorecard](../benchmarks/feedback/live_v3_focused_context_trial/semantic-report.json)

The protocol and contrast cases were frozen at `8ad7ae2c7ba8b68e640ebca62cdac42d13e7378d`. Live inference used `497af3eaf9ffeed4f07a4dcdc2337e1ddaf0c992`. All 22 requests completed without API or execution errors, in 42.038 seconds of summed request time. The trace reproduces the source-only input fingerprints, each exact focus quote, and each raw response. Independent reviewers scored one final pass each against the frozen references. [Configuration](../benchmarks/feedback/live_v3_focused_context_trial/configuration.json) · [Request trace](../benchmarks/feedback/live_v3_focused_context_trial/request-trace.json) · [Adjudications](../benchmarks/feedback/live_v3_focused_context_trial/adjudications.json)

| Measure across both passes | Result |
| --- | ---: |
| Correct quote roles | 20/22 |
| Preference recall before and after validation | 14/14 |
| Preference precision before and after validation | 14/16 |
| Fully correct cases | 10/12 |
| Correct review routes | 10/12 |
| Correct hard-rule actions | 12/12 |
| Validator rejections, unsupported career downgrades, and unauthorized hard-rule changes | 0 |

| Case | Result across both passes |
| --- | --- |
| FI-041 | Recovered the positive evaluation of the specific AI advisor posting and the separate distrust of Trustline AI. Both preferences used the reference dimensions and scopes. The prior accounting classifier missed the praise and assigned the employer objection to culture in both passes. |
| FH3-002 | Kept the positive vendor-clause duty and routed the proposed $92 hourly minimum to separate confirmation. The existing rules stayed intact. |
| FC3-001 and FC3-002 | Kept explicit posting praise and the independent employer objection in the first case. The neutral description in the matched second case supplied context only. The employer objection survived in both. |
| FC3-003 | Kept the voltage-diagnosis preference and treated its stated benefit as context. |
| FC3-004 | The source said “Seems pretty good so far.” The check used the posting title to turn the vague impression into a preference for the whole opening. The existing validator accepted the structurally valid proposal, so no clarification was requested. |

The result isolates the remaining failure at the point where the model decides whether the user supplied an identifiable target. Requiring an exact quote verifies the words and their location. It cannot establish that a vague reaction supports the particular target supplied by the posting. Before promoting this approach, test that target distinction on fresh examples. The focused trial used preselected quotes, so the full benchmark still needs to verify that the interpreter finds the evidence itself. The full benchmark and learning integration remain on hold.
