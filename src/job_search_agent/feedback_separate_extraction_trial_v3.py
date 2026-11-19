"""Compare one-call feedback classification with a separate evidence inventory."""

import argparse
from collections.abc import Mapping
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import sys
from time import perf_counter

from . import feedback, feedback_extraction_v3, feedback_rules_v3, feedback_taxonomy, feedback_v3
from .feedback import FeedbackOutputError, FeedbackProviderError, _enum, _model_input, _strict_object
from .feedback_evaluation import _RecordingProvider, _save_json, load_suite
from .feedback_evaluation_v3 import _fingerprint, load_v3_suite
from .feedback_extraction_schema_trial_v3 import _present_text
from .feedback_extraction_trial_v3 import KNOWN_FIXTURES, _arm_report
from .feedback_extraction_v3 import CLAUSE_ROLES, PROMPT_VERSION, OpenAIFeedbackProviderV3, _INSTRUCTIONS, _PROPOSAL_SCHEMA
from .feedback_v3 import _span, interpret_feedback_v3


DEFAULT_NOVEL = Path("benchmarks/feedback/extraction_separate_trial_cases_v3.json")
DEFAULT_INVENTORY = Path("benchmarks/feedback/extraction_separate_trial_v3_inventory.txt")
DEFAULT_HANDOFF = Path("benchmarks/feedback/extraction_separate_trial_v3_handoff.txt")
KNOWN_CASES = (("gold", "FI-041"), ("holdout", "FH3-011"), ("holdout", "FH3-007"), ("holdout", "FH3-002"))
NOVEL_IDS = tuple(f"FS3-{number:03d}" for number in range(1, 5))
ARMS = ("baseline", "split")
PASSES = (1, 2)
MODEL = "gpt-5.4-2026-03-05"
TEMPERATURE = 0.1
_INVENTORY_NAME = "feedback_evidence_inventory_v3"
_FINAL_NAME = "feedback_extraction_v3"
_INVENTORY_SCHEMA = _strict_object({
    "statements": {"type": "array", "items": _strict_object({
        "quote": {"type": "string"}, "role": _enum(*CLAUSE_ROLES),
    })},
})


def _load_cases(novel_path):
    paths = {kind: KNOWN_FIXTURES[kind] for kind in ("gold", "holdout")}
    sources = {kind: load_v3_suite(path, kind) for kind, path in paths.items()}
    paths["novel"] = novel_path
    sources["novel"] = load_suite(novel_path, expected_count=len(NOVEL_IDS))
    rules = sources["gold"].hard_rules
    if any(suite.hard_rules != rules for suite in sources.values()):
        raise ValueError("all trial fixtures must share the approved hard rules")
    fixtures = {kind: {"file": str(paths[kind]), "version": suite.version, "sha256": suite.sha256}
                for kind, suite in sources.items()}
    by_id = {kind: {case["case_id"]: case for case in suite.cases} for kind, suite in sources.items()}
    if by_id["novel"].keys() != set(NOVEL_IDS) or any(case_id not in by_id[kind] for kind, case_id in KNOWN_CASES):
        raise ValueError("the fixtures must contain the four selected known and four fresh trial cases")
    case_keys = (*KNOWN_CASES, *(("novel", case_id) for case_id in NOVEL_IDS))
    return [by_id[kind][case_id] for kind, case_id in case_keys], rules, fixtures


def _case_order(cases):
    return [
        {"pass_number": number, "case_id": case["case_id"], "arm": arm}
        for number in PASSES
        for index, case in enumerate(cases)
        for arm in (ARMS if (index + number) % 2 else ARMS[::-1])
    ]


def _verified_inventory(raw, feedback_text, rejections):
    if not isinstance(raw, Mapping) or set(raw) != {"statements"} or not isinstance(raw["statements"], list):
        rejections.append({"index": None, "reason": "invalid_inventory"})
        raise FeedbackOutputError("Invalid inventory response.")
    verified = []
    used = set()
    revision = sha256(feedback_text.encode()).hexdigest()
    for index, item in enumerate(raw["statements"]):
        if not isinstance(item, Mapping) or set(item) != {"quote", "role"} or item["role"] not in CLAUSE_ROLES:
            rejections.append({"index": index, "reason": "invalid_statement"})
            continue
        try:
            span = _span(feedback_text, item["quote"], item["role"], revision)
        except FeedbackOutputError:
            rejections.append({"index": index, "reason": "quote_not_unique_verbatim"})
            continue
        offsets = span["start"], span["end"]
        if offsets in used:
            rejections.append({"index": index, "reason": "duplicate_span"})
            continue
        used.add(offsets)
        verified.append({key: span[key] for key in ("quote", "role", "start", "end")})
    return verified


class _TrialProvider(OpenAIFeedbackProviderV3):
    def __init__(self, identity, trace, inventory_instructions, handoff_instructions):
        super().__init__(MODEL, temperature=TEMPERATURE)
        self.identity = identity
        self.trace = trace
        self.inventory_instructions = inventory_instructions
        self.handoff_instructions = handoff_instructions
        self.inventory = {"raw": None, "verified": [], "rejections": []}
        self.original_input_sha256 = None

    def _request_proposal(self, model_input, *, instructions, schema_name, schema):
        request = {
            **self.identity, "request_number": len(self.trace) + 1,
            "stage": "inventory" if schema_name == _INVENTORY_NAME else "classifier",
            "input_sha256": _fingerprint(model_input), "origin_input_sha256": self.original_input_sha256,
            "instructions_sha256": sha256(instructions.encode()).hexdigest(),
            "response_schema_sha256": _fingerprint(schema),
        }
        self.trace.append(request)
        started = perf_counter()
        try:
            response = super()._request_proposal(model_input, instructions=instructions, schema_name=schema_name, schema=schema)
        except FeedbackProviderError as error:
            request.update(status="error", error_type=type(error).__name__)
            raise
        else:
            request.update(status="completed", response_sha256=_fingerprint(response))
            return response
        finally:
            request["elapsed_seconds"] = round(perf_counter() - started, 3)

    def propose(self, decision, feedback_text, job_context, hard_rules):
        original = _model_input(decision, feedback_text, job_context, hard_rules)
        self.original_input_sha256 = _fingerprint(original)
        if self.identity["arm"] == "baseline":
            return super().propose(decision, feedback_text, job_context, hard_rules)
        raw = self._request_proposal(original, instructions=self.inventory_instructions,
                                     schema_name=_INVENTORY_NAME, schema=_INVENTORY_SCHEMA)
        self.inventory["raw"] = raw
        verified = _verified_inventory(raw, feedback_text, self.inventory["rejections"])
        self.inventory["verified"] = verified
        return self._request_proposal(
            {**original, "evidence_inventory": verified},
            instructions=_INSTRUCTIONS + "\n\n" + self.handoff_instructions,
            schema_name=_FINAL_NAME, schema=_PROPOSAL_SCHEMA,
        )


def _span_relation(inventory, output):
    start, end = inventory["start"], inventory["end"]
    left, right = output["start"], output["end"]
    if (start, end) == (left, right):
        return "exact"
    if left <= start < end <= right:
        return "output_contains_inventory"
    if start <= left < right <= end:
        return "inventory_contains_output"
    if start < right and left < end:
        return "partial_overlap"
    return None


def _signal_links(spans_by_index, verified):
    return {
        str(index): [{"inventory_index": inventory_index, "relationship": relation}
                     for inventory_index, item in enumerate(verified)
                     if span is not None and (relation := _span_relation(item, span)) is not None]
        for index, span in spans_by_index.items()
    }


def _inventory_diagnostics(feedback_text, verified, raw, validated):
    raw = raw if isinstance(raw, Mapping) else {}
    raw_clauses = raw.get("clauses", [])
    raw_signals = raw.get("signals", [])
    revision = sha256(feedback_text.encode()).hexdigest()
    raw_spans = {}
    if isinstance(raw_clauses, list):
        for index, clause in enumerate(raw_clauses):
            if isinstance(clause, Mapping):
                try:
                    raw_spans[index] = _span(feedback_text, clause.get("quote"), clause.get("role"), revision)
                except FeedbackOutputError:
                    pass
    raw_signal_spans = {}
    if isinstance(raw_signals, list):
        for index, signal in enumerate(raw_signals):
            clause_index = signal.get("clause_index") if isinstance(signal, Mapping) else None
            raw_signal_spans[index] = raw_spans.get(clause_index) if type(clause_index) is int else None
    validated_spans = {index: signal["evidence"][0] for index, signal in enumerate(validated.get("interpretations", []))}
    raw_links = _signal_links(raw_signal_spans, verified)
    validated_links = _signal_links(validated_spans, verified)
    return {
        "index_base": 0,
        "raw_clause_links": _signal_links(raw_spans, verified),
        "raw_signal_links": raw_links,
        "validated_signal_links": validated_links,
        "inventory_preferences_without_raw_signal": _unlinked_inventory_preferences(verified, raw_links),
        "inventory_preferences_without_validated_signal": _unlinked_inventory_preferences(verified, validated_links),
        "raw_signals_without_inventory_preference": _unlinked_signals(verified, raw_links),
        "validated_signals_without_inventory_preference": _unlinked_signals(verified, validated_links),
    }


def _unlinked_inventory_preferences(verified, links):
    linked = {item["inventory_index"] for matches in links.values() for item in matches}
    return [index for index, item in enumerate(verified) if item["role"] == "preference" and index not in linked]


def _unlinked_signals(verified, links):
    return [int(index) for index, matches in links.items()
            if not any(verified[match["inventory_index"]]["role"] == "preference" for match in matches)]


def _capture_pass(output, number, order, cases, rules, trace, inventory_instructions, handoff):
    by_id = {case["case_id"]: case for case in cases}
    raw, validated, inventory = {arm: {} for arm in ARMS}, {arm: {} for arm in ARMS}, {}
    for entry in order:
        arm, case_id = entry["arm"], entry["case_id"]
        case = by_id[case_id]
        provider = _TrialProvider(entry, trace, inventory_instructions, handoff)
        recorder = _RecordingProvider(provider)
        try:
            validated[arm][case_id] = interpret_feedback_v3(
                case["decision"], case["original_feedback"], case["job_context"], provider=recorder, hard_rules=rules,
            )
        except FeedbackProviderError as error:
            validated[arm][case_id] = {"evaluation_error": type(error).__name__}
        finally:
            recorder.finish_case(case_id)
        raw[arm][case_id] = recorder.proposals[case_id]
        if arm == "split":
            inventory[case_id] = {**provider.inventory, "diagnostics": _inventory_diagnostics(
                case["original_feedback"], provider.inventory["verified"], raw[arm][case_id], validated[arm][case_id],
            )}
        print(f"Captured pass {number} {arm} {case_id}.", file=sys.stderr)
    pass_dir = output / f"pass-{number}"
    pass_dir.mkdir()
    return {
        "pass_number": number, "directory": pass_dir.name,
        "arms": {arm: _arm_report(pass_dir, arm, cases, raw[arm], validated[arm]) for arm in ARMS},
        "inventory_file": "split.inventory.json",
        "inventory_sha256": _save_json(pass_dir / "split.inventory.json", inventory),
        "inventory_rejection_count": sum(len(result["rejections"]) for result in inventory.values()),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--novel", type=Path, default=DEFAULT_NOVEL)
    parser.add_argument("--inventory-instructions", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--handoff-instructions", type=Path, default=DEFAULT_HANDOFF)
    parser.add_argument("--output", type=Path, required=True, help="New directory for both captures and trial report")
    args = parser.parse_args(argv)

    try:
        cases, rules, fixtures = _load_cases(args.novel)
        inventory, inventory_hash = _present_text(args.inventory_instructions, "inventory instructions")
        handoff, handoff_hash = _present_text(args.handoff_instructions, "classifier handoff")
        order = _case_order(cases)
        planned_requests = [{**entry, "stage": stage} for entry in order
                            for stage in (("classifier",) if entry["arm"] == "baseline" else ("inventory", "classifier"))]
        source_hashes = {
            case["case_id"]: _fingerprint(_model_input(case["decision"], case["original_feedback"], case["job_context"], rules))
            for case in cases
        }
        args.output.mkdir(parents=True)
        configuration_sha256 = _save_json(args.output / "configuration.json", {
            "trial_version": "3.0-targeted-separate-extraction", "started_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "model": MODEL, "temperature": TEMPERATURE, "python_version": sys.version.split()[0],
            "validator_prompt_version_field": PROMPT_VERSION, "recover_explicit_conditions": False,
            "expected_requests": len(planned_requests), "planned_requests": planned_requests,
            "hard_rules_sha256": _fingerprint(rules), "fixtures": fixtures, "case_input_sha256": source_hashes,
            "known_case_ids": [case_id for _, case_id in KNOWN_CASES], "novel_case_ids": list(NOVEL_IDS),
            "inventory_instruction_file": str(args.inventory_instructions), "inventory_instructions_sha256": inventory_hash,
            "handoff_instruction_file": str(args.handoff_instructions), "handoff_instructions_sha256": handoff_hash,
            "baseline_instructions_sha256": sha256(_INSTRUCTIONS.encode()).hexdigest(),
            "split_classifier_instructions_sha256": sha256((_INSTRUCTIONS + "\n\n" + handoff).encode()).hexdigest(),
            "inventory_schema_name": _INVENTORY_NAME, "inventory_schema_sha256": _fingerprint(_INVENTORY_SCHEMA),
            "classifier_schema_name": _FINAL_NAME, "classifier_schema_sha256": _fingerprint(_PROPOSAL_SCHEMA),
            "source_sha256": {
                Path(path).name: sha256(Path(path).read_bytes()).hexdigest()
                for path in (__file__, feedback.__file__, feedback_extraction_v3.__file__, feedback_v3.__file__,
                             feedback_rules_v3.__file__, feedback_taxonomy.__file__)
            },
        })
        trace = []
        passes = [_capture_pass(args.output, number, [entry for entry in order if entry["pass_number"] == number],
                                cases, rules, trace, inventory, handoff) for number in PASSES]
        trace_hash = _save_json(args.output / "request-trace.json", trace)
        mismatches = [entry["request_number"] for entry in trace
                      if entry["origin_input_sha256"] != source_hashes[entry["case_id"]]]
        attempts = {(entry["pass_number"], entry["case_id"], entry["arm"], entry["stage"]) for entry in trace}
        unattempted = [entry for entry in planned_requests
                       if (entry["pass_number"], entry["case_id"], entry["arm"], entry["stage"]) not in attempts]
        request_errors = sum(entry["status"] == "error" for entry in trace)
        _save_json(args.output / "report.json", {
            "score_status": "automated_diagnostics_only", "configuration_sha256": configuration_sha256,
            "request_trace_file": "request-trace.json", "request_trace_sha256": trace_hash,
            "requests_attempted": len(trace), "requests_completed": len(trace) - request_errors,
            "request_errors": request_errors, "unattempted_requests": unattempted,
            "origin_input_mismatches": mismatches, "passes": passes,
        })
    except (OSError, ValueError, FeedbackProviderError) as error:
        print(f"Separate extraction trial could not complete. {error}", file=sys.stderr)
        return 2
    case_errors = any(arm["execution_errors"] for run in passes for arm in run["arms"].values())
    return int(bool(case_errors or request_errors or mismatches or unattempted))


if __name__ == "__main__":
    sys.exit(main())
