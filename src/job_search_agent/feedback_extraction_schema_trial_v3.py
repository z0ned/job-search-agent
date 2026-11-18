"""Capture a bounded v3 evidence-review comparison that varies only the response schema."""

import argparse
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import sys
from time import perf_counter

from . import feedback_extraction_schema_v3
from .feedback import FeedbackProviderError
from .feedback_evaluation import _RecordingProvider, _save_json
from .feedback_evaluation_v3 import _fingerprint
from .feedback_extraction_followup_v3 import DEFAULT_ADDENDUM, FOLLOWUP_IDS, _EvidenceReviewProvider, _prior_revalidation
from .feedback_extraction_schema_v3 import TRIAL_SCHEMA, schema_issues
from .feedback_extraction_trial_replay_v3 import DEFAULT_CANDIDATE, DEFAULT_NOVEL, _read_arms, _read_trial
from .feedback_extraction_trial_v3 import _arm_report
from .feedback_extraction_v3 import _PROPOSAL_SCHEMA
from .feedback_v3 import interpret_feedback_v3


DEFAULT_GUIDANCE = Path("benchmarks/feedback/extraction_trial_v3_schema_guidance.txt")
ARMS = ("control", "trial")


class _SchemaReviewProvider(_EvidenceReviewProvider):
    def __init__(self, model, *, response_schema, **review_arguments):
        super().__init__(model, **review_arguments)
        self._schema = response_schema
        self.input_sha256 = None

    def _request_proposal(self, model_input, *, instructions, schema_name, schema):
        self.input_sha256 = _fingerprint(model_input)
        return super()._request_proposal(
            model_input, instructions=instructions, schema_name=schema_name, schema=self._schema,
        )


def _request_order():
    return [
        {"case_id": case_id, "arm": arm}
        for index, case_id in enumerate(FOLLOWUP_IDS)
        for arm in (ARMS if index % 2 == 0 else tuple(reversed(ARMS)))
    ]


def _present_text(path, label):
    data = path.read_bytes()
    content = data.decode("utf-8")
    if not content.strip():
        raise ValueError(f"{label} cannot be blank")
    return content, sha256(data).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--novel", type=Path, default=DEFAULT_NOVEL)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--addendum", type=Path, default=DEFAULT_ADDENDUM)
    parser.add_argument("--schema-guidance", type=Path, default=DEFAULT_GUIDANCE)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if any(path.resolve() in (output, *output.parents) for path in (args.archive, args.replay)):
        parser.error("--output must be a new directory outside both source captures")

    try:
        suite, live_report, provenance = _read_trial(args.archive, args.novel, args.candidate)
        cases_by_id = {case["case_id"]: case for case in suite.cases}
        source = {"requested_model": provenance["model"], "prompt_version": provenance["validator_prompt_version_field"]}
        original, _, original_metadata = _read_arms(args.archive, live_report, set(cases_by_id), source)["candidate"]
        prior, replay_hash = _prior_revalidation(args.replay, provenance, set(cases_by_id))
        candidate, candidate_hash = _present_text(args.candidate, "candidate instructions")
        addendum, addendum_hash = _present_text(args.addendum, "evidence review addendum")
        guidance, guidance_hash = _present_text(args.schema_guidance, "schema guidance")
        common_instructions = candidate.rstrip() + "\n\n" + addendum
        instructions = common_instructions + "\n\n" + guidance
        cases = [cases_by_id[case_id] for case_id in FOLLOWUP_IDS]
        schemas = {"control": _PROPOSAL_SCHEMA, "trial": TRIAL_SCHEMA}
        schema_hashes = {arm: _fingerprint(schema) for arm, schema in schemas.items()}
        if schema_hashes["control"] == schema_hashes["trial"]:
            raise ValueError("trial response schema must differ from the control")
        schedule = _request_order()
        output.mkdir(parents=True)
        configuration_hash = _save_json(output / "configuration.json", {
            "mode": "targeted_evidence_review_schema_trial", "expected_requests": len(schedule),
            "started_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "case_ids": list(FOLLOWUP_IDS), "request_order": schedule,
            "model": provenance["model"], "temperature": provenance["temperature"],
            "response_schema_name": "feedback_extraction_v3", "response_schema_sha256": schema_hashes,
            "instructions_sha256": sha256(instructions.encode()).hexdigest(),
            "prior_evidence_review_instructions_sha256": sha256(common_instructions.encode()).hexdigest(),
            "candidate_instructions_sha256": candidate_hash, "addendum_sha256": addendum_hash,
            "schema_guidance_sha256": guidance_hash, "recover_explicit_conditions": True,
            "archived_candidate_raw_sha256": original_metadata["raw_proposals_sha256"],
            "original_archive_configuration_sha256": provenance["archive_configuration_sha256"],
            "offline_replay_report_sha256": replay_hash,
            "source_sha256": {
                **provenance["replay_source_sha256"],
                **{Path(path).name: sha256(Path(path).read_bytes()).hexdigest()
                   for path in (__file__, feedback_extraction_schema_v3.__file__)},
            },
        })
        predictions, proposals, traces = ({arm: {} for arm in ARMS}, {arm: {} for arm in ARMS}, {arm: [] for arm in ARMS})
        for index, entry in enumerate(schedule, start=1):
            arm, case_id = entry["arm"], entry["case_id"]
            case = cases_by_id[case_id]
            provider = _SchemaReviewProvider(
                provenance["model"], temperature=provenance["temperature"], instructions=instructions,
                response_schema=schemas[arm], prior={
                    "raw": original[case_id], "validated": {key: prior[case_id][key] for key in ("clauses", "interpretations")},
                },
                diagnostics={key: prior[case_id][key]
                             for key in ("validation_issues", "evidence_findings", "condition_recoveries")},
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
                "response_schema_sha256": schema_hashes[arm], "elapsed_seconds": round(perf_counter() - started, 3),
                "raw_record_sha256": _fingerprint(raw), "validated_record_sha256": _fingerprint(prediction),
                "schema_issues": schema_issues(raw) if raw is not None else [],
                **({"execution_error": prediction["evaluation_error"]} if "evaluation_error" in prediction else {}),
            })
            print(f"Captured {arm} evidence review {index}/{len(schedule)} for {case_id}.", file=sys.stderr)

        reports = {}
        for arm in ARMS:
            diagnostics = _arm_report(output, arm, cases, proposals[arm], predictions[arm])
            trace_file = f"{arm}.trace.json"
            reports[arm] = {
                **diagnostics, "trace_file": trace_file, "trace_sha256": _save_json(output / trace_file, traces[arm]),
                "raw_schema_issue_count": sum(len(entry["schema_issues"]) for entry in traces[arm]),
                "cases_with_raw_schema_issues": [entry["case_id"] for entry in traces[arm] if entry["schema_issues"]],
            }
        _save_json(output / "report.json", {
            "configuration_sha256": configuration_hash, "requests_completed": sum(len(trace) for trace in traces.values()),
            "score_status": "automated_diagnostics_only", "arms": reports,
        })
    except (OSError, ValueError, FeedbackProviderError) as error:
        print(f"Schema trial could not complete. {error}", file=sys.stderr)
        return 2
    return int(any(report["execution_errors"] for report in reports.values()))


if __name__ == "__main__":
    sys.exit(main())
