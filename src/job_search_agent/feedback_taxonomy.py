"""Versioned, conservative vocabulary for feedback benchmark scoring."""

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import re


TAXONOMY_VERSION = "feedback-taxonomy-v2.0"


@dataclass(frozen=True)
class CanonicalSignal:
    dimension: str
    feature_id: str
    feature_label: str
    polarity: str
    scope_type: str
    scope_id: str
    scope_label: str

    def to_dict(self) -> dict:
        return asdict(self)


# Entries give a feature identifier, equivalent display labels, a scope
# identifier, and equivalent scope labels. A scope identifier is scoped to
# the enclosing dimension and type. The vocabulary is independent of any case ID.
_VOCABULARY = {
    ("role_responsibilities", "role_feature"): (
        ("status_reporting_heavy_duties", ("mostly status reporting", "status-reporting-intensive work"),
         "status_reporting", ("status_reporting_duties", "status_reporting_work")),
        ("client_problem_solving", ("solving client problems",),
         "client_problem_solving", ("solving_client_problems",)),
        ("ai_workshops", ("AI solution workshops", "running AI workshops", "running AI solution workshops"),
         "ai_workshops", ("ai_solution_workshops",)),
        ("advisory_work", ("advisory responsibilities", "advisory duties"),
         "advisory", ("advisory_work", "advisory_duties")),
        ("sales_quota_responsibilities", ("carrying a sales quota", "sales quota", "quota-carrying sales duties"),
         "sales_quota", ("carrying_a_sales_quota", "sales_quota_responsibilities")),
        ("transformation_milestone_delivery", ("delivery of defined transformation milestones",
                                                "delivering defined transformation milestones"),
         "transformation_delivery", ("transformation_milestone_delivery",)),
        ("client_facing_ai_work", ("client-facing AI responsibilities",),
         "client_facing_ai", ("client_facing_ai_work",)),
        ("stated_duty_scope", ("scope of duties", "role scope", "scope of this role"),
         "stated_scope", ("role_scope", "scope_of_duties")),
        ("attractive_underlying_duties", ("appealing underlying duties",),
         "interesting_role", ("attractive_underlying_duties", "appealing_underlying_duties")),
        ("client_work", ("client-facing work", "client-facing responsibilities", "client work focus"),
         "client_facing", ("client_work", "client_facing_work")),
        ("python_coding_heavy_duties", ("mostly daily Python coding", "Python-heavy daily work",
                                        "daily work mostly writing Python code"),
         "coding_heavy", ("python_coding_heavy", "python_heavy_daily_work")),
        ("ai_advisory_responsibilities", ("AI advisory work", "AI advisory duties"),
         "ai_advisory", ("ai_advisory_work", "ai_advisory_responsibilities")),
        ("sales_oriented_work", ("sales-heavy work", "sales-focused work"),
         "sales_heavy", ("sales_oriented_work", "sales_focused_work")),
        ("exceptional_role_attractiveness", ("exceptionally attractive role", "exceptional job attractiveness"),
         "exceptional_role", ("exceptionally_attractive_role",)),
    ),
    ("career_category", "career_category"): (
        ("contact_center_operations", ("contact-center operations roles", "contact-center operations career"),
         "contact_center_operations", ("contact_center_operations_roles",)),
        ("ai_enablement", ("AI enablement career path", "AI enablement career direction",
                           "interest in AI enablement roles"),
         "ai_enablement", ("ai_enablement_career", "ai_enablement_career_path")),
        ("core_banking_replacement", ("core-banking replacement transformation", "core-banking replacement work",
                                      "core-banking replacement transformation roles"),
         "core_banking_replacement", ("core_banking_replacement_transformation",)),
        ("ai_solution_architecture", ("AI solution architect roles", "AI solution architecture career",
                                      "move into AI solution architecture"),
         "ai_solution_architecture", ("ai_solution_architect", "ai_solution_architect_roles")),
        ("ai_evangelism", ("AI evangelist roles", "AI evangelism career"),
         "ai_evangelism", ("ai_evangelist", "ai_evangelist_roles")),
        ("quota_carrying_sales", ("quota-carrying sales careers", "quota sales", "quota-bearing sales"),
         "quota_sales", ("quota_carrying_sales", "quota_bearing_sales", "quota_carrying_sales_careers")),
        ("ai_product_leadership", ("AI product leadership career",),
         "ai_product_leadership", ("ai_product_leadership_career",)),
        ("ai_strategy_consulting", ("AI strategy consulting career",),
         "ai_strategy_consulting", ("ai_strategy_consulting_career",)),
        ("consulting", ("consulting as a career", "consulting career"),
         "consulting", ("consulting_career",)),
    ),
    ("work_arrangement", "schedule"): (
        ("overnight_on_call", ("overnight on-call rotation", "rotating overnight on-call duties",
                               "rotating overnight on-call"),
         "overnight_on_call", ("overnight_on_call_rotation", "rotating_overnight_on_call")),
        ("night_weekend_coverage", ("night/weekend coverage", "night and weekend coverage"),
         "night_weekend", ("night_weekend_coverage", "night_and_weekend_coverage")),
    ),
    ("work_arrangement", "arrangement"): (
        ("onsite_schedule", ("on-site schedule", "onsite work schedule"),
         "onsite_schedule", ("on_site_schedule", "onsite_work_schedule")),
        ("fully_remote", ("fully remote work", "100% remote", "fully remote arrangement"),
         "fully_remote", ("fully_remote_work", "100% remote", "fully_remote_arrangement")),
    ),
    ("work_arrangement", "location_arrangement"): (
        ("nearby_hybrid", ("hybrid at a nearby office", "nearby hybrid work"),
         "hybrid_nearby", ("nearby_hybrid", "nearby_hybrid_work")),
    ),
    ("work_arrangement", "travel_frequency"): (
        ("weekly_air_travel", ("weekly flights", "flying every week", "weekly travel by air"),
         "weekly_flights", ("weekly_air_travel", "flying_every_week")),
        ("occasional_business_travel", ("occasional business trips", "occasional work travel"),
         "occasional", ("occasional_business_travel", "occasional_business_trips")),
    ),
    ("compensation", "compensation_context"): (
        ("c2c_110_hour", ("C2C hourly rate of $110", "$110/hour C2C rate", "$110/hour C2C"),
         "c2c_110_hour", ("c2c_110_per_hour", "c2c_110_usd_hour")),
        ("c2c_140_hour", ("C2C rate of $140", "C2C hourly rate of $140", "$140/hour C2C rate", "$140/hour C2C"),
         "c2c_140_hour", ("c2c_140_per_hour", "c2c_140_usd_hour")),
        ("w2_80_hour", ("W-2 rate of $80", "W-2 hourly rate of $80", "$80/hour W-2 rate", "$80/hour W-2"),
         "w2_80_hour", ("w2_80_per_hour", "w2_80_usd_hour")),
        ("permanent_base_190000", ("annual base of $190000", "$190,000 base salary", "$190000 base salary",
                                    "$190,000 annual base salary"),
         "permanent_base_190000", ("permanent_190000_base", "permanent_190000_base_year")),
        ("c2c_105_hour", ("C2C rate of $105", "C2C hourly rate of $105", "$105/hour C2C rate", "$105/hour C2C"),
         "c2c_105_hour", ("c2c_105_per_hour", "c2c_105_usd_hour")),
        ("this_job_pay", ("compensation in this job", "this job's pay", "pay for this job"),
         "this_job_pay", ("this_job_compensation", "pay_for_this_job")),
    ),
    ("compensation", "compensation_transparency"): (
        ("base_salary_nondisclosure", ("employer salary nondisclosure", "base salary nondisclosure",
                                       "undisclosed base salary", "refusal to disclose base salary"),
         "undisclosed_base", ("undisclosed_base_salary", "base_salary_nondisclosure")),
    ),
    ("contract_terms", "employment_type"): (
        ("short_duration_contracts", ("short contracts", "short-term contracts"),
         "contract", ()),
    ),
    ("contract_terms", "contract_term"): (
        ("c2c_billable_work_gaps", ("unbillable gaps in C2C contracts", "C2C billable work gaps",
                                    "gaps in billable C2C work"),
         "billing_gaps", ("billable_work_gaps", "c2c_billable_work_gaps")),
    ),
    ("growth_purpose", "role_feature"): (
        ("learning_opportunity", ("opportunity to learn", "opportunity to learn new skills"),
         "learning_new_skills", ("learning_opportunity", "opportunity_to_learn_new_skills")),
        ("mission_alignment", ("alignment with the mission", "resonance with the mission"),
         "mission_alignment", ("alignment_with_mission", "mission_resonance")),
        ("training_and_skill_development", ("training and developing skills", "training and developing new skills"),
         "skill_development", ("training_and_skill_development",)),
    ),
    ("growth_purpose", "mission"): (
        ("nonprofit_ai_enablement", ("AI assistance to nonprofits", "helping nonprofits apply AI"),
         "nonprofit_ai_enablement", ("helping_nonprofits_apply_ai", "nonprofit_ai_assistance")),
    ),
    ("employer", "employer"): (
        ("northstar_tech", ("Northstar Tech employer",), "northstar_tech", ()),
        ("verity_labs", (), "verity_labs", ()),
        ("ridgetop_bank", (), "ridgetop_bank", ()),
        ("current_job_employer", ("this employer", "current employer in this job posting"),
         "current_job_employer", ("this_employer",)),
        ("omega_health", (), "omega_health", ()),
    ),
    ("industry", "industry"): (
        ("tobacco_industry", ("tobacco", "tobacco sector"), "tobacco", ("tobacco_industry", "tobacco_sector")),
    ),
    ("culture_environment", "culture_feature"): (
        ("micromanagement", ("manager micromanagement", "micromanaging management style"),
         "micromanagement", ("manager_micromanagement",)),
        ("collaborative_peers", ("thoughtful collaborative peers", "thoughtful and collaborative technical team"),
         "collaborative_peers", ("collaborative_teammates",)),
    ),
    ("seniority_scope", "seniority_feature"): (
        ("hands_on_expert_responsibility", ("hands-on expert role", "trusted hands-on expert"),
         "hands_on_expert", ("hands_on_expert_responsibility",)),
        ("large_team_people_management", ("managing a large team", "large-team management"),
         "large_team_management", ("large_team_people_management", "managing_a_large_team")),
        ("many_direct_reports", ("large direct-report responsibility", "managing many direct reports"),
         "many_direct_reports", ("large_direct_report_responsibility",)),
        ("large_ai_transformation_portfolio_ownership", ("larger AI transformation portfolio ownership",
                                                         "owning a larger AI transformation portfolio"),
         "large_portfolio_ownership", ("larger_ai_transformation_portfolio_ownership",)),
        ("limited_decision_making_autonomy", ("low decision-making autonomy", "little decision-making autonomy"),
         "low_autonomy", ("limited_decision_making_autonomy", "low_decision_making_autonomy")),
        ("insufficient_seniority", ("role is not senior enough", "insufficient role seniority"),
         "not_senior_enough", ("insufficient_seniority", "insufficient_role_seniority")),
    ),
}


def _alias_key(label: str) -> str:
    # Separator and case variants are accepted only for registered labels.
    # Preserve hyphens before numbers so a signed rate never loses its sign.
    words = re.sub(r"(?<=[^\W\d_])-(?=[^\W\d_])", " ", label.strip().casefold())
    return re.sub(r"[\s_]+", " ", words)


def _add_aliases(index, context, identifier, labels):
    for label in (identifier, *labels):
        key = (*context, _alias_key(label))
        if index.setdefault(key, identifier) != identifier:
            raise ValueError(f"Ambiguous taxonomy alias {label!r} in {context!r}.")


def _build_indexes():
    features, scopes = {}, {}
    for (dimension, scope_type), definitions in _VOCABULARY.items():
        for feature_id, feature_labels, scope_id, scope_labels in definitions:
            _add_aliases(features, (dimension,), feature_id, feature_labels)
            _add_aliases(scopes, (dimension, scope_type), scope_id, scope_labels)
    return features, scopes


_FEATURES, _SCOPES = _build_indexes()


def canonicalize_signal(signal: Mapping) -> CanonicalSignal:
    """Resolve registered labels, preserving exact unknown labels and original text."""
    dimension = signal["dimension"]
    scope_type = signal["scope"]["type"]
    feature_label = signal["feature"]
    scope_label = signal["scope"]["value"]
    return CanonicalSignal(
        dimension=dimension,
        feature_id=_FEATURES.get((dimension, _alias_key(feature_label)), "literal:" + feature_label),
        feature_label=feature_label,
        polarity=signal["polarity"],
        scope_type=scope_type,
        scope_id=_SCOPES.get((dimension, scope_type, _alias_key(scope_label)), "literal:" + scope_label),
        scope_label=scope_label,
    )
