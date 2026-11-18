"""Revalidate archived v3 raw proposals locally without making model requests."""

import argparse
from collections.abc import Mapping
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import sys

from . import feedback_extraction_v3, feedback_rules_v3, feedback_taxonomy, feedback_v3
from .feedback_evaluation import _nonblank, _save_json
from .feedback_evaluation_v3 import (
    PASS_COUNT, SUITE_COUNTS, _live_configuration, _pass_stability, evaluate_v3, load_v3_suite,
)


def _unique_fields(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("archive JSON contains a duplicate field")
        result[name] = value
    return result


def _read_archive_json(path, expected_sha256=None):
    data = path.read_bytes()
    digest = sha256(data).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError(f"{path.name} does not match the recorded SHA-256")
    try:
        document = json.loads(data, object_pairs_hook=_unique_fields)
    except (ValueError, UnicodeError):
        raise ValueError(f"{path.name} must contain unambiguous JSON") from None
    if not isinstance(document, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return document, digest


def _archive_configuration(archive, expected):
    report, report_hash = _read_archive_json(archive / "live-report.json")
    recorded_config = report.get("configuration")
    if not isinstance(recorded_config, Mapping) or not _nonblank(recorded_config.get("capture_configuration_sha256")):
        raise ValueError("archived live report lacks the configuration digest")
    configuration, configuration_hash = _read_archive_json(
        archive / "configuration.json", recorded_config["capture_configuration_sha256"],
    )
    fixture_fields = (
        "benchmark_version", "suite_kind", "suite_version", "suite_sha256", "scenario_count",
        "hard_rules", "hard_rules_sha256",
    )
    if any(configuration.get(field) != expected[field] for field in fixture_fields):
        raise ValueError("archive configuration does not match the selected fixture or hard rules")
    inputs = configuration.get("inputs")
    if not isinstance(inputs, Mapping) or inputs.keys() != expected["inputs"].keys() or any(
        not isinstance(captured, Mapping)
        or not {"original_feedback_sha256", "job_context_sha256"} <= captured.keys()
        or any(expected["inputs"][case_id].get(field) != value for field, value in captured.items())
        for case_id, captured in inputs.items()
    ):
        raise ValueError("archive configuration does not match the selected case inputs")
    source = configuration.get("evaluation_source")
    if (
        not isinstance(source, Mapping) or source != report.get("evaluation_source") or source.get("mode") != "live"
        or source.get("passes") != PASS_COUNT or not _nonblank(source.get("requested_model"))
        or source.get("prompt_version") != feedback_extraction_v3.PROMPT_VERSION
    ):
        raise ValueError("archive must identify the original live model and compatible extraction prompt")
    return report, report_hash, configuration, configuration_hash


def _archived_passes(archive, suite, report, source):
    runs = report.get("runs")
    if not isinstance(runs, list) or len(runs) != PASS_COUNT:
        raise ValueError("archive must contain two live passes")
    case_ids = {case["case_id"] for case in suite.cases}
    captures = []
    for number, run in enumerate(runs, start=1):
        original_file, raw_file = f"pass-{number}.json", f"pass-{number}.proposals.json"
        if (
            not isinstance(run, Mapping) or run.get("pass_number") != number or not _nonblank(run.get("capture_id"))
            or run.get("capture_files") != {"predictions": original_file, "proposals": raw_file}
            or not all(_nonblank(run.get(field)) for field in ("predictions_sha256", "proposals_sha256"))
        ):
            raise ValueError(f"live pass {number} lacks capture metadata")
        original, original_hash = _read_archive_json(archive / original_file, run["predictions_sha256"])
        raw, raw_hash = _read_archive_json(archive / raw_file, run["proposals_sha256"])
        if original.keys() != case_ids or raw.keys() != case_ids:
            raise ValueError(f"live pass {number} case IDs must match the entire selected fixture")
        if any(
            not isinstance(result, Mapping) or (not result.get("evaluation_error") and (
                result.get("model") != source["requested_model"] or result.get("prompt_version") != source["prompt_version"]
            )) for result in original.values()
        ):
            raise ValueError(f"live pass {number} original predictions lack consistent model and prompt provenance")
        captures.append((raw, original, {
            "pass_number": number, "original_capture_id": run["capture_id"],
            "original_predictions_file": original_file, "original_predictions_sha256": original_hash,
            "raw_proposals_file": raw_file, "raw_proposals_sha256": raw_hash,
        }))
    if len({metadata["original_capture_id"] for _, _, metadata in captures}) != PASS_COUNT:
        raise ValueError("archived live passes must identify distinct captures")
    return captures


class _ArchivedProposalProvider:
    def __init__(self, model, proposal):
        self.model = model
        self._proposal = proposal

    def propose(self, decision, feedback, job_context, hard_rules):
        return self._proposal


def revalidate_pass(suite, proposals, source, *, recover_explicit_conditions=None):
    """Run only the deterministic v3 pipeline against a complete archived pass."""
    if not isinstance(proposals, Mapping) or proposals.keys() != {case["case_id"] for case in suite.cases}:
        raise ValueError("archived proposal IDs must match the entire selected fixture")
    options = {} if recover_explicit_conditions is None else {"recover_explicit_conditions": recover_explicit_conditions}
    predictions = {}
    for case in suite.cases:
        case_id = case["case_id"]
        proposal = proposals[case_id]
        if proposal is None:
            predictions[case_id] = {"evaluation_error": "MissingArchivedProposal"}
            continue
        provider = _ArchivedProposalProvider(source["requested_model"], proposal)
        try:
            prediction = feedback_v3.interpret_feedback_v3(
                case["decision"], case["original_feedback"], case["job_context"],
                provider=provider, hard_rules=suite.hard_rules, **options,
            )
        except Exception as error:
            prediction = {"evaluation_error": type(error).__name__}
        else:
            prediction["prompt_version"] = source["prompt_version"]
        predictions[case_id] = prediction
    return predictions


def _compare_with_original(original, repaired):
    case_ids = list(repaired)
    return {
        "identical_case_count": sum(original[case_id] == repaired[case_id] for case_id in case_ids),
        "changed_case_ids": [case_id for case_id in case_ids if original[case_id] != repaired[case_id]],
        "changed_fields": {
            field: [case_id for case_id in case_ids if original[case_id].get(field) != repaired[case_id].get(field)]
            for field in (
                "review_status", "hard_constraint_action", "interpretations", "validation_issues", "evaluation_error",
                "clarification_question", "profile_fact_candidate", "clauses", "eligibility_violation",
            )
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenarios", type=Path)
    parser.add_argument("--suite", choices=SUITE_COUNTS, default="gold")
    parser.add_argument("--archive", type=Path, required=True, help="Directory containing the archived live v3 run")
    parser.add_argument("--output", type=Path, required=True, help="New directory for offline predictions and report")
    args = parser.parse_args(argv)
    archive, output = args.archive.resolve(), args.output.resolve()
    if output == archive or archive in output.parents:
        parser.error("--output must be a new directory outside the archive")

    try:
        suite = load_v3_suite(args.scenarios, args.suite)
        configuration = _live_configuration(args, suite, datetime.now(UTC).isoformat(timespec="seconds"))
        original_report, report_hash, original_config, config_hash = _archive_configuration(archive, configuration)
        source = original_config["evaluation_source"]
        captures = _archived_passes(archive, suite, original_report, source)
        provenance = {
            "mode": "offline_raw_revalidation", "inference_requests": 0, "archive_directory": str(args.archive),
            "archive_configuration_sha256": config_hash, "archive_live_report_sha256": report_hash,
            "original_evaluation_source": source,
            "validator_sources_sha256": {
                Path(module.__file__).name: sha256(Path(module.__file__).read_bytes()).hexdigest()
                for module in (feedback_v3, feedback_rules_v3, feedback_taxonomy, feedback_extraction_v3)
            },
        }
        repaired_passes = [revalidate_pass(suite, raw, source) for raw, _, _ in captures]
        reports = [
            {**evaluate_v3(suite, repaired), **metadata, "comparison_with_live_validated": _compare_with_original(original, repaired)}
            for repaired, (_, original, metadata) in zip(repaired_passes, captures, strict=True)
        ]
        output.mkdir(parents=True)
        configuration_file = {**configuration, "evaluation_source": provenance}
        saved_configuration_hash = _save_json(output / "configuration.json", configuration_file)
        for repaired, report in zip(repaired_passes, reports, strict=True):
            name = f"pass-{report['pass_number']}.json"
            report["validated_predictions_file"] = name
            report["predictions_sha256"] = _save_json(output / name, repaired)
        complete = all(not report["execution_errors"] for report in reports)
        clean = complete and all(not report["validation_issue_count"] for report in reports)
        _save_json(output / "report.json", {
            "configuration": configuration_file, "evaluation_source": provenance,
            "output_configuration_sha256": saved_configuration_hash,
            "score_status": "provisional_automation", "quality_gates_passed": False,
            "two_complete_passes": complete, "repeated_pass_requirement_met": clean,
            "automated_stability": _pass_stability(suite, repaired_passes, reports), "runs": reports,
        })
    except (OSError, ValueError) as error:
        print(f"Offline revalidation could not complete. {error}", file=sys.stderr)
        return 2

    print(f"Revalidated {len(suite.cases) * len(reports)} archived cases. Saved {args.output / 'report.json'}.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
