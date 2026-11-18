# Feedback interpreter v3 reference decisions

This record applies to future v3 scoring. The source fixture is `1.0-draft` with SHA-256 `fbf6872f847d533871ad2db7d3412a324504171f057f56ae7a8f1f8f48311523`. [Frozen gold cases](../feedback_interpretation_gold_cases_v1.json)

## FI-007

The user approved the project-type interpretation on November 18, 2026. The feedback was “I am not interested in another core-banking replacement transformation.”

| Field | Frozen reference | Approved interpretation for v3 |
| --- | --- | --- |
| Preference | Negative career-category preference for core-banking replacement | Negative preference for core-banking replacement projects |
| Scope | `career_category` with value `core_banking_replacement` | The recurring project type, independent of employer or job title |
| Career-category interest change | Yes | No |

“Another” indicates a recurring kind of project. Apply the preference where the opportunity involves replacing a core-banking system. The quote establishes no preference about banking as an industry, transformation programs generally, or other types of projects. The existing mild strength, pending approval route, and unchanged hard-rule action carry forward. This decision defines the meaning and scope. A machine identifier can be assigned when the v3 taxonomy is approved. [V2 case adjudication](feedback_adjudication_v2/Gold_01_17.md#fi-007)
