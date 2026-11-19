# Feedback interpreter claim independence and scope trial

The earlier replay held FI-033 autonomy and FI-048 sales proposals when reviewers disagreed about the relationship between claims or the scope of one claim. This offline trial gives those questions separate judgments and keeps disputed reactions visible with review flags. [Earlier replay](Feedback_Interpreter_Claim_Review_Replay_v3.md#results)

## Protocol

Use both validated arms of the existing ten-case live trial. Create two masked views of the same original feedback and posting context. Two reviewers judge claim relationships from the preference anchors and complete feedback. They see the indexed quotes without the proposed taxonomy, polarity, or qualifiers. Two other reviewers judge the scope of each full proposal. They see the complete proposal and its evidence without the relationship judgments. Withhold case IDs, arm labels, gold references, and prior verdicts from both reviews. Freeze reviewer outputs before scoring. [Saved live trial](../benchmarks/feedback/live_v3_extraction_independence_trial/report.json)

| Judgment | Questions |
| --- | --- |
| Claim relationship | Does the indexed wording evaluate a distinct target, explain or restate another reaction, or leave that relationship unresolved? Link an explanation to the specific independent claim it supports. |
| Proposed scope | Does the full source support this polarity, dimension, referent, material qualifier, and condition as proposed? Record `supported`, `unsupported`, or `unresolved`. Consider what the evidence establishes about the degree and applicability of the reaction. |

Require agreement on each judgment and on the target of any explanatory link. Resolve disagreements to `unresolved`. A linked explanation becomes context only when both reviewers agree on that relationship and the target is independently supported as a claim. Keep all other claims visible. Flag a visible claim when its relationship is unresolved or its scope lacks agreement on full support. A flag preserves a proposal for review. Every proposal retains the archive's held-for-review status. The replay projects saved signal indices and preserves existing case routing, profile facts, validation diagnostics, and hard-rule actions.

Use the frozen semantic adjudications after the review. Report visible recall and precision separately from unflagged-list recall and precision. A matched claim with a flag remains visible and creates no permission to treat its scope as settled. Count unresolved and unsupported scopes and include every unflagged reference extra explicitly. Compare each arm against its own archived routing and validation results. Earlier validation losses remain in the score.

The targeted test requires every previously matched signal to remain visible, the broad FI-033 claim to stay out of the unflagged list, and any material FI-048 scope disagreement to appear on its visible objection. FI3X-001 must keep the specific reaction and demote only its agreed summary. FI3X-002 must preserve both distinct objections. FI3X-003 and FI3X-004 must maintain the correct profile-review route and preserve the independently stated positive signal in the latter case. The projection must preserve all archived routes and hard-rule actions and introduce no mutation or application. These checks measure a small offline review workflow on two captures of ten cases.

## Results

**The split restored visibility for all four previously held matches and missed the FI-033 gate in both arms.** Reviewers agreed on 24 of 26 claim relationships and 26 of 26 scope judgments. The two relationship disagreements are both instances of the same FI-033 comment. The replay made zero benchmark API requests. [Blinded reviews](../benchmarks/feedback/offline_v3_claim_scope_review/reviews.json) · [Consensus decisions](../benchmarks/feedback/offline_v3_claim_scope_review/decisions.json) · [Case-level scorecard](../benchmarks/feedback/offline_v3_claim_scope_review/comparison.json)

| Measure | Control | Treatment |
| --- | ---: | ---: |
| Archived precision | 11/14 | 9/12 |
| Visible-list precision | 11/13 | 9/11 |
| Visible-list recall | 11/12 | 9/12 |
| Unflagged-list precision | 9/11 | 7/9 |
| Unflagged-list recall | 9/12 | 7/12 |
| Visible reference matches carrying a review flag | 2 | 2 |
| Unflagged outputs without a frozen reference match | 2 | 2 |
| Correct archived routes | 10/10 | 9/10 |
| Correct archived hard-rule actions | 10/10 | 10/10 |

Visible-list recall equals the original validated recall in both arms. The earlier single-judgment replay left the four matches out of its independent list. The unflagged-list scores show why visibility and clearance need separate measures. All candidates remain held for review. [Replay projection](../benchmarks/feedback/offline_v3_claim_scope_review/replay.json)

| Case | Result |
| --- | --- |
| FI-033 | The relationship reviewers disagreed on whether the autonomy clause adds a distinct claim or explains “too junior.” Both scope reviewers supported the autonomy scope. The autonomy signal stayed visible and flagged. The broad seniority claim stayed unflagged because the relationship decision was recorded on the autonomy signal alone. The frozen reference scores the broad claim as an extra. |
| FI-048 | Both reviewers confirmed that the objection is an independent reaction. The scope reviewers marked the control's “sales-focused” wording unresolved and the treatment's “sales-heavy” wording unsupported because it implies a substantial workload share. Both versions stayed visible with a scope flag. |
| FI3X-001 | The reviewers linked the introductory authority complaint to the objection about inspection order. Both arms retained the specific claim and moved the summary to context. |
| FI3X-002 | Both distinct objections stayed visible. The reviewers accepted duty scope for the budget objection. The frozen reference expects seniority scope, so this is the second unflagged reference mismatch in each arm. |
| FI3X-003 and FI3X-004 | Both profile-review routes and the independent positive debrief preference were preserved. The posting fact in FI3X-003 yielded zero signals. |
| FT-002 and FT-004 | The treatment's two archived validator rejections remained visible in the diagnostics. FT-002 stayed on the original incorrect clarification route. |

The replay preserved the archive's review details and advisory hard-rule actions. No hard rules were mutated, and the saved cases contained no unsupported career downgrades. The approved references and existing captures remain intact.

## Recommendation

Keep separate scope and relationship judgments for review. The FI-033 result suggests that a disputed relationship should flag both implicated claims while preserving the source evidence and each claim's own scope verdict. Test that policy separately from taxonomy disagreements such as FI3X-002 and validator losses such as FT-002. The targeted gate leaves the full live benchmark and learning integration on hold.

## Reproduce the projection

Run from the repository root with an unused output file.

```sh
PYTHONPATH=src python -m job_search_agent.feedback_claim_scope_review_v3 \
  --archive benchmarks/feedback/live_v3_extraction_independence_trial \
  --decisions benchmarks/feedback/offline_v3_claim_scope_review/decisions.json \
  --output /tmp/feedback-v3-claim-scope-review.json
```
