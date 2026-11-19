"""Replay narrow validator and scope repairs on saved v3 proposals."""

import argparse
from hashlib import sha256
from pathlib import Path
import sys
from types import SimpleNamespace

from . import (
    feedback_autonomy_review_v3, feedback_employer_context_repair_v3, feedback_enthusiasm_scope_v3,
    feedback_intensity_repair_v3, feedback_v3,
)
from .feedback_evaluation import GoldSuite, _save_json, load_suite
from .feedback_evaluation_v3 import _fingerprint, _live_configuration, load_v3_suite
from .feedback_extraction_independence_trial_v3 import CONTRAST_IDS, DEFAULT_CONTRASTS
from .feedback_extraction_trial_replay_v3 import DEFAULT_NOVEL
from .feedback_extraction_trial_v3 import KNOWN_FIXTURES, _load_trial
from .feedback_replay_v3 import _ArchivedProposalProvider, _archive_configuration, _archived_passes, _read_archive_json


ROOT = Path("benchmarks/feedback")


def _full_benchmark_batches():
    for kind, fixture in KNOWN_FIXTURES.items():
        suite = load_v3_suite(fixture, kind)
        live = ROOT / f"live_v3_{kind}"
        offline = ROOT / f"offline_v3_{kind}"
        configuration = _live_configuration(SimpleNamespace(suite=kind, scenarios=fixture), suite, None)
        report, report_hash, live_config, config_hash = _archive_configuration(live, configuration)
        source = live_config["evaluation_source"]
        old_report, offline_hash = _read_archive_json(offline / "report.json")
        for (raw, _, metadata), older in zip(_archived_passes(live, suite, report, source), old_report["runs"], strict=True):
            number = metadata["pass_number"]
            if older["pass_number"] != number or older["raw_proposals_sha256"] != metadata["raw_proposals_sha256"]:
                raise ValueError(f"{kind} pass {number} has mismatched offline repair provenance")
            prior, prior_hash = _read_archive_json(offline / f"pass-{number}.json", older["predictions_sha256"])
            yield suite, raw, prior, {
                "id": f"{kind}/pass-{number}", "model": source["requested_model"], "prompt_version": source["prompt_version"],
                "source_report_sha256": report_hash, "source_configuration_sha256": config_hash,
                "raw_proposals_sha256": metadata["raw_proposals_sha256"], "baseline_predictions_sha256": prior_hash,
                "baseline_report_sha256": offline_hash, "fixture_sha256": suite.sha256,
                "recover_explicit_conditions": False,
            }


def _targeted_trial_batches():
    known, rules, _, _ = _load_trial(DEFAULT_NOVEL)
    contrasts = load_suite(DEFAULT_CONTRASTS, expected_count=len(CONTRAST_IDS))
    if _fingerprint(contrasts.hard_rules) != _fingerprint(rules):
        raise ValueError("trial fixtures disagree on hard rules")
    cases = {case["case_id"]: case for case in [*known, *contrasts.cases]}
    for kind, arms in (("schema", ("control", "trial")), ("independence", ("control", "treatment"))):
        archive = ROOT / f"live_v3_extraction_{kind}_trial"
        report, report_hash = _read_archive_json(archive / "report.json")
        configuration, config_hash = _read_archive_json(archive / "configuration.json", report["configuration_sha256"])
        if configuration.get("recover_explicit_conditions") is not True or set(report["arms"]) != set(arms):
            raise ValueError(f"{kind} trial lacks the original evidence recovery and arm configuration")
        if kind == "independence" and configuration["synthetic_fixture"]["sha256"] != contrasts.sha256:
            raise ValueError("the independence trial fixture does not match its captured fingerprint")
        case_ids = (configuration["case_ids"] if kind == "schema"
                    else configuration["known_case_ids"] + configuration["synthetic_case_ids"])
        source_cases = [cases[case_id] for case_id in case_ids]
        suite = GoldSuite(kind, _fingerprint(source_cases), source_cases, rules)
        for arm in arms:
            metadata = report["arms"][arm]
            raw, raw_hash = _read_archive_json(archive / f"{arm}.proposals.json", metadata["raw_proposals_sha256"])
            prior, prior_hash = _read_archive_json(archive / f"{arm}.json", metadata["validated_sha256"])
            yield suite, raw, prior, {
                "id": f"{kind}/{arm}", "model": configuration["model"],
                "prompt_version": next(iter(prior.values()))["prompt_version"],
                "source_report_sha256": report_hash, "source_configuration_sha256": config_hash,
                "raw_proposals_sha256": raw_hash, "baseline_predictions_sha256": prior_hash,
                "baseline_report_sha256": report_hash, "fixture_sha256": suite.sha256,
                "recover_explicit_conditions": True,
            }


def _revalidate(case, hard_rules, proposal, metadata):
    return feedback_v3.interpret_feedback_v3(
        case["decision"], case["original_feedback"], case["job_context"],
        provider=_ArchivedProposalProvider(metadata["model"], proposal), hard_rules=hard_rules,
        recover_explicit_conditions=metadata["recover_explicit_conditions"],
    )


def _repaired_prediction(case, hard_rules, proposal, metadata):
    feedback = case["original_feedback"]
    joined = feedback_employer_context_repair_v3.prepare_employer_career_context(proposal, feedback)
    prepared, extra_evidence = feedback_intensity_repair_v3.prepare_duplicate_intensity(joined, feedback, case["job_context"])
    result = _revalidate(case, hard_rules, prepared, metadata)
    for signal in result["interpretations"]:
        for anchor in extra_evidence.get(signal["clause_index"], ()):
            if anchor not in signal["evidence"]:
                signal["evidence"].append(anchor)
    arguments = result["clauses"], result["interpretations"]
    findings = [*feedback_autonomy_review_v3.near_zero_autonomy_findings(*arguments),
                *feedback_enthusiasm_scope_v3.enthusiasm_scope_findings(*arguments)]
    if findings:
        result["evidence_findings"] = [*result.get("evidence_findings", ()), *findings]
    return result, {
        "joined_employer_exception": joined is not proposal,
        "coalesced_intensity_clause_indices": sorted(extra_evidence),
        "new_scope_findings": findings,
    }


def _compare_batch(suite, raw, baseline, metadata):
    expected_ids = {case["case_id"] for case in suite.cases}
    if raw.keys() != baseline.keys() or raw.keys() != expected_ids:
        raise ValueError(f"{metadata['id']} does not cover the full archived case set")
    changes = {}
    for case in suite.cases:
        cid = case["case_id"]
        prefix = f"{metadata['id']}/{cid}"
        before = _revalidate(case, suite.hard_rules, raw[cid], metadata)
        if before != baseline[cid] or before.get("prompt_version") != metadata["prompt_version"]:
            raise ValueError(f"{prefix} no longer reproduces its saved validation baseline")
        after, repairs = _repaired_prediction(case, suite.hard_rules, raw[cid], metadata)
        same_action = before["hard_constraint_action"] == after["hard_constraint_action"]
        all_held = all(signal["application_status"] == "held_for_review" for signal in after["interpretations"])
        old_downgrades = [s for s in before["interpretations"] if s["dimension"] == "career_category" and s["polarity"] == "negative"]
        new_downgrades = [s for s in after["interpretations"] if s["dimension"] == "career_category" and s["polarity"] == "negative"]
        if not same_action or after["hard_constraints_mutated"] is not False or not all_held or old_downgrades != new_downgrades:
            raise ValueError(f"{prefix} changed rule authority or a negative career signal")
        if before == after:
            continue
        fields = {field: {"before": before.get(field), "after": value} for field, value in after.items()
                  if before.get(field) != value}
        changes[cid] = {**repairs, "fields": fields, "expected_route": case["expected_review_status"],
                        "signal_count_before": len(before["interpretations"]), "signal_count_after": len(after["interpretations"])}
    return {**metadata, "baseline_reproduced": True, "record_count": len(expected_ids), "changes": changes}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New report file outside the benchmark inputs")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    try:
        batches = [_compare_batch(*batch) for loader in (_full_benchmark_batches, _targeted_trial_batches)
                   for batch in loader()]
        _save_json(output, {
            "mode": "offline_validation_and_scope_repair_trial", "inference_requests": 0,
            "baseline_record_count": sum(batch["record_count"] for batch in batches),
            "changed_record_count": sum(len(batch["changes"]) for batch in batches),
            "source_sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in map(Path, (
                __file__, feedback_v3.__file__, feedback_autonomy_review_v3.__file__,
                feedback_employer_context_repair_v3.__file__, feedback_intensity_repair_v3.__file__,
                feedback_enthusiasm_scope_v3.__file__,
            ))},
            "batches": batches,
        })
    except (OSError, ValueError) as error:
        print(f"Saved proposal replay could not complete. {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
