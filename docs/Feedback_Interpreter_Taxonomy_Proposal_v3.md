# Feedback interpreter taxonomy proposal v3

Keep the v2 evaluator and its archived results as the reproducible baseline. The v2 taxonomy makes literal comparisons more useful through explicit aliases and typed scope IDs. Its fallback preserves exact unknown strings, so two faithful paraphrases can still miss each other and a supported negative career signal can trigger the downgrade gate. V2 also represents scope and conditions as strings. A correct quote can therefore contain a limitation that the proposed signal loses. V3 would represent the limitation explicitly and distinguish registry coverage from evidence support. [V2 taxonomy](Feedback_Interpreter_Taxonomy_v2.md) · [V2 failure analysis](Feedback_Interpreter_Failure_Analysis_v2.md)

## Signal representation

| Field | Proposed contract |
| --- | --- |
| `dimension` | A controlled value such as `career_category`, `role_responsibilities`, or `compensation`. Register each feature in one dimension. A different dimension has its own identifier and review. |
| `feature_id` | A stable registry key such as `career.quota_carrying_sales` or `compensation.quoted_rate`. Keys are immutable and independent of wording, polarity, strength, or a particular posting. A key can define typed parameters when the concept is reusable, such as a rate. |
| `display_label` | Human-readable proposal wording preserved alongside the machine fields. The registry supplies a preferred label for display and can revise or translate it without changing identity. |
| `scope` | A tagged object with a referent and any material qualifiers. Validate the scope type and allowed fields against the feature. A career category, duty, quoted rate, posting, and named employer have different types. A rate records amount, currency, unit, and employment type explicitly. |
| `polarity` and `strength` | Independent controlled values. Polarity records the expressed direction. Strength records emphasis. Neither authorizes a rule change. |
| `condition` | A predicate over the scoped referent or another named participant, anchored to the source. Preserve modality such as required, available, or actual. Keep explicit conjunctions and alternatives distinct. Use `null` for an unconditional reaction. |
| `evidence` | An array of source anchors with roles such as `preference_assertion`, `qualifier`, `condition`, or `context_only`. Each anchor links to an immutable source revision. |
| `identity_status` | `registered` only when the feature exists and its referent and required fields validate against the pinned registry. `candidate` holds an unresolved concept or referent for reviewer assessment and has a null `feature_id`. |

An intrinsic qualifier limits the scope being rated. A condition describes a circumstance under which a reaction applies. Spending most of each day on a duty limits the workload being assessed. A client requiring the candidate to supply equipment conditions a reaction to a rate. A delivery option can condition interest in one activity while leaving the rest of the job unspecified. Keep the original text and its anchor even when a predicate cannot be represented. Hold the signal for review if a material qualifier or condition cannot be resolved.

The stable identity for scoring consists of dimension, registered feature ID, polarity, fully typed scope, and normalized predicate values. The feature ID alone is insufficient. For example, `compensation.quoted_rate` at USD 115 per hour on a C2C contract and the same amount on W-2 identify different scopes. Evidence support, strength, and review routing are separate checks. Registry-level matches and manually adjudicated matches for candidates should appear as separate results, with misses and unresolved candidates visible.

## Evidence and provenance

Reference the exact immutable feedback event or posting revision used to construct a proposal. For feedback, record `source_id`, `source_revision`, `origin`, zero-based half-open `start` and `end` offsets in Unicode code points, `quote`, and the anchor role. Resolve against the exact original text without stripping whitespace or normalizing Unicode before slicing. Verify `text[start:end] == quote`. Reject out-of-range anchors and flag ambiguous legacy spans for review. For a structured context field, use the frozen source revision and a JSON Pointer with the captured value. [Prototype](Feedback_Interpreter_Prototype.md)

The preference assertion must come from the user's own feedback. Posting data and confirmed hard rules can identify a referent or support an eligibility check. They supply no evidence of the direction of a preference. A verified text span establishes provenance. The reviewer still checks whether it establishes the feature, polarity, scope, qualifiers, and conditions. Require explicit direct feedback evidence for a negative career-category proposal, including any exception that narrows the dislike.

## Reviewed examples

These are examples of the proposed representation. The source `original_feedback` refers to the immutable fixture record for the listed case. Production anchors would also carry the actual source revision identifier. The example `registered` IDs illustrate the proposed catalog. They do not modify the frozen fixtures or any measured result. [V2 case findings](Feedback_Interpreter_Failure_Analysis_v2.md) · [Gold fixture](../feedback_interpretation_gold_cases_v1.json) · [Holdout fixture](../benchmarks/feedback/holdout_cases_v2.json)

### FI-040 and FH-005

FI-040 supports the specific quota-carrying sales career category. `quota_carrying_sales_career` in the v2 capture and the gold label describe that same category. FH-005 supports two distinct claims. The negative procurement operations career signal and the positive vendor negotiation duty signal can both be substantively correct while their identities remain unresolved. Neither claim establishes anything about all procurement or supply chain careers. [FI-040 clarification](Feedback_Interpreter_Gold_Review_v2.md) · [Gold capture](../benchmarks/feedback/live_v2_gold/pass-1.json) · [Holdout capture](../benchmarks/feedback/live_v2_holdout/pass-1.json)

```json
[
  {
    "case_id": "FI-040",
    "identity_status": "registered",
    "dimension": "career_category",
    "feature_id": "career.quota_carrying_sales",
    "display_label": "Quota-carrying sales careers",
    "polarity": "negative",
    "strength": "strong",
    "scope": {"type": "career_category", "referent": {"category_id": "quota_carrying_sales"}},
    "condition": null,
    "evidence": [
      {"origin": "original_feedback", "role": "preference_assertion", "start": 0, "end": 46,
       "quote": "I do not want a career in quota-carrying sales"}
    ]
  },
  {
    "case_id": "FH-005",
    "identity_status": "candidate",
    "dimension": "career_category",
    "feature_id": null,
    "display_label": "Procurement operations career",
    "polarity": "negative",
    "strength": "strong",
    "scope": {"type": "career_category", "referent": {"category_label": "procurement operations"}},
    "condition": null,
    "evidence": [
      {"origin": "original_feedback", "role": "preference_assertion", "start": 0, "end": 47,
       "quote": "I don't want a career in procurement operations"}
    ]
  },
  {
    "case_id": "FH-005",
    "identity_status": "candidate",
    "dimension": "role_responsibilities",
    "feature_id": null,
    "display_label": "Vendor negotiation",
    "polarity": "positive",
    "strength": "mild",
    "scope": {"type": "role_duty", "referent": {"duty_label": "vendor negotiation"}},
    "condition": null,
    "evidence": [
      {"origin": "original_feedback", "role": "preference_assertion", "start": 61, "end": 93,
       "quote": "vendor negotiation appeals to me"}
    ]
  }
]
```

### FH-006, FH-010, and FH-011

FH-006 is about processing purchase orders for most of each day. Encode the share of time as `most` per `workday`, with no invented percentage. FH-010 concerns a specific rate under an equipment requirement. The quoted-rate feature can represent a new amount through typed parameters, without minting an ID for every dollar value. FH-011 expresses one workshop preference conditional on possible video delivery. The condition targets the same workshop duty. It supplies no separate preference about the job's arrangement. [Holdout capture](../benchmarks/feedback/live_v2_holdout/pass-1.json) · [Second holdout capture](../benchmarks/feedback/live_v2_holdout/pass-2.json)

```json
[
  {
    "case_id": "FH-006",
    "identity_status": "candidate",
    "dimension": "role_responsibilities",
    "feature_id": null,
    "display_label": "Purchase-order processing for most of each day",
    "polarity": "negative",
    "strength": "strong",
    "scope": {
      "type": "role_duty",
      "referent": {"duty_label": "purchase-order processing"},
      "qualifiers": [{"type": "time_share", "quantity": "most", "period": "workday", "evidence_index": 1}]
    },
    "condition": null,
    "evidence": [
      {"origin": "original_feedback", "role": "preference_assertion", "start": 0, "end": 66,
       "quote": "I do not want to spend most of each day processing purchase orders"},
      {"origin": "original_feedback", "role": "qualifier", "start": 23, "end": 39,
       "quote": "most of each day"}
    ]
  },
  {
    "case_id": "FH-010",
    "identity_status": "registered",
    "dimension": "compensation",
    "feature_id": "compensation.quoted_rate",
    "display_label": "USD 115/hour for this C2C contract",
    "polarity": "negative",
    "strength": "mild",
    "scope": {
      "type": "quoted_rate",
      "referent": {"posting": "current", "amount": "115", "currency": "USD", "unit": "hour",
                   "employment_type": "c2c_contract"}
    },
    "condition": {"predicate": "requires_equipment_provider", "required_by": "client",
                  "provider": "candidate", "item_label": "lab kit", "evidence_index": 1},
    "evidence": [
      {"origin": "original_feedback", "role": "preference_assertion", "start": 0, "end": 50,
       "quote": "I would pass on $115 an hour for this C2C contract"},
      {"origin": "original_feedback", "role": "condition", "start": 51, "end": 92,
       "quote": "if the client makes me supply the lab kit"},
      {"origin": "job_context", "role": "context_only", "json_pointer": "/hourly_rate_usd", "value": 115}
    ]
  },
  {
    "case_id": "FH-011",
    "identity_status": "candidate",
    "dimension": "role_responsibilities",
    "feature_id": null,
    "display_label": "Leading onboarding workshops",
    "polarity": "positive",
    "strength": "mild",
    "scope": {"type": "role_duty", "referent": {"duty_label": "leading onboarding workshops"}},
    "condition": {"predicate": "delivery_mode_available", "target": "scope_referent",
                  "mode": "video", "evidence_index": 1},
    "evidence": [
      {"origin": "original_feedback", "role": "preference_assertion", "start": 0, "end": 46,
       "quote": "I would enjoy leading the onboarding workshops"},
      {"origin": "original_feedback", "role": "condition", "start": 47, "end": 79,
       "quote": "if I could deliver them by video"}
    ]
  }
]
```

## Candidate review and aliases

1. Assign each proposal a record ID with no taxonomy meaning. Preserve its text, attempted dimension, typed scope, evidence, model and prompt provenance, and registry version. An unresolved feature or referent stays a review candidate. Identical candidate labels do not establish a canonical match.
2. Let reviewers assess evidence support and scope independently of identity resolution. A candidate may have direct support, incomplete evidence, broader scope than the evidence permits, or no support. Record the disposition with the reviewer and rationale. A supported negative career proposal with unresolved identity remains held for review. An unsupported negative career proposal fails the zero-tolerance gate regardless of registry coverage.
3. Resolve a candidate to an existing ID when a reviewer confirms an exact semantic fit. Propose a new registry entry when it captures a distinct supported concept. Preserve both records and the resolution under the applicable registry version. Dismiss unsupported proposals with a reason. None of these dispositions applies a preference or an eligibility rule.
4. Admit an alias only when it preserves bidirectional meaning within the same dimension, type, and specificity. Record context of use, supporting examples, and a nearby example that must stay separate. Use guarded aliases for labels with multiple meanings and require their disambiguating scope. Keep names, currencies, amounts, units, frequency, mode, modality, conditions, and exceptions distinct. Broader, narrower, and related concepts can be documented as relationships without sharing an ID.

Build the registry from varied feedback patterns and sources, including new roles, work modes, compensation structures, qualifiers, and conditions. Use human-reviewed examples for both supported and unsupported proposals and reserve blind holdouts. Equivalent labels and material distinctions should be represented in tests. Observed holdout labels can motivate a future taxonomy proposal after review. The same holdout then serves as a diagnostic replay, and a fresh blind set is needed to measure generalization.

## Versioning and initial scope

Pin the schema version and the registry release and fingerprint in every report. Keep past definitions and preferred labels available for replay. Alias additions, deprecations, and splits require recorded review and a new release. An equivalent redirect may link two IDs after review. A split needs explicit resolution and keeps older history interpretable under the older release. Historical scores remain attached to their original registry configuration. Compare revised scores in a separately labeled replay. Approve any change to benchmark annotations separately from registry changes. [Benchmark v2 specification](Feedback_Interpreter_Benchmark_Spec_v2.md) · [Gold review](Feedback_Interpreter_Gold_Review_v2.md)

Start with a small catalog of reviewed concepts, typed career and duty referents, quoted-rate parameters, time-share qualifiers, equipment requirements, and delivery-mode conditions. Prioritize anchors and read-only candidate review. Import a v2 signal automatically only where the alias, typed referent, all material constraints, and evidence offsets map unambiguously. Retain the original v2 export and send ambiguous imports to review. Keep the original gold and holdout versions available for replay. A later scoring implementation should report coverage, grounded support, canonical correctness, and case-level misses separately.

Keep learning disabled. A recognized ID or a supported proposal carries no authority to change a preference or hard rule. Retain the downgrade and hard-rule safeguards, with separate human review of eligibility-rule requests. Before expanding the catalog or testing any integration, review whether the pilot can preserve the restrictions in FH-006, FH-010, and FH-011 and distinguish lexical novelty from unsupported career downgrades in FI-040 and FH-005.
