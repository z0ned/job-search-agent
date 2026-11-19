"""Replay the saved split classifier and test explicit reaction accounting."""

import argparse
from collections.abc import Mapping
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter

from . import feedback, feedback_extraction_v3, feedback_reaction_accounting_v3, feedback_rules_v3, feedback_taxonomy, feedback_v3
from . import feedback_separate_extraction_trial_v3 as separate
from .feedback import FeedbackOutputError, FeedbackProviderError, _enum, _model_input, _strict_object
from .feedback_evaluation import _RecordingProvider, _save_json
from .feedback_evaluation_v3 import _fingerprint
from .feedback_extraction_schema_trial_v3 import _present_text
from .feedback_extraction_trial_v3 import _arm_report
from .feedback_extraction_v3 import OpenAIFeedbackProviderV3, _INSTRUCTIONS, _PROPOSAL_SCHEMA
from .feedback_reaction_accounting_v3 import audit_reactions, identify_reactions
from .feedback_replay_v3 import _read_archive_json
from .feedback_v3 import interpret_feedback_v3


DEFAULT_ARCHIVE = Path("benchmarks/feedback/live_v3_separate_extraction_trial")
DEFAULT_ACCOUNTING = Path("benchmarks/feedback/extraction_reaction_accounting_v3.txt")
_SCHEMA_NAME = "feedback_reaction_accounting_v3"
_ACCOUNTING_SCHEMA = _strict_object({
    **_PROPOSAL_SCHEMA["properties"],
    "reaction_dispositions": {"type": "array", "items": _strict_object({
        "reaction_id": {"type": "string"},
        "status": _enum("signal", "context", "needs_review"),
        "signal_index": {"type": ["integer", "null"]},
        "reason": {"type": ["string", "null"]},
    })},
})


def _digest(data):
    return sha256(data).hexdigest()


def _source_hashes(modules):
    return {path.name: _digest(path.read_bytes()) for path in (Path(module.__file__) for module in modules)}


_ARCHIVED_MODULES = (feedback, feedback_extraction_v3, feedback_rules_v3, feedback_taxonomy, feedback_v3, separate)


def _read_trace(archive, report):
    data = (archive / "request-trace.json").read_bytes()
    if _digest(data) != report["request_trace_sha256"]:
        raise ValueError("the archived request trace does not match its recorded fingerprint")
    trace = json.loads(data)
    if not isinstance(trace, list):
        raise ValueError("the archived request trace must be an array")
    return trace


def _verify_archive_configuration(config, report, inputs, fixtures, rules, handoff):
    previous_instructions = _INSTRUCTIONS + "\n\n" + handoff
    expected_config = {
        "trial_version": "3.0-targeted-separate-extraction",
        "model": separate.MODEL,
        "temperature": separate.TEMPERATURE,
        "validator_prompt_version_field": separate.PROMPT_VERSION,
        "recover_explicit_conditions": False,
        "fixtures": fixtures,
        "case_input_sha256": {case_id: _fingerprint(value) for case_id, value in inputs.items()},
        "hard_rules_sha256": _fingerprint(rules),
        "split_classifier_instructions_sha256": _digest(previous_instructions.encode()),
        "classifier_schema_name": separate._FINAL_NAME,
        "classifier_schema_sha256": _fingerprint(_PROPOSAL_SCHEMA),
        "source_sha256": _source_hashes(_ARCHIVED_MODULES),
    }
    if any(config.get(key) != expected for key, expected in expected_config.items()):
        raise ValueError("the archive does not match the current inputs, classifier, or validator")
    if (report.get("request_trace_file") != "request-trace.json"
            or report.get("request_errors") != 0 or report.get("unattempted_requests") != []
            or report.get("origin_input_mismatches") != []):
        raise ValueError("the archived trial must have completed without mismatched inputs")
    return previous_instructions


def _verified_archived_pass(archive, entry, expected_ids):
    number = entry["pass_number"]
    directory = archive / f"pass-{number}"
    if entry["directory"] != directory.name or entry["inventory_file"] != "split.inventory.json":
        raise ValueError(f"the archive has unexpected pass {number} filenames")
    split = entry["arms"]["split"]
    if split["raw_proposals_file"] != "split.proposals.json" or split["validated_file"] != "split.json":
        raise ValueError(f"the archive has unexpected pass {number} split classifier filenames")
    hashes = {
        "raw_proposals_sha256": split["raw_proposals_sha256"],
        "validated_sha256": split["validated_sha256"],
        "inventory_sha256": entry["inventory_sha256"],
    }
    raw, _ = _read_archive_json(directory / "split.proposals.json", hashes["raw_proposals_sha256"])
    predictions, _ = _read_archive_json(directory / "split.json", hashes["validated_sha256"])
    inventories, _ = _read_archive_json(directory / "split.inventory.json", hashes["inventory_sha256"])
    if any(set(values) != expected_ids for values in (raw, predictions, inventories)):
        raise ValueError(f"the archive has unexpected pass {number} case IDs")
    return {"raw": raw, "predictions": predictions, "inventories": inventories, "hashes": hashes}


def _check_classifier_trace(config, previous_input, case_id, archived, old_requests, number):
    inventory_request = old_requests[(number, case_id, "split", "inventory")]
    classifier_request = old_requests[(number, case_id, "split", "classifier")]
    expected = (
        (inventory_request, {
            "input_sha256": config["case_input_sha256"][case_id],
            "response_sha256": _fingerprint(archived["inventories"][case_id]["raw"]),
            "instructions_sha256": config["inventory_instructions_sha256"],
            "response_schema_sha256": config["inventory_schema_sha256"],
        }),
        (classifier_request, {
            "input_sha256": _fingerprint(previous_input),
            "response_sha256": _fingerprint(archived["raw"][case_id]),
            "instructions_sha256": config["split_classifier_instructions_sha256"],
            "response_schema_sha256": config["classifier_schema_sha256"],
        }),
    )
    if any(request.get(key) != value for request, fields in expected for key, value in fields.items()):
        raise ValueError(f"pass {number} {case_id} does not reproduce its archived classifier handoff")
    return classifier_request["input_sha256"]


def _load_archive(archive, cases, rules, fixtures, handoff):
    report, report_hash = _read_archive_json(archive / "report.json")
    config, config_hash = _read_archive_json(archive / "configuration.json", report["configuration_sha256"])
    inputs = {case["case_id"]: _model_input(case["decision"], case["original_feedback"], case["job_context"], rules)
              for case in cases}
    previous_instructions = _verify_archive_configuration(config, report, inputs, fixtures, rules, handoff)
    trace = _read_trace(archive, report)
    planned = [{**entry, "stage": stage} for entry in separate._case_order(cases)
               for stage in (("classifier",) if entry["arm"] == "baseline" else ("inventory", "classifier"))]
    if (config.get("planned_requests") != planned or len(planned) != config.get("expected_requests")
            or len(trace) != len(planned) or report.get("requests_attempted") != len(trace)
            or report.get("requests_completed") != len(trace)):
        raise ValueError("the archive does not have the full earlier two-pass trace")
    old_requests = {}
    for request_number, (row, entry) in enumerate(zip(trace, planned, strict=True), 1):
        if (not isinstance(row, Mapping) or row.get("request_number") != request_number
                or row.get("status") != "completed" or any(row.get(key) != value for key, value in entry.items())
                or row.get("origin_input_sha256") != config["case_input_sha256"][entry["case_id"]]):
            raise ValueError("the archived request trace differs from the pinned request plan")
        old_requests[(entry["pass_number"], entry["case_id"], entry["arm"], entry["stage"])] = row
    if [entry["pass_number"] for entry in report["passes"]] != list(separate.PASSES):
        raise ValueError("the archive lacks an independent two-pass capture")
    passes = {}
    for entry in report["passes"]:
        number = entry["pass_number"]
        archived = _verified_archived_pass(archive, entry, set(inputs))
        identified, classifier_hashes = {}, {}
        for case_id, original in inputs.items():
            old_inventory = archived["inventories"][case_id]
            rejections = []
            verified = separate._verified_inventory(old_inventory["raw"], original["original_feedback"], rejections)
            if verified != old_inventory["verified"] or rejections != old_inventory["rejections"] or rejections:
                raise ValueError(f"pass {number} {case_id} has inconsistent or rejected archived inventory")
            previous_input = {**original, "evidence_inventory": verified}
            classifier_hashes[case_id] = _check_classifier_trace(config, previous_input, case_id, archived, old_requests, number)
            identified[case_id] = identify_reactions(original["original_feedback"], verified)
        passes[number] = {**archived, "identified": identified, "classifier_hashes": classifier_hashes}
    return passes, previous_instructions, {
        "archive_configuration_sha256": config_hash,
        "archive_report_sha256": report_hash,
        "archive_request_trace_sha256": report["request_trace_sha256"],
        "archive_split_classifier_instructions_sha256": config["split_classifier_instructions_sha256"],
        "case_input_sha256": config["case_input_sha256"],
        "fixtures": fixtures,
    }


class _AccountingClassifier(OpenAIFeedbackProviderV3):
    def __init__(self, identity, inventory, instructions, previous_input_hash, trace):
        super().__init__(separate.MODEL, temperature=separate.TEMPERATURE)
        self.identity = identity
        self.inventory = inventory
        self.instructions = instructions
        self.previous_input_hash = previous_input_hash
        self.trace = trace
        self.response = None

    def propose(self, decision, feedback_text, context, hard_rules):
        original = _model_input(decision, feedback_text, context, hard_rules)
        model_input = {**original, "evidence_inventory": self.inventory}
        request = {
            **self.identity, "request_number": len(self.trace) + 1,
            "origin_input_sha256": _fingerprint(original), "input_sha256": _fingerprint(model_input),
            "archive_classifier_input_sha256": self.previous_input_hash,
            "instructions_sha256": _digest(self.instructions.encode()),
            "response_schema_sha256": _fingerprint(_ACCOUNTING_SCHEMA),
        }
        self.trace.append(request)
        started = perf_counter()
        try:
            self.response = self._request_proposal(
                model_input, instructions=self.instructions, schema_name=_SCHEMA_NAME, schema=_ACCOUNTING_SCHEMA,
            )
        except FeedbackProviderError as error:
            request.update(status="error", error_type=type(error).__name__)
            raise
        else:
            request.update(status="completed", response_sha256=_fingerprint(self.response))
        finally:
            request["elapsed_seconds"] = round(perf_counter() - started, 3)
        if not isinstance(self.response, Mapping) or set(self.response) != set(_ACCOUNTING_SCHEMA["properties"]):
            raise FeedbackOutputError("The accounting response has unexpected fields.")
        return {key: self.response[key] for key in _PROPOSAL_SCHEMA["properties"]}


def _capture_pass(output, number, cases, rules, archived, requests, instructions, trace):
    by_id = {case["case_id"]: case for case in cases}
    inventory = archived["identified"]
    if instructions is None:
        raw, predictions, responses = archived["raw"], archived["predictions"], None
    else:
        raw, predictions, responses = {}, {}, {}
        for identity in requests:
            case_id = identity["case_id"]
            case = by_id[case_id]
            provider = _AccountingClassifier(identity, inventory[case_id], instructions,
                                             archived["classifier_hashes"][case_id], trace)
            recorder = _RecordingProvider(provider)
            try:
                predictions[case_id] = interpret_feedback_v3(
                    case["decision"], case["original_feedback"], case["job_context"], provider=recorder, hard_rules=rules,
                )
            except FeedbackProviderError as error:
                predictions[case_id] = {"evaluation_error": type(error).__name__}
            finally:
                recorder.finish_case(case_id)
            raw[case_id] = recorder.proposals[case_id]
            responses[case_id] = provider.response
            print(f"Captured accounting pass {number} {case_id}.", file=sys.stderr)
    audits = {}
    for case_id, case in by_id.items():
        dispositions = None
        if responses is not None:
            response = responses[case_id]
            dispositions = response.get("reaction_dispositions") if isinstance(response, Mapping) else None
            if dispositions is None:
                dispositions = []
        audits[case_id] = audit_reactions(
            case["original_feedback"], inventory[case_id], raw[case_id], predictions[case_id], dispositions,
        )
    directory = output / f"pass-{number}"
    directory.mkdir()
    result = {
        "pass_number": number, "directory": directory.name,
        "arms": {"accounting": _arm_report(directory, "accounting", cases, raw, predictions)},
        "inventory_file": "accounting.inventory.json",
        "inventory_sha256": _save_json(directory / "accounting.inventory.json", inventory),
        "audit_file": "accounting.audit.json",
        "audit_sha256": _save_json(directory / "accounting.audit.json", audits),
        "archive_comparator": archived["hashes"],
    }
    if responses is not None:
        result.update(responses_file="accounting.responses.json",
                      responses_sha256=_save_json(directory / "accounting.responses.json", responses))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--accounting-instructions", type=Path, default=DEFAULT_ACCOUNTING)
    parser.add_argument("--output", type=Path, required=True, help="New directory for the accounting capture")
    parser.add_argument("--offline", action="store_true", help="Audit archived classifier outputs without model calls")
    args = parser.parse_args(argv)
    try:
        cases, rules, fixtures = separate._load_cases(separate.DEFAULT_NOVEL)
        handoff, _ = _present_text(separate.DEFAULT_HANDOFF, "archived classifier handoff")
        archived, previous_instructions, provenance = _load_archive(args.archive, cases, rules, fixtures, handoff)
        instructions = None
        requests = []
        treatment = {}
        if not args.offline:
            accounting, accounting_hash = _present_text(args.accounting_instructions, "accounting instructions")
            instructions = previous_instructions + "\n\n" + accounting
            requests = [{"pass_number": number, "case_id": case["case_id"], "arm": "accounting", "stage": "classifier"}
                        for number in separate.PASSES for case in cases]
            treatment = {
                "started_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "accounting_instruction_file": str(args.accounting_instructions),
                "accounting_instructions_sha256": accounting_hash,
                "classifier_instructions_sha256": _digest(instructions.encode()),
                "classifier_schema_name": _SCHEMA_NAME,
                "classifier_schema_sha256": _fingerprint(_ACCOUNTING_SCHEMA),
            }
        args.output.mkdir(parents=True)
        configuration_sha256 = _save_json(args.output / "configuration.json", {
            **provenance, **treatment,
            "mode": "offline_reaction_accounting_replay" if args.offline else "classifier_reaction_accounting",
            "model": separate.MODEL, "temperature": separate.TEMPERATURE,
            "validator_prompt_version_field": separate.PROMPT_VERSION,
            "recover_explicit_conditions": False, "expected_requests": len(requests), "planned_requests": requests,
            "source_sha256": {
                **_source_hashes((*_ARCHIVED_MODULES, feedback_reaction_accounting_v3)),
                Path(__file__).name: _digest(Path(__file__).read_bytes()),
            },
        })
        trace = []
        passes = [_capture_pass(args.output, number, cases, rules, archived[number],
                                [entry for entry in requests if entry["pass_number"] == number], instructions, trace)
                  for number in separate.PASSES]
        request_errors = sum(row["status"] == "error" for row in trace)
        _save_json(args.output / "report.json", {
            "score_status": "automated_diagnostics_only", "configuration_sha256": configuration_sha256,
            "request_trace_file": "request-trace.json",
            "request_trace_sha256": _save_json(args.output / "request-trace.json", trace),
            "requests_attempted": len(trace), "requests_completed": len(trace) - request_errors,
            "request_errors": request_errors, "passes": passes,
        })
    except (OSError, ValueError, KeyError, TypeError, FeedbackProviderError) as error:
        print(f"Reaction accounting trial could not complete. {error}", file=sys.stderr)
        return 2
    case_errors = any(entry["arms"]["accounting"]["execution_errors"] for entry in passes)
    return int(bool(case_errors or request_errors or len(trace) != len(requests)))


if __name__ == "__main__":
    sys.exit(main())
