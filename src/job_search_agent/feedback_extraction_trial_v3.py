"""Capture a fixed v3 extraction-prompt trial with one request per arm and case."""

import argparse
from collections import Counter
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import sys
from time import perf_counter

from . import feedback, feedback_extraction_v3, feedback_rules_v3, feedback_taxonomy, feedback_v3
from .feedback import FeedbackProviderError
from .feedback_evaluation import _RecordingProvider, _save_json, load_suite
from .feedback_evaluation_v3 import _fingerprint, load_v3_suite
from .feedback_extraction_v3 import OpenAIFeedbackProviderV3, _INSTRUCTIONS, _PROPOSAL_SCHEMA
from .feedback_v3 import interpret_feedback_v3


KNOWN_FIXTURES = {
    "gold": Path("benchmarks/feedback/gold_cases_v3.json"),
    "regression": Path("benchmarks/feedback/holdout_cases_v2.json"),
    "holdout": Path("benchmarks/feedback/holdout_cases_v3.json"),
}
KNOWN_CASES = (
    ("gold", "FI-033"), ("gold", "FI-048"), ("holdout", "FH3-010"),
    ("gold", "FI-041"), ("regression", "FH-005"),
)
NOVEL_IDS = tuple(f"FT-{number:03d}" for number in range(1, len(KNOWN_CASES) + 1))
ARMS = ("baseline", "candidate")


class _TrialPromptProvider(OpenAIFeedbackProviderV3):
    """Change only the instruction field going into the shared request."""

    def __init__(self, model, *, temperature, candidate_instructions):
        super().__init__(model, temperature=temperature)
        self._trial_instructions = candidate_instructions

    def _request_proposal(self, model_input, *, instructions, schema_name, schema):
        return super()._request_proposal(
            model_input, instructions=self._trial_instructions, schema_name=schema_name, schema=schema,
        )


def _load_trial(novel_path):
    paths = {**KNOWN_FIXTURES, "novel": novel_path}
    suites = {kind: load_v3_suite(path, kind) for kind, path in KNOWN_FIXTURES.items()}
    suites["novel"] = load_suite(novel_path, expected_count=len(NOVEL_IDS))
    rules = suites["gold"].hard_rules
    rules_hash = _fingerprint(rules)
    if any(_fingerprint(suite.hard_rules) != rules_hash for suite in suites.values()):
        raise ValueError("all trial fixtures must use the approved gold hard-rule inputs")
    by_id = {kind: {case["case_id"]: case for case in suite.cases} for kind, suite in suites.items()}
    if by_id["novel"].keys() != set(NOVEL_IDS):
        raise ValueError("the novel trial fixture must contain FT-001 through FT-005")
    if any(case_id not in by_id[kind] for kind, case_id in KNOWN_CASES):
        raise ValueError("a required known trial case is absent from its approved fixture")

    case_keys = (*KNOWN_CASES, *(("novel", case_id) for case_id in NOVEL_IDS))
    cases = [by_id[kind][case_id] for kind, case_id in case_keys]
    fixture_sources = {
        kind: {"file": str(paths[kind]), "version": suite.version, "sha256": suite.sha256}
        for kind, suite in suites.items()
    }
    pairs = [{"known": case_id, "novel": novel_id}
             for (_, case_id), novel_id in zip(KNOWN_CASES, NOVEL_IDS, strict=True)]
    return cases, rules, fixture_sources, pairs


def _request_order(cases):
    return [
        {"arm": arm, "case_id": case["case_id"]}
        for index, case in enumerate(cases)
        for arm in (ARMS if index % 2 == 0 else tuple(reversed(ARMS)))
    ]


def _configuration(args, cases, rules, sources, pairs, candidate_bytes, model, schedule):
    return {
        "trial_version": "3.0-targeted-extraction-ab", "started_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "model": model, "temperature": args.temperature, "python_version": sys.version.split()[0],
        "validator_prompt_version_field": feedback_extraction_v3.PROMPT_VERSION,
        "arms": {
            "baseline": {"instruction_sha256": sha256(_INSTRUCTIONS.encode()).hexdigest()},
            "candidate": {"instruction_file": str(args.candidate), "instruction_sha256": sha256(candidate_bytes).hexdigest()},
        },
        "response_schema_name": "feedback_extraction_v3", "response_schema_sha256": _fingerprint(_PROPOSAL_SCHEMA),
        "hard_rules": rules, "hard_rules_sha256": _fingerprint(rules), "fixtures": sources, "paired_cases": pairs,
        "case_input_sha256": {
            case["case_id"]: _fingerprint({
                "decision": case["decision"], "original_feedback": case["original_feedback"],
                "job_context": case["job_context"], "hard_rules": rules,
            }) for case in cases
        },
        "source_sha256": {
            Path(path).name: sha256(Path(path).read_bytes()).hexdigest()
            for path in (__file__, feedback.__file__, feedback_extraction_v3.__file__, feedback_v3.__file__,
                         feedback_rules_v3.__file__, feedback_taxonomy.__file__)
        },
        "request_order": schedule,
    }


def _arm_report(output, arm, cases, proposals, predictions):
    validated_file, raw_file = f"{arm}.json", f"{arm}.proposals.json"
    diagnostics = []
    for case in cases:
        case_id = case["case_id"]
        result = predictions[case_id]
        diagnostics.append({
            "case_id": case_id, "actual_route": result.get("review_status"),
            "actual_hard_action": result.get("hard_constraint_action"),
            "expected_route": case["expected_review_status"],
            "expected_hard_action": case["expected_hard_constraint_action"],
            "validation_issues": result.get("validation_issues", []),
            "emitted_signals": len(result.get("interpretations", [])),
            **({"execution_error": result["evaluation_error"]} if "evaluation_error" in result else {}),
        })
    return {
        "validated_file": validated_file, "validated_sha256": _save_json(output / validated_file, predictions),
        "raw_proposals_file": raw_file, "raw_proposals_sha256": _save_json(output / raw_file, proposals),
        "routes": dict(Counter(case["actual_route"] for case in diagnostics if case["actual_route"] is not None)),
        "hard_actions": dict(Counter(case["actual_hard_action"] for case in diagnostics if case["actual_hard_action"] is not None)),
        "execution_errors": dict(Counter(case["execution_error"] for case in diagnostics if "execution_error" in case)),
        "validation_issue_count": sum(len(case["validation_issues"]) for case in diagnostics), "cases": diagnostics,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--novel", type=Path, required=True, help="Frozen fixture with FT-001 through FT-005")
    parser.add_argument("--candidate", type=Path, required=True, help="Complete candidate extraction instructions as UTF-8")
    parser.add_argument("--model", default="gpt-5.4-2026-03-05")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--output", type=Path, required=True, help="New directory for both captures and trial report")
    args = parser.parse_args(argv)
    try:
        cases, rules, sources, pairs = _load_trial(args.novel)
        candidate_bytes = args.candidate.read_bytes()
        candidate_instructions = candidate_bytes.decode("utf-8")
        if not candidate_instructions.strip() or candidate_instructions == _INSTRUCTIONS:
            raise ValueError("candidate instructions must be nonblank and differ from the baseline")
        providers = {
            "baseline": _RecordingProvider(OpenAIFeedbackProviderV3(args.model, temperature=args.temperature)),
            "candidate": _RecordingProvider(_TrialPromptProvider(
                args.model, temperature=args.temperature, candidate_instructions=candidate_instructions,
            )),
        }
        if providers["baseline"].model != providers["candidate"].model:
            raise ValueError("trial arms must use the same model")
        schedule = _request_order(cases)
        configuration = _configuration(
            args, cases, rules, sources, pairs, candidate_bytes, providers["baseline"].model, schedule,
        )
        args.output.mkdir(parents=True)
        configuration_hash = _save_json(args.output / "configuration.json", configuration)
        by_id = {case["case_id"]: case for case in cases}
        predictions = {arm: {} for arm in ARMS}
        request_log = []
        for entry in schedule:
            arm, case_id = entry["arm"], entry["case_id"]
            case, provider = by_id[case_id], providers[arm]
            started = perf_counter()
            try:
                prediction = interpret_feedback_v3(
                    case["decision"], case["original_feedback"], case["job_context"], provider=provider, hard_rules=rules,
                )
            except Exception as error:
                prediction = {"evaluation_error": type(error).__name__}
            finally:
                provider.finish_case(case_id)
            predictions[arm][case_id] = prediction
            request_log.append({**entry, "elapsed_seconds": round(perf_counter() - started, 3)})
            print(f"Captured {arm} {case_id} ({len(request_log)}/{len(schedule)}).", file=sys.stderr)
        reports = {arm: _arm_report(args.output, arm, cases, providers[arm].proposals, predictions[arm]) for arm in ARMS}
        _save_json(args.output / "report.json", {
            "score_status": "automated_diagnostics_only", "configuration_sha256": configuration_hash,
            "requests_completed": len(request_log), "request_log": request_log, "arms": reports,
        })
    except (ValueError, OSError, FeedbackProviderError) as error:
        print(f"Extraction trial could not complete. {error}", file=sys.stderr)
        return 2
    return int(any(report["execution_errors"] for report in reports.values()))


if __name__ == "__main__":
    sys.exit(main())
