from __future__ import annotations

import json

import pytest

from polynexus_core.runtime.d1b_producer import (
    build_d1b_execution_plan,
    produce_d1b_runtime_evidence,
)
from polynexus_core.runtime.external_contracts import ExternalContractError
from polynexus_core.storage.content import ContentStore


def _plan(*, cross_review: bool = False):
    return build_d1b_execution_plan(
        task_id="task-d1b-runtime",
        generation_revision=1,
        run_id="run-d1b-reviewer" if cross_review else "run-d1b-runtime",
        candidate_id="sha256:" + "1" * 64,
        contract_id="sha256:" + "2" * 64,
        result_snapshot_id="sha256:" + "3" * 64,
        check_ids=("tests",),
        observation_kind="D1B_CROSS_REVIEW" if cross_review else "D1B_DETERMINISTIC_CHECK",
        reviewer_ref="reviewer:d1b-runtime" if cross_review else None,
        reviewer_profile_ref="sha256:" + "2" * 64 if cross_review else None,
        reviewer_profile_revision=1 if cross_review else None,
        reviewed_candidate_id="sha256:" + "1" * 64 if cross_review else None,
        reviewed_contract_id="sha256:" + "2" * 64 if cross_review else None,
        reviewed_verification_id="verification-target" if cross_review else None,
        reviewed_evidence_set_id="evidence-set-target" if cross_review else None,
        reviewed_evidence_id="evidence-target" if cross_review else None,
    )


def test_runtime_producer_emits_explicit_deterministic_check(tmp_path):
    evidence, artifacts = produce_d1b_runtime_evidence(
        plan=_plan(),
        task_id="task-d1b-runtime",
        run_id="run-d1b-runtime",
        project_id="project-d1b-runtime",
        normalized_result={
            "d1b_checks": [{
                "check_id": "tests",
                "argv": ["pytest", "-q"],
                "cwd": "C:/managed/checks",
                "runner_exit": 0,
                "child_exit": 0,
                "output": "2 passed",
                "execution_id": "exec-d1b-runtime",
            }],
        },
        runner_exit=0,
        default_cwd="C:/managed/run",
        content_store=ContentStore(tmp_path / "content"),
    )
    assert len(evidence) == 1 and len(artifacts) == 1
    assert evidence[0].metadata["d1b_observation_kind"] == "D1B_DETERMINISTIC_CHECK"
    assert evidence[0].metadata["d1b_check_id"] == "tests"
    assert evidence[0].metadata["child_exit"] == 0
    assert artifacts[0].artifact_type.value == "TEST_RESULT"


def test_runtime_producer_emits_bound_cross_review_facts(tmp_path):
    evidence, _ = produce_d1b_runtime_evidence(
        plan=_plan(cross_review=True),
        task_id="task-d1b-runtime",
        run_id="run-d1b-reviewer",
        project_id="project-d1b-runtime",
        normalized_result={
            "d1b_checks": [{
                "check_id": "tests",
                "argv": ["reviewer", "--candidate"],
                "cwd": "C:/managed/reviewer",
                "child_exit": 0,
                "output": "independent review passed",
            }],
        },
        runner_exit=0,
        default_cwd="C:/managed/reviewer",
        content_store=ContentStore(tmp_path / "content"),
    )
    assert evidence[0].metadata["d1b_observation_kind"] == "D1B_CROSS_REVIEW"
    assert evidence[0].metadata["reviewer_ref"] == "reviewer:d1b-runtime"
    assert evidence[0].metadata["reviewed_evidence_id"] == "evidence-target"


def test_generic_runtime_result_does_not_synthesize_d1b_evidence(tmp_path):
    with pytest.raises(ExternalContractError, match="d1b_execution_plan_invalid"):
        produce_d1b_runtime_evidence(
            plan=None,  # type: ignore[arg-type]
            task_id="task-d1b-runtime",
            run_id="run-d1b-runtime",
            project_id="project-d1b-runtime",
            normalized_result={"format": "codex.exec.jsonl.v1"},
            runner_exit=0,
            default_cwd="C:/managed/run",
            content_store=ContentStore(tmp_path / "content"),
        )


def test_runtime_producer_rejects_missing_child_exit(tmp_path):
    with pytest.raises(ExternalContractError, match="d1b_execution_plan_invalid"):
        produce_d1b_runtime_evidence(
            plan=_plan(),
            task_id="task-d1b-runtime",
            run_id="run-d1b-runtime",
            project_id="project-d1b-runtime",
            normalized_result={
                "d1b_checks": [{
                    "check_id": "tests",
                    "argv": ["pytest", "-q"],
                    "cwd": "C:/managed/checks",
                    "output": "missing child exit",
                }],
            },
            runner_exit=0,
            default_cwd="C:/managed/run",
            content_store=ContentStore(tmp_path / "content"),
        )
