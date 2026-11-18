"""Revalidate both archived extraction-trial arms without any model requests."""

import argparse
from collections.abc import Mapping
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import sys
from types import SimpleNamespace

from . import feedback_conditions_v3, feedback_evaluation_v3, feedback_evidence_checks_v3, feedback_replay_v3
from .feedback_evaluation import GoldSuite, _nonblank, _save_json
from .feedback_evaluation_v3 import _fingerprint, evaluate_v3
from .feedback_extraction_trial_v3 import ARMS, _configuration, _load_trial, _request_order
from .feedback_replay_v3 import _compare_with_original, _read_archive_json, revalidate_pass


DEFAULT_NOVEL = Path("benchmarks/feedback/extraction_trial_v3_novel.json")
DEFAULT_CANDIDATE = Path("benchmarks/feedback/extraction_trial_v3_candidate.txt")
REPAIR_SOURCE = "feedback_v3.py"


def _read_trial(archive, novel, candidate):
    report, report_hash = _read_archive_json(archive / "report.json")
    configuration_hash = report.get("configuration_sha256")
    if not _nonblank(configuration_hash):
        raise ValueError("trial report lacks the original configuration SHA-256")
    archived, _ = _read_archive_json(archive / "configuration.json", configuration_hash)
    model, temperature = archived.get("model"), archived.get("temperature")
    if not _nonblank(model) or type(temperature) not in (int, float) or not 0 <= temperature <= 2:
        raise ValueError("trial configuration lacks its model or temperature")

    cases, rules, fixture_sources, pairs = _load_trial(novel)
    schedule = _request_order(cases)
    expected = _configuration(
        SimpleNamespace(temperature=temperature, candidate=candidate),
        cases, rules, fixture_sources, pairs, candidate.read_bytes(), model, schedule,
    )
    fields = (
        "trial_version", "validator_prompt_version_field", "response_schema_name", "response_schema_sha256",
        "hard_rules_sha256", "case_input_sha256", "paired_cases", "request_order",
    )
    if any(archived.get(field) != expected[field] for field in fields) or (
        _fingerprint(archived.get("hard_rules")) != expected["hard_rules_sha256"]
    ):
        raise ValueError("archived trial configuration does not match the case inputs, hard rules, or response schema")
    fixtures, arms = archived.get("fixtures"), archived.get("arms")
    if not isinstance(fixtures, Mapping) or fixtures.keys() != fixture_sources.keys() or any(
        not isinstance(fixtures[kind], Mapping)
        or any(fixtures[kind].get(field) != source[field] for field in ("version", "sha256"))
        for kind, source in fixture_sources.items()
    ):
        raise ValueError("archived trial fixture versions or hashes differ from the selected files")
    if not isinstance(arms, Mapping) or set(arms) != set(ARMS) or any(
        not isinstance(arms[arm], Mapping)
        or arms[arm].get("instruction_sha256") != expected["arms"][arm]["instruction_sha256"]
        for arm in ARMS
    ):
        raise ValueError("archived trial instruction hashes do not match the baseline and candidate prompts")
    source = archived.get("source_sha256")
    if not isinstance(source, Mapping) or source.keys() != expected["source_sha256"].keys() or any(
        not _nonblank(digest) or (name != REPAIR_SOURCE and digest != expected["source_sha256"][name])
        for name, digest in source.items()
    ):
        raise ValueError("archived trial source differs outside the permitted validator repair")

    requests = report.get("request_log")
    if (
        not isinstance(requests, list) or len(requests) != len(schedule) or report.get("requests_completed") != len(schedule)
        or any(not isinstance(request, Mapping) or any(request.get(key) != value for key, value in entry.items())
               for request, entry in zip(requests, schedule, strict=True))
    ):
        raise ValueError("archived report does not capture the complete expected request order")
    provenance = {
        "mode": "offline_extraction_trial_revalidation", "inference_requests": 0,
        "archive_configuration_sha256": configuration_hash, "archive_report_sha256": report_hash,
        "model": model, "temperature": temperature, "arms": arms,
        "validator_prompt_version_field": archived["validator_prompt_version_field"],
        "response_schema_name": archived["response_schema_name"],
        "response_schema_sha256": archived["response_schema_sha256"],
        "archived_source_sha256": source,
        "replay_source_sha256": {
            **expected["source_sha256"],
            **{Path(path).name: sha256(Path(path).read_bytes()).hexdigest()
               for path in (__file__, feedback_conditions_v3.__file__, feedback_evidence_checks_v3.__file__, feedback_evaluation_v3.__file__,
                            feedback_replay_v3.__file__)},
        },
        "fixtures": fixtures, "paired_cases": pairs, "case_input_sha256": expected["case_input_sha256"],
        "hard_rules_sha256": expected["hard_rules_sha256"],
    }
    suite = GoldSuite(archived["trial_version"], _fingerprint({kind: data["sha256"] for kind, data in fixtures.items()}),
                      cases, rules)
    return suite, report, provenance


def _read_arms(archive, report, case_ids, source):
    report_arms = report.get("arms")
    if not isinstance(report_arms, Mapping) or set(report_arms) != set(ARMS):
        raise ValueError("archived report must contain both extraction-trial arms")
    captures = {}
    for arm in ARMS:
        raw_file, validated_file = f"{arm}.proposals.json", f"{arm}.json"
        report_arm = report_arms[arm]
        if (
            not isinstance(report_arm, Mapping) or report_arm.get("raw_proposals_file") != raw_file
            or report_arm.get("validated_file") != validated_file
            or not all(_nonblank(report_arm.get(field)) for field in ("raw_proposals_sha256", "validated_sha256"))
        ):
            raise ValueError(f"{arm} archive lacks its captured file metadata")
        raw, raw_hash = _read_archive_json(archive / raw_file, report_arm["raw_proposals_sha256"])
        original, original_hash = _read_archive_json(archive / validated_file, report_arm["validated_sha256"])
        if raw.keys() != case_ids or original.keys() != case_ids:
            raise ValueError(f"{arm} archive must match the complete set of trial case IDs")
        if any(
            not isinstance(result, Mapping) or (not result.get("evaluation_error") and (
                result.get("model") != source["requested_model"] or result.get("prompt_version") != source["prompt_version"]
            )) for result in original.values()
        ):
            raise ValueError(f"{arm} archived predictions lack matching model or prompt provenance")
        captures[arm] = raw, original, {"raw_proposals_sha256": raw_hash, "archived_validated_sha256": original_hash}
    return captures


def _compare_arm(original, replay):
    comparison = _compare_with_original(original, replay)
    for field in ("evidence_findings", "condition_recoveries"):
        comparison["changed_fields"][field] = [
            case_id for case_id in replay if original[case_id].get(field, []) != replay[case_id].get(field, [])
        ]
    return comparison


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True, help="Archived live extraction-trial directory")
    parser.add_argument("--novel", type=Path, default=DEFAULT_NOVEL)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--output", type=Path, required=True, help="New directory for revalidated arms and report")
    parser.add_argument("--recover-explicit-conditions", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args(argv)
    archive, output = args.archive.resolve(), args.output.resolve()
    if output == archive or archive in output.parents:
        parser.error("--output must be a new directory outside the archive")

    try:
        suite, report, provenance = _read_trial(archive, args.novel, args.candidate)
        source = {"requested_model": provenance["model"], "prompt_version": provenance["validator_prompt_version_field"]}
        captures = _read_arms(archive, report, {case["case_id"] for case in suite.cases}, source)
        revalidated = {
            arm: revalidate_pass(suite, raw, source, recover_explicit_conditions=args.recover_explicit_conditions)
            for arm, (raw, _, _) in captures.items()
        }
        reports = {
            arm: {**evaluate_v3(suite, revalidated[arm]), **metadata,
                  "comparison_with_live_validated": _compare_arm(original, revalidated[arm])}
            for arm, (_, original, metadata) in captures.items()
        }
        output.mkdir(parents=True)
        configuration_hash = _save_json(output / "configuration.json", {
            **provenance, "archive_directory": str(args.archive),
            "started_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "recover_explicit_conditions": args.recover_explicit_conditions,
        })
        for arm, arm_report in reports.items():
            name = f"{arm}.json"
            arm_report["validated_file"] = name
            arm_report["validated_sha256"] = _save_json(output / name, revalidated[arm])
            arm_report["byte_exact_archive_match"] = arm_report["validated_sha256"] == arm_report["archived_validated_sha256"]
        byte_exact = all(arm["byte_exact_archive_match"] for arm in reports.values())
        errored = any(arm["execution_errors"] for arm in reports.values())
        _save_json(output / "report.json", {
            "configuration_sha256": configuration_hash, "inference_requests": 0,
            "revalidated_cases": len(suite.cases) * len(reports), "recover_explicit_conditions": args.recover_explicit_conditions,
            "byte_exact_archive_match": byte_exact, "score_status": "automated_diagnostics_only", "arms": reports,
        })
    except (OSError, ValueError) as error:
        print(f"Offline extraction-trial replay could not complete. {error}", file=sys.stderr)
        return 2

    print(f"Revalidated {len(suite.cases) * len(reports)} archived proposals. Saved {args.output / 'report.json'}.", file=sys.stderr)
    return int(errored or (not args.recover_explicit_conditions and not byte_exact))


if __name__ == "__main__":
    sys.exit(main())
