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
