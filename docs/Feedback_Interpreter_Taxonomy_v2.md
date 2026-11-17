# Feedback interpreter taxonomy v2

`feedback-taxonomy-v2.0` defines benchmark identifiers for preference features and context scopes. The [versioned vocabulary](../src/job_search_agent/feedback_taxonomy.py) supplies the complete alias list and is part of the evaluation configuration. Each canonical signal carries a feature ID and the original feature label, plus a scope type, scope ID, and the original scope label. Dimension and polarity carry through from the input. Reports can show the original wording alongside the machine identifiers.

## Identity and boundaries

- A feature ID is qualified by its dimension. A scope ID is qualified by its dimension and scope type. The scorer resolves the feature and scope independently, so an equivalent feature label cannot repair an incorrectly typed or broadened scope.
- An alias must name the same concept at the same specificity. Registered labels accept case, whitespace, underscores, and hyphens between letters as formatting variants. There is no stemming, fuzzy matching, automatic abbreviation, or inference from the job context.
- Unregistered labels receive a `literal:` key containing the exact original text. Different unknown labels remain distinct. Exact agreement on an unknown label can still count, and the key makes such agreements visible in reports.
- Narrow distinctions include employer identity, compensation amount and unit, employment type, travel frequency and mode, the extent of onsite presence, and whether a preference targets a career or a specific duty. A `fully_remote` preference does not match an unqualified `remote` preference. Weekly flights and weekly travel have different meanings. `$110/hour C2C` and `$110/hour W-2` require separate identifiers. Assistance specific to small nonprofits remains distinct from a preference for nonprofit work of any size.
- Independent preference signals stay independent. Interest in AI enablement and the opportunity to learn can co-occur. Interest in AI advisory work has a separate identifier from generic advisory work and from interest in an AI advisory career.
- A term such as `quota-carrying sales` is evaluated within its declared dimension and scope. The career alias `quota_carrying_sales` maps to the career scope `quota_sales`. In role responsibilities, carrying a sales quota resolves to `sales_quota_responsibilities` in scope `sales_quota`. Broad dislike of sales careers and dislike of sales-oriented duties each remain distinct from quota-carrying sales careers.

## Registered features and scopes

Each slash-separated grouping names the dimension and scope type. Arrows indicate that a feature ID has a differently named scope ID. IDs listed without arrows are used for both. The table is a vocabulary reference. Report matching checks both independently against the emitted values.

| Dimension and scope type | Feature IDs and associated scope IDs |
| --- | --- |
| `role_responsibilities` / `role_feature` | `status_reporting_heavy_duties` → `status_reporting`, `client_problem_solving`, `ai_workshops`, `advisory_work` → `advisory`, `sales_quota_responsibilities` → `sales_quota`, `transformation_milestone_delivery` → `transformation_delivery`, `client_facing_ai_work` → `client_facing_ai`, `stated_duty_scope` → `stated_scope`, `attractive_underlying_duties` → `interesting_role`, `client_work` → `client_facing`, `python_coding_heavy_duties` → `coding_heavy`, `ai_advisory_responsibilities` → `ai_advisory`, `sales_oriented_work` → `sales_heavy`, `exceptional_role_attractiveness` → `exceptional_role` |
| `career_category` / `career_category` | `contact_center_operations`, `ai_enablement`, `core_banking_replacement`, `ai_solution_architecture`, `ai_evangelism`, `quota_carrying_sales` → `quota_sales`, `ai_product_leadership`, `ai_strategy_consulting`, `consulting` |
| `work_arrangement` / `schedule` | `overnight_on_call`, `night_weekend_coverage` → `night_weekend` |
| `work_arrangement` / `arrangement` | `onsite_schedule`, `fully_remote` |
| `work_arrangement` / `location_arrangement` | `nearby_hybrid` → `hybrid_nearby` |
| `work_arrangement` / `travel_frequency` | `weekly_air_travel` → `weekly_flights`, `occasional_business_travel` → `occasional` |
| `compensation` / `compensation_context` | `c2c_105_hour`, `c2c_110_hour`, `c2c_140_hour`, `w2_80_hour`, `permanent_base_190000`, `this_job_pay` |
| `compensation` / `compensation_transparency` | `base_salary_nondisclosure` → `undisclosed_base` |
| `contract_terms` / `employment_type` | `short_duration_contracts` → `contract` |
| `contract_terms` / `contract_term` | `c2c_billable_work_gaps` → `billing_gaps` |
| `growth_purpose` / `role_feature` | `learning_opportunity` → `learning_new_skills`, `mission_alignment`, `training_and_skill_development` → `skill_development` |
| `growth_purpose` / `mission` | `nonprofit_ai_enablement` |
| `employer` / `employer` | `northstar_tech`, `verity_labs`, `ridgetop_bank`, `current_job_employer`, `omega_health` |
| `industry` / `industry` | `tobacco_industry` → `tobacco` |
| `culture_environment` / `culture_feature` | `micromanagement`, `collaborative_peers` |
| `seniority_scope` / `seniority_feature` | `hands_on_expert_responsibility` → `hands_on_expert`, `large_team_people_management` → `large_team_management`, `many_direct_reports`, `large_ai_transformation_portfolio_ownership` → `large_portfolio_ownership`, `limited_decision_making_autonomy` → `low_autonomy`, `insufficient_seniority` → `not_senior_enough` |

The initial entries cover the frozen gold labels and narrow wording variants. The taxonomy is finite. New concepts can appear in the holdout or production feedback before a reviewer defines aliases for them. A taxonomy revision should record the evidence for equivalence and include a counterexample that must stay distinct. A reference annotation revision follows the separate human approval process in the [gold-case review](Feedback_Interpreter_Gold_Review_v2.md).
