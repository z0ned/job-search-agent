"""Test a source-only, quote-level review of feedback clause roles and scope."""

import argparse
from collections.abc import Mapping
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import sys
from time import perf_counter

from . import feedback, feedback_extraction_v3, feedback_rules_v3, feedback_taxonomy, feedback_v3
from .feedback import FeedbackOutputError, FeedbackProviderError, _enum, _model_input, _nonblank, _strict_object
from .feedback_evaluation import _save_json, load_suite
from .feedback_evaluation_v3 import _fingerprint, load_v3_suite
from .feedback_extraction_schema_trial_v3 import _present_text
from .feedback_extraction_trial_v3 import KNOWN_FIXTURES, _arm_report
from .feedback_extraction_v3 import CLAUSE_ROLES, OpenAIFeedbackProviderV3, _SIGNAL_SCHEMA
from .feedback_replay_v3 import _ArchivedProposalProvider, _read_archive_json
from .feedback_separate_extraction_trial_v3 import MODEL, PASSES, TEMPERATURE
from .feedback_v3 import _span, interpret_feedback_v3


DEFAULT_ARCHIVE = Path("benchmarks/feedback/live_v3_reaction_accounting_trial")
DEFAULT_NOVEL = Path("benchmarks/feedback/focused_context_trial_cases_v3.json")
DEFAULT_INSTRUCTIONS = Path("benchmarks/feedback/focused_context_trial_v3.txt")
NOVEL_IDS = ("FC3-001", "FC3-002", "FC3-003", "FC3-004")
KNOWN_ROLES = {"FI-041": ("preference", "preference"), "FH3-002": ("preference", "rule_reconsideration")}
ARM = "focused"
RESPONSE_SCHEMA_NAME = "feedback_focused_context_v3"
_SIGNAL_PROPERTIES = {key: value for key, value in _SIGNAL_SCHEMA["properties"].items() if key != "clause_index"}
_FOCUS_SCHEMA = _strict_object({
    "role": _enum(*CLAUSE_ROLES),
    "detail": {"type": ["string", "null"]},
    "signal": {"anyOf": [_strict_object(_SIGNAL_PROPERTIES), {"type": "null"}]},
})


def _checked_quotes(case):
    source = case["original_feedback"]
    revision = sha256(source.encode()).hexdigest()
    rows = case.get("focus_quotes")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{case['case_id']} requires a nonempty focus_quotes array")
    last_end = 0
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {"quote", "expected_roles"}:
            raise ValueError(f"{case['case_id']} has an invalid focus row")
        roles = row["expected_roles"]
        if (not isinstance(roles, list) or not roles or any(role not in CLAUSE_ROLES for role in roles)
                or len(set(roles)) != len(roles)):
            raise ValueError(f"{case['case_id']} has an invalid expected role set")
        span = _span(source, row["quote"], "context", revision)
        if span["start"] < last_end or any(char.isalnum() for char in source[last_end:span["start"]]):
            raise ValueError(f"{case['case_id']} focus quotes must cover the source in order without overlap")
        last_end = span["end"]
    if any(char.isalnum() for char in source[last_end:]):
        raise ValueError(f"{case['case_id']} focus quotes must cover the source in order without overlap")


def _known_focus(archive, cases, rules, fixtures):
    report, report_hash = _read_archive_json(archive / "report.json")
    config, config_hash = _read_archive_json(archive / "configuration.json", report["configuration_sha256"])
    if (config.get("mode") != "classifier_reaction_accounting"
            or config.get("model") != MODEL or config.get("temperature") != TEMPERATURE
            or report.get("request_errors") != 0 or report.get("requests_completed") != config.get("expected_requests")
            or any(config["fixtures"][kind] != fixtures[kind] for kind in ("gold", "holdout"))):
        raise ValueError("the source archive differs from the pinned accounting trial")
    if [entry["pass_number"] for entry in report["passes"]] != list(PASSES):
        raise ValueError("the accounting archive lacks two completed passes")
    source_inputs = {case["case_id"]: _model_input(case["decision"], case["original_feedback"], case["job_context"], rules)
                     for case in cases}
    if any(config["case_input_sha256"][case_id] != _fingerprint(value) for case_id, value in source_inputs.items()):
        raise ValueError("the selected cases differ from their archived source inputs")
    saved_inventories = []
    inventory_hashes = {}
    for entry in report["passes"]:
        number = entry["pass_number"]
        directory = f"pass-{number}"
        filename = "accounting.inventory.json"
        if entry["directory"] != directory or entry["inventory_file"] != filename:
            raise ValueError(f"unexpected pass {number} accounting inventory path")
        inventory, inventory_hash = _read_archive_json(archive / directory / filename, entry["inventory_sha256"])
        inventory_hashes[directory] = inventory_hash
        saved_inventories.append({case_id: inventory[case_id] for case_id in KNOWN_ROLES})
    first, second = saved_inventories
    if first != second:
        raise ValueError("the selected saved quote inventories differ between passes")
    selected = {}
    for case in cases:
        case_id = case["case_id"]
        expected = KNOWN_ROLES[case_id]
        rows = first[case_id]
        if len(rows) != len(expected):
            raise ValueError(f"unexpected number of saved quotes for {case_id}")
        source = case["original_feedback"]
        revision = sha256(source.encode()).hexdigest()
        selected[case_id] = []
        for row, role in zip(rows, expected, strict=True):
            anchor = _span(source, row["quote"], role, revision)
            if (anchor["start"], anchor["end"]) != (row["start"], row["end"]):
                raise ValueError(f"saved quote offsets do not match the source for {case_id}")
            selected[case_id].append({"quote": row["quote"], "expected_roles": [role]})
    return selected, {"file": str(archive), "report_sha256": report_hash, "configuration_sha256": config_hash,
                      "inventory_sha256": inventory_hashes}


def _load_cases(novel_path, archive_path):
    paths = {kind: KNOWN_FIXTURES[kind] for kind in ("gold", "holdout")}
    suites = {kind: load_v3_suite(path, kind) for kind, path in paths.items()}
    paths["novel"] = novel_path
    suites["novel"] = load_suite(novel_path, expected_count=len(NOVEL_IDS))
    rules = suites["gold"].hard_rules
    if any(suite.hard_rules != rules for suite in suites.values()):
        raise ValueError("all focused cases must share the approved hard rules")
    fixtures = {kind: {"file": str(paths[kind]), "version": suite.version, "sha256": suite.sha256}
                for kind, suite in suites.items()}
    by_id = {case["case_id"]: case for kind in ("gold", "holdout") for case in suites[kind].cases}
    fresh = {case["case_id"]: case for case in suites["novel"].cases}
    if fresh.keys() != set(NOVEL_IDS) or not set(KNOWN_ROLES) <= by_id.keys():
        raise ValueError("case IDs differ from the selected known and fresh cases")
    known = [by_id[case_id] for case_id in KNOWN_ROLES]
    selected, archive_source = _known_focus(archive_path, known, rules, fixtures)
    fixtures["accounting_archive"] = archive_source
    cases = [{**case, "focus_quotes": selected[case["case_id"]]} for case in known]
    cases.extend(fresh[case_id] for case_id in NOVEL_IDS)
    for case in cases:
        _checked_quotes(case)
    return cases, rules, fixtures


def _planned_requests(cases):
    return [{"pass_number": number, "case_id": case["case_id"], "focus_index": index}
            for number in PASSES for case in cases for index in range(len(case["focus_quotes"]))]


def _checked_response(response):
    if not isinstance(response, Mapping) or set(response) != {"role", "detail", "signal"}:
        raise FeedbackOutputError("Focus output has unexpected fields.")
    role, detail, signal = (response[key] for key in ("role", "detail", "signal"))
    if role not in CLAUSE_ROLES or (detail is not None and not _nonblank(detail)):
        raise FeedbackOutputError("Focus output has an invalid role or detail.")
    if role == "preference":
        if not isinstance(signal, Mapping) or set(signal) != set(_SIGNAL_PROPERTIES):
            raise FeedbackOutputError("A focused preference requires one complete standard signal.")
    elif signal is not None:
        raise FeedbackOutputError("A non-preference focus cannot emit a signal.")


def _call_focus(provider, original, focus, instructions, request, trace):
    model_input = {**original, "focus_quote": focus["quote"]}
    metadata = {
        **request, "request_number": len(trace) + 1, "input_sha256": _fingerprint(model_input),
        "origin_input_sha256": _fingerprint(original), "instructions_sha256": sha256(instructions.encode()).hexdigest(),
        "response_schema_sha256": _fingerprint(_FOCUS_SCHEMA),
    }
    trace.append(metadata)
    record = {**focus, "response": None}
    started = perf_counter()
    try:
        record["response"] = provider._request_proposal(
            model_input, instructions=instructions, schema_name=RESPONSE_SCHEMA_NAME, schema=_FOCUS_SCHEMA,
        )
    except FeedbackProviderError as error:
        metadata.update(status="error", error_type=type(error).__name__)
        record["issue"] = type(error).__name__
    else:
        metadata.update(status="completed", response_sha256=_fingerprint(record["response"]))
        try:
            _checked_response(record["response"])
        except FeedbackOutputError as error:
            record["issue"] = str(error)
    finally:
        metadata["elapsed_seconds"] = round(perf_counter() - started, 3)
    return record


def _run_case(case, rules, provider, instructions, number, trace):
    case_id = case["case_id"]
    original = _model_input(case["decision"], case["original_feedback"], case["job_context"], rules)
    records = [_call_focus(provider, original, focus, instructions,
                           {"pass_number": number, "case_id": case_id, "focus_index": index}, trace)
               for index, focus in enumerate(case["focus_quotes"])]
    if any("issue" in record for record in records):
        return records, None, {"evaluation_error": "InvalidFocusResult"}
    clauses, signals = [], []
    for index, record in enumerate(records):
        answer = record["response"]
        clauses.append({"role": answer["role"], "quote": record["quote"], "detail": answer["detail"]})
        if answer["signal"] is not None:
            signals.append({"clause_index": index, **answer["signal"]})
    proposal = {"clauses": clauses, "signals": signals}
    try:
        prediction = interpret_feedback_v3(
            case["decision"], case["original_feedback"], case["job_context"],
            provider=_ArchivedProposalProvider(provider.model, proposal), hard_rules=rules,
        )
    except FeedbackProviderError as error:
        prediction = {"evaluation_error": type(error).__name__}
    return records, proposal, prediction


def _capture_pass(output, number, cases, rules, provider, instructions, trace):
    responses, proposals, predictions = {}, {}, {}
    for case in cases:
        case_id = case["case_id"]
        responses[case_id], proposals[case_id], predictions[case_id] = _run_case(
            case, rules, provider, instructions, number, trace,
        )
        print(f"Captured focused pass {number} {case_id}.", file=sys.stderr)
    directory = output / f"pass-{number}"
    directory.mkdir()
    responses_file = "focused.responses.json"
    return {
        "pass_number": number, "directory": directory.name,
        "responses_file": responses_file, "responses_sha256": _save_json(directory / responses_file, responses),
        "arms": {ARM: _arm_report(directory, ARM, cases, proposals, predictions)},
        "focus_result_issue_count": sum("issue" in row for rows in responses.values() for row in rows),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--novel", type=Path, default=DEFAULT_NOVEL)
    parser.add_argument("--instructions", type=Path, default=DEFAULT_INSTRUCTIONS)
    parser.add_argument("--output", required=True, type=Path, help="New directory for the two-pass capture")
    args = parser.parse_args(argv)
    try:
        cases, rules, fixtures = _load_cases(args.novel, args.archive)
        instructions, instructions_hash = _present_text(args.instructions, "focused context instructions")
        provider = OpenAIFeedbackProviderV3(MODEL, temperature=TEMPERATURE)
        planned = _planned_requests(cases)
        source_modules = (feedback, feedback_extraction_v3, feedback_rules_v3, feedback_taxonomy, feedback_v3)
        args.output.mkdir(parents=True)
        configuration_hash = _save_json(args.output / "configuration.json", {
            "mode": "focused_context_trial", "model": MODEL, "temperature": TEMPERATURE,
            "validator_prompt_version_field": feedback_extraction_v3.PROMPT_VERSION,
            "recover_explicit_conditions": False, "started_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "fixtures": fixtures, "expected_requests": len(planned), "planned_requests": planned,
            "case_input_sha256": {case["case_id"]: _fingerprint(_model_input(
                case["decision"], case["original_feedback"], case["job_context"], rules,
            )) for case in cases},
            "focus_quotes_sha256": {case["case_id"]: _fingerprint(case["focus_quotes"]) for case in cases},
            "hard_rules_sha256": _fingerprint(rules), "instructions_file": str(args.instructions),
            "instructions_sha256": instructions_hash, "response_schema_name": RESPONSE_SCHEMA_NAME,
            "response_schema_sha256": _fingerprint(_FOCUS_SCHEMA),
            "source_sha256": {path.name: sha256(path.read_bytes()).hexdigest()
                              for path in (Path(__file__), *(Path(module.__file__) for module in source_modules))},
        })
        trace = []
        passes = [_capture_pass(args.output, number, cases, rules, provider, instructions, trace) for number in PASSES]
        request_errors = sum(entry["status"] == "error" for entry in trace)
        _save_json(args.output / "report.json", {
            "score_status": "automated_diagnostics_only", "configuration_sha256": configuration_hash,
            "request_trace_file": "request-trace.json",
            "request_trace_sha256": _save_json(args.output / "request-trace.json", trace),
            "requests_attempted": len(trace), "requests_completed": len(trace) - request_errors,
            "request_errors": request_errors, "passes": passes,
        })
    except (OSError, ValueError, KeyError, TypeError, FeedbackProviderError) as error:
        print(f"Focused context trial could not complete. {error}", file=sys.stderr)
        return 2
    case_errors = any(entry["arms"][ARM]["execution_errors"] for entry in passes)
    return int(bool(case_errors or request_errors or len(trace) != len(planned)))


if __name__ == "__main__":
    sys.exit(main())
