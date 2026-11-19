"""Capture a paired v3 trial that varies only the independence guidance."""

import argparse
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import sys
from time import perf_counter

from . import feedback_extraction_followup_v3, feedback_extraction_schema_trial_v3, feedback_extraction_schema_v3
from .feedback import FeedbackProviderError, _model_input
from .feedback_evaluation import _RecordingProvider, _save_json, load_suite
from .feedback_evaluation_v3 import _fingerprint
from .feedback_extraction_followup_v3 import DEFAULT_ADDENDUM, FOLLOWUP_IDS, _prior_revalidation
from .feedback_extraction_schema_trial_v3 import DEFAULT_GUIDANCE, _SchemaReviewProvider, _present_text
from .feedback_extraction_schema_v3 import TRIAL_SCHEMA, schema_issues
from .feedback_extraction_trial_replay_v3 import DEFAULT_CANDIDATE, DEFAULT_NOVEL, _read_arms, _read_trial
from .feedback_extraction_trial_v3 import _arm_report
from .feedback_v3 import interpret_feedback_v3


DEFAULT_CONTRASTS = Path("benchmarks/feedback/extraction_independence_trial_cases_v3.json")
DEFAULT_INDEPENDENCE_GUIDANCE = Path("benchmarks/feedback/extraction_trial_v3_independent_signals.txt")
CONTRAST_IDS = ("FI3X-001", "FI3X-002", "FI3X-003", "FI3X-004")
ARMS = ("control", "treatment")
SCHEMA_NAME = "feedback_extraction_v3"


class _DirectSchemaProvider(_SchemaReviewProvider):
    """Use the same strict request transport with only original source inputs."""

    def propose(self, decision, feedback, job_context, hard_rules):
        return self._request_proposal(
            _model_input(decision, feedback, job_context, hard_rules),
            instructions=self.instructions, schema_name=SCHEMA_NAME, schema=TRIAL_SCHEMA,
        )


def _request_order():
    return [
        {"case_id": case_id, "arm": arm, "input_mode": "evidence_review" if case_id in FOLLOWUP_IDS else "direct"}
        for index, case_id in enumerate((*FOLLOWUP_IDS, *CONTRAST_IDS))
        for arm in (ARMS if index % 2 == 0 else tuple(reversed(ARMS)))
    ]


def _trial_cases(suite, contrasts_path):
    contrasts = load_suite(contrasts_path, expected_count=len(CONTRAST_IDS))
    if _fingerprint(contrasts.hard_rules) != _fingerprint(suite.hard_rules):
        raise ValueError("synthetic contrasts must use the archived approved hard-rule inputs")
    contrast_cases = {case["case_id"]: case for case in contrasts.cases}
    if contrast_cases.keys() != set(CONTRAST_IDS):
        raise ValueError("synthetic fixture must contain FI3X-001 through FI3X-004")
    known = {case["case_id"]: case for case in suite.cases}
    if not set(FOLLOWUP_IDS) <= known.keys():
        raise ValueError("archived trial must contain all six evidence-review cases")
    return [*[known[case_id] for case_id in FOLLOWUP_IDS], *[contrast_cases[case_id] for case_id in CONTRAST_IDS]], contrasts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--novel", type=Path, default=DEFAULT_NOVEL, help="Novel fixture for the archived extraction trial")
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--addendum", type=Path, default=DEFAULT_ADDENDUM)
    parser.add_argument("--schema-guidance", type=Path, default=DEFAULT_GUIDANCE)
    parser.add_argument("--contrasts", type=Path, default=DEFAULT_CONTRASTS)
    parser.add_argument("--independence-guidance", type=Path, default=DEFAULT_INDEPENDENCE_GUIDANCE)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if any(path.resolve() in (output, *output.parents) for path in (args.archive, args.replay)):
        parser.error("--output must be a new directory outside both source captures")

    try:
        suite, live_report, provenance = _read_trial(args.archive, args.novel, args.candidate)
        case_ids = {case["case_id"] for case in suite.cases}
        source = {"requested_model": provenance["model"], "prompt_version": provenance["validator_prompt_version_field"]}
        original, _, original_metadata = _read_arms(args.archive, live_report, case_ids, source)["candidate"]
        prior, replay_hash = _prior_revalidation(args.replay, provenance, case_ids)
        cases, contrasts = _trial_cases(suite, args.contrasts)
        candidate, candidate_hash = _present_text(args.candidate, "candidate instructions")
        addendum, addendum_hash = _present_text(args.addendum, "evidence review addendum")
        schema_guidance, schema_guidance_hash = _present_text(args.schema_guidance, "schema guidance")
        independence, independence_hash = _present_text(args.independence_guidance, "independence guidance")
        controls = {
            "evidence_review": candidate.rstrip() + "\n\n" + addendum + "\n\n" + schema_guidance,
            "direct": candidate.rstrip() + "\n\n" + schema_guidance,
        }
        instructions = {mode: {"control": control, "treatment": control + "\n\n" + independence}
                        for mode, control in controls.items()}
        instruction_hashes = {mode: {arm: sha256(text.encode()).hexdigest() for arm, text in arms.items()}
                              for mode, arms in instructions.items()}
        schema_hash = _fingerprint(TRIAL_SCHEMA)
        schedule = _request_order()
        output.mkdir(parents=True)
        configuration_hash = _save_json(output / "configuration.json", {
            "mode": "targeted_independent_signal_trial", "expected_requests": len(schedule),
            "started_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "python_version": sys.version.split()[0],
            "known_case_ids": list(FOLLOWUP_IDS), "synthetic_case_ids": list(CONTRAST_IDS), "request_order": schedule,
            "model": provenance["model"], "temperature": provenance["temperature"], "response_schema_name": SCHEMA_NAME,
            "validator_prompt_version_field": provenance["validator_prompt_version_field"],
            "response_schema_sha256": schema_hash, "recover_explicit_conditions": True,
            "instructions_sha256": instruction_hashes, "candidate_instructions_sha256": candidate_hash,
            "evidence_review_addendum_sha256": addendum_hash, "schema_guidance_sha256": schema_guidance_hash,
            "independence_guidance_sha256": independence_hash,
            "archived_candidate_raw_sha256": original_metadata["raw_proposals_sha256"],
            "original_archive_configuration_sha256": provenance["archive_configuration_sha256"],
            "offline_replay_report_sha256": replay_hash, "hard_rules_sha256": provenance["hard_rules_sha256"],
            "synthetic_fixture": {"file": str(args.contrasts), "version": contrasts.version, "sha256": contrasts.sha256},
            "source_sha256": {
                **provenance["replay_source_sha256"],
                **{Path(path).name: sha256(Path(path).read_bytes()).hexdigest()
                   for path in (__file__, feedback_extraction_schema_v3.__file__, feedback_extraction_followup_v3.__file__,
                                feedback_extraction_schema_trial_v3.__file__)},
            },
        })
        cases_by_id = {case["case_id"]: case for case in cases}
        predictions, proposals, traces = ({arm: {} for arm in ARMS}, {arm: {} for arm in ARMS}, {arm: [] for arm in ARMS})
        for index, entry in enumerate(schedule, start=1):
            arm, case_id, mode = entry["arm"], entry["case_id"], entry["input_mode"]
            case = cases_by_id[case_id]
            review = mode == "evidence_review"
            provider_class = _SchemaReviewProvider if review else _DirectSchemaProvider
            provider = provider_class(
                provenance["model"], temperature=provenance["temperature"], instructions=instructions[mode][arm],
                response_schema=TRIAL_SCHEMA, prior={
                    "raw": original[case_id], "validated": {key: prior[case_id][key] for key in ("clauses", "interpretations")},
                } if review else None,
                diagnostics={key: prior[case_id][key]
                             for key in ("validation_issues", "evidence_findings", "condition_recoveries")} if review else None,
            )
            recorder = _RecordingProvider(provider)
            started = perf_counter()
            try:
                prediction = interpret_feedback_v3(
                    case["decision"], case["original_feedback"], case["job_context"], provider=recorder,
                    hard_rules=suite.hard_rules, recover_explicit_conditions=True,
                )
            except FeedbackProviderError as error:
                prediction = {"evaluation_error": type(error).__name__}
            finally:
                recorder.finish_case(case_id)
            raw = recorder.proposals[case_id]
            predictions[arm][case_id], proposals[arm][case_id] = prediction, raw
            traces[arm].append({
                **entry, "request_number": index, "input_sha256": provider.input_sha256,
                "instructions_sha256": instruction_hashes[mode][arm], "response_schema_sha256": schema_hash,
                "elapsed_seconds": round(perf_counter() - started, 3), "raw_record_sha256": _fingerprint(raw),
                "validated_record_sha256": _fingerprint(prediction), "schema_issues": schema_issues(raw) if raw is not None else [],
                **({"execution_error": prediction["evaluation_error"]} if "evaluation_error" in prediction else {}),
            })
            print(f"Captured {arm} {case_id} ({index}/{len(schedule)}).", file=sys.stderr)

        reports = {}
        for arm in ARMS:
            diagnostics = _arm_report(output, arm, cases, proposals[arm], predictions[arm])
            trace_file = f"{arm}.trace.json"
            reports[arm] = {
                **diagnostics, "trace_file": trace_file, "trace_sha256": _save_json(output / trace_file, traces[arm]),
                "raw_schema_issue_count": sum(len(entry["schema_issues"]) for entry in traces[arm]),
                "cases_with_raw_schema_issues": [entry["case_id"] for entry in traces[arm] if entry["schema_issues"]],
            }
        paired_input_mismatches = [
            control["case_id"] for control, treatment in zip(traces["control"], traces["treatment"], strict=True)
            if control["input_sha256"] is None or control["input_sha256"] != treatment["input_sha256"]
        ]
        _save_json(output / "report.json", {
            "configuration_sha256": configuration_hash, "requests_completed": sum(len(trace) for trace in traces.values()),
            "score_status": "automated_diagnostics_only", "paired_input_mismatch_case_ids": paired_input_mismatches, "arms": reports,
        })
    except (OSError, ValueError, FeedbackProviderError) as error:
        print(f"Independence trial could not complete. {error}", file=sys.stderr)
        return 2
    return int(bool(paired_input_mismatches) or any(report["execution_errors"] for report in reports.values()))


if __name__ == "__main__":
    sys.exit(main())
