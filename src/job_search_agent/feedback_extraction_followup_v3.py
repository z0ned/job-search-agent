"""Capture a bounded evidence review for six saved extraction-trial cases."""

import argparse
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
import sys

from .feedback import FeedbackProviderError, _model_input
from .feedback_evaluation import _RecordingProvider, _save_json
from .feedback_extraction_trial_replay_v3 import (
    DEFAULT_CANDIDATE, DEFAULT_NOVEL, _read_arms, _read_trial,
)
from .feedback_extraction_trial_v3 import _arm_report
from .feedback_extraction_v3 import _PROPOSAL_SCHEMA, OpenAIFeedbackProviderV3
from .feedback_replay_v3 import _read_archive_json
from .feedback_v3 import interpret_feedback_v3


FOLLOWUP_IDS = ("FI-033", "FI-048", "FI-041", "FT-002", "FT-004", "FT-005")
DEFAULT_ADDENDUM = Path("benchmarks/feedback/extraction_trial_v3_evidence_review.txt")


class _EvidenceReviewProvider(OpenAIFeedbackProviderV3):
    def __init__(self, model, *, temperature, instructions, prior, diagnostics):
        super().__init__(model, temperature=temperature)
        self.instructions = instructions
        self.prior = prior
        self.diagnostics = diagnostics

    def propose(self, decision, feedback, job_context, hard_rules):
        inputs = _model_input(decision, feedback, job_context, hard_rules)
        inputs.update(prior_proposal=self.prior, review_findings=self.diagnostics)
        return self._request_proposal(
            inputs, instructions=self.instructions, schema_name="feedback_extraction_v3", schema=_PROPOSAL_SCHEMA,
        )


def _prior_revalidation(path, provenance, case_ids):
    report, report_hash = _read_archive_json(path / "report.json")
    if report.get("recover_explicit_conditions") is not True or report.get("inference_requests") != 0:
        raise ValueError("replay must use the offline evidence checks and condition recovery")
    configuration_hash = report.get("configuration_sha256")
    if not isinstance(configuration_hash, str):
        raise ValueError("offline replay report lacks its configuration digest")
    configuration, _ = _read_archive_json(path / "configuration.json", configuration_hash)
    required = ("archive_configuration_sha256", "case_input_sha256", "hard_rules_sha256", "replay_source_sha256")
    if any(configuration.get(key) != provenance[key] for key in required):
        raise ValueError("offline replay does not match the original trial inputs and active validator")
    arms = report.get("arms")
    candidate = arms.get("candidate") if isinstance(arms, Mapping) else None
    if not isinstance(candidate, Mapping) or candidate.get("execution_errors"):
        raise ValueError("offline replay must provide complete candidate diagnostics")
    validated_hash = candidate.get("validated_sha256")
    if not isinstance(validated_hash, str):
        raise ValueError("offline replay report lacks its candidate digest")
    prior, _ = _read_archive_json(path / "candidate.json", validated_hash)
    if prior.keys() != case_ids or any(
        not isinstance(record, Mapping) or any(
            not isinstance(record.get(key), list)
            for key in ("clauses", "interpretations", "validation_issues", "evidence_findings", "condition_recoveries")
        )
        for record in prior.values()
    ):
        raise ValueError("offline replay must describe every trial case with evidence checks enabled")
    return prior, report_hash


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--novel", type=Path, default=DEFAULT_NOVEL)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--addendum", type=Path, default=DEFAULT_ADDENDUM)
    args = parser.parse_args(argv)

    try:
        suite, live_report, provenance = _read_trial(args.archive, args.novel, args.candidate)
        cases_by_id = {case["case_id"]: case for case in suite.cases}
        source = {"requested_model": provenance["model"], "prompt_version": provenance["validator_prompt_version_field"]}
        original, _, _ = _read_arms(args.archive, live_report, set(cases_by_id), source)["candidate"]
        prior, replay_hash = _prior_revalidation(args.replay, provenance, set(cases_by_id))
        addendum = args.addendum.read_text(encoding="utf-8")
        if not addendum.strip():
            raise ValueError("evidence review addendum cannot be blank")
        instructions = args.candidate.read_text(encoding="utf-8").rstrip() + "\n\n" + addendum
        cases = [cases_by_id[case_id] for case_id in FOLLOWUP_IDS]
        args.output.mkdir(parents=True)
        configuration_sha256 = _save_json(args.output / "configuration.json", {
            "mode": "targeted_evidence_review_followup", "expected_requests": len(cases), "case_ids": list(FOLLOWUP_IDS),
            "model": provenance["model"], "temperature": provenance["temperature"],
            "response_schema_sha256": provenance["response_schema_sha256"],
            "instructions_sha256": sha256(instructions.encode()).hexdigest(),
            "addendum_sha256": sha256(args.addendum.read_bytes()).hexdigest(),
            "archived_candidate_raw_sha256": live_report["arms"]["candidate"]["raw_proposals_sha256"],
            "original_archive_configuration_sha256": provenance["archive_configuration_sha256"],
            "offline_replay_report_sha256": replay_hash,
            "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        })
        predictions, proposals = {}, {}
        for index, case in enumerate(cases, 1):
            case_id = case["case_id"]
            prior_proposal = {
                "raw": original[case_id],
                "validated": {key: prior[case_id][key] for key in ("clauses", "interpretations")},
            }
            provider = _RecordingProvider(_EvidenceReviewProvider(
                provenance["model"], temperature=provenance["temperature"], instructions=instructions,
                prior=prior_proposal,
                diagnostics={key: prior[case_id][key]
                             for key in ("validation_issues", "evidence_findings", "condition_recoveries")},
            ))
            try:
                predictions[case_id] = interpret_feedback_v3(
                    case["decision"], case["original_feedback"], case["job_context"], provider=provider,
                    hard_rules=suite.hard_rules, recover_explicit_conditions=True,
                )
            except FeedbackProviderError as error:
                predictions[case_id] = {"evaluation_error": type(error).__name__}
            finally:
                provider.finish_case(case_id)
            proposals.update(provider.proposals)
            print(f"Captured evidence review {index}/{len(cases)} for {case_id}.", file=sys.stderr)
        diagnostics = _arm_report(args.output, "followup", cases, proposals, predictions)
        _save_json(args.output / "report.json", {
            "configuration_sha256": configuration_sha256, "requests_completed": len(proposals),
            "score_status": "automated_diagnostics_only", **diagnostics,
        })
    except (OSError, ValueError, FeedbackProviderError) as error:
        print(f"Evidence review could not complete. {error}", file=sys.stderr)
        return 2
    return int(bool(diagnostics["execution_errors"]))


if __name__ == "__main__":
    sys.exit(main())
