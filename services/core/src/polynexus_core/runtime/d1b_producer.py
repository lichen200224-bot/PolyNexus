"""Core-owned producer for explicit D1b check evidence.

The ordinary runtime result remains generic runtime evidence.  A D1b check is
emitted only when Core supplied an immutable execution plan and the terminal
runtime payload contains an explicit, bounded result for that plan.  This
module never infers a check from process success or from a diff artifact.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from polynexus_core.domain.enums import ArtifactType, EvidenceStatus, EvidenceType
from polynexus_core.domain.models import Artifact, Evidence
from polynexus_core.runtime.external_contracts import ExternalContractError
from polynexus_core.storage.content import ContentStore


_OBSERVATION_KINDS = frozenset({"D1B_DETERMINISTIC_CHECK", "D1B_CROSS_REVIEW"})
_MAX_CHECKS = 256
_MAX_OUTPUT_BYTES = 1 * 1024 * 1024


def _invalid() -> ExternalContractError:
    return ExternalContractError("d1b_execution_plan_invalid")


def _required_text(value: object, *, limit: int = 256) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise _invalid()
    return value


def _required_int(value: object, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise _invalid()
    return value


@dataclass(frozen=True)
class D1bExecutionPlan:
    """Immutable plan issued by the Core verification boundary.

    This is intentionally not read from caller-owned ContextPackage facts.
    The D1b repository constructs it only after resolving the candidate,
    snapshots, validation contract and terminal Run from Core-owned rows.
    """

    task_id: str
    generation_revision: int
    run_id: str
    candidate_id: str
    contract_id: str
    result_snapshot_id: str
    check_ids: tuple[str, ...]
    observation_kind: str = "D1B_DETERMINISTIC_CHECK"
    reviewer_ref: str | None = None
    reviewer_profile_ref: str | None = None
    reviewer_profile_revision: int | None = None
    reviewed_candidate_id: str | None = None
    reviewed_contract_id: str | None = None
    reviewed_verification_id: str | None = None
    reviewed_evidence_set_id: str | None = None
    reviewed_evidence_id: str | None = None

    def __post_init__(self) -> None:
        for value in (
            self.task_id,
            self.run_id,
            self.candidate_id,
            self.contract_id,
            self.result_snapshot_id,
        ):
            _required_text(value)
        _required_int(self.generation_revision, minimum=1)
        if self.observation_kind not in _OBSERVATION_KINDS:
            raise _invalid()
        if (
            not isinstance(self.check_ids, tuple)
            or not self.check_ids
            or len(self.check_ids) > _MAX_CHECKS
            or any(not isinstance(value, str) or not value.strip() for value in self.check_ids)
            or len(set(self.check_ids)) != len(self.check_ids)
        ):
            raise _invalid()
        if self.observation_kind == "D1B_CROSS_REVIEW":
            for value in (
                self.reviewer_ref,
                self.reviewer_profile_ref,
                self.reviewed_candidate_id,
                self.reviewed_contract_id,
                self.reviewed_verification_id,
                self.reviewed_evidence_set_id,
                self.reviewed_evidence_id,
            ):
                _required_text(value)
            _required_int(self.reviewer_profile_revision, minimum=1)


def build_d1b_execution_plan(
    *,
    task_id: str,
    generation_revision: int,
    run_id: str,
    candidate_id: str,
    contract_id: str,
    result_snapshot_id: str,
    check_ids: tuple[str, ...],
    observation_kind: str = "D1B_DETERMINISTIC_CHECK",
    reviewer_ref: str | None = None,
    reviewer_profile_ref: str | None = None,
    reviewer_profile_revision: int | None = None,
    reviewed_candidate_id: str | None = None,
    reviewed_contract_id: str | None = None,
    reviewed_verification_id: str | None = None,
    reviewed_evidence_set_id: str | None = None,
    reviewed_evidence_id: str | None = None,
) -> D1bExecutionPlan:
    """Construct a plan at a Core-owned boundary; callers cannot supply it to runtime facts."""

    return D1bExecutionPlan(
        task_id=task_id,
        generation_revision=generation_revision,
        run_id=run_id,
        candidate_id=candidate_id,
        contract_id=contract_id,
        result_snapshot_id=result_snapshot_id,
        check_ids=tuple(check_ids),
        observation_kind=observation_kind,
        reviewer_ref=reviewer_ref,
        reviewer_profile_ref=reviewer_profile_ref,
        reviewer_profile_revision=reviewer_profile_revision,
        reviewed_candidate_id=reviewed_candidate_id,
        reviewed_contract_id=reviewed_contract_id,
        reviewed_verification_id=reviewed_verification_id,
        reviewed_evidence_set_id=reviewed_evidence_set_id,
        reviewed_evidence_id=reviewed_evidence_id,
    )


def produce_d1b_runtime_evidence(
    *,
    plan: D1bExecutionPlan,
    task_id: str,
    run_id: str,
    project_id: str,
    normalized_result: Mapping[str, Any],
    runner_exit: int,
    default_cwd: str,
    content_store: ContentStore,
) -> tuple[tuple[Evidence, ...], tuple[Artifact, ...]]:
    """Convert explicit terminal runtime checks into durable D1b evidence.

    The plan must be a Core-issued immutable ``D1bExecutionPlan``.  A generic
    runtime result without such a plan never becomes D1b evidence.
    """
    if not isinstance(plan, D1bExecutionPlan) or plan.task_id != task_id or plan.run_id != run_id:
        raise _invalid()
    checks = normalized_result.get("d1b_checks")
    if not isinstance(checks, list) or not checks or len(checks) > _MAX_CHECKS:
        raise _invalid()
    candidate_id = plan.candidate_id
    contract_id = plan.contract_id
    result_snapshot_id = plan.result_snapshot_id
    generation_revision = plan.generation_revision
    observation_kind = plan.observation_kind
    planned_id_set = set(plan.check_ids)
    if isinstance(runner_exit, bool) or not isinstance(runner_exit, int):
        raise _invalid()
    default_cwd = _required_text(default_cwd, limit=1024)
    if observation_kind == "D1B_CROSS_REVIEW":
        reviewer_ref = plan.reviewer_ref
        reviewer_profile_ref = plan.reviewer_profile_ref
        reviewer_profile_revision = plan.reviewer_profile_revision
        reviewed_candidate_id = plan.reviewed_candidate_id
        reviewed_contract_id = plan.reviewed_contract_id
        reviewed_verification_id = plan.reviewed_verification_id
        reviewed_evidence_set_id = plan.reviewed_evidence_set_id
        reviewed_evidence_id = plan.reviewed_evidence_id

    evidence: list[Evidence] = []
    artifacts: list[Artifact] = []
    seen_check_ids: set[str] = set()
    for check in checks:
        if not isinstance(check, dict):
            raise _invalid()
        check_id = _required_text(check.get("check_id"), limit=256)
        if check_id in seen_check_ids or (planned_id_set is not None and check_id not in planned_id_set):
            raise _invalid()
        seen_check_ids.add(check_id)
        argv = check.get("argv")
        if (
            not isinstance(argv, list)
            or not argv
            or len(argv) > 128
            or any(not isinstance(value, str) or not value for value in argv)
        ):
            raise _invalid()
        cwd = check.get("cwd", default_cwd)
        cwd = _required_text(cwd, limit=1024)
        child_exit = _required_int(check.get("child_exit"))
        check_runner_exit = check.get("runner_exit", runner_exit)
        check_runner_exit = _required_int(check_runner_exit)
        output = check.get("output")
        if not isinstance(output, str) or len(output.encode("utf-8")) > _MAX_OUTPUT_BYTES:
            raise _invalid()
        artifact_bytes = output.encode("utf-8")
        digest, size = content_store.put(artifact_bytes)
        artifact = Artifact(
            project_id=project_id,
            task_id=task_id,
            run_id=run_id,
            artifact_type=ArtifactType.TEST_RESULT,
            mime_type="text/plain",
            source_type="runtime.codex.exec.d1b",
            storage_ref=f"core-blob:{digest}",
            sha256=digest,
            size=size,
        )
        metadata: dict[str, Any] = {
            "d1b_check_id": check_id,
            "d1b_candidate_id": candidate_id,
            "d1b_contract_id": contract_id,
            "d1b_result_snapshot_id": result_snapshot_id,
            "d1b_task_id": task_id,
            "d1b_generation_revision": generation_revision,
            "d1b_run_id": run_id,
            "d1b_observation_kind": observation_kind,
            "argv_json": json.dumps(argv, ensure_ascii=False, separators=(",", ":")),
            "cwd": cwd,
            "exit_code": check_runner_exit,
            "child_exit": child_exit,
            "execution_id": check.get("execution_id", run_id),
        }
        if observation_kind == "D1B_CROSS_REVIEW":
            metadata.update({
                "reviewer_ref": reviewer_ref,
                "reviewed_candidate_id": reviewed_candidate_id,
                "reviewed_contract_id": reviewed_contract_id,
                "reviewed_verification_id": reviewed_verification_id,
                "reviewed_evidence_set_id": reviewed_evidence_set_id,
                "reviewed_evidence_id": reviewed_evidence_id,
                "reviewer_profile_ref": reviewer_profile_ref,
                "reviewer_profile_revision": reviewer_profile_revision,
            })
        evidence.append(Evidence(
            task_id=task_id,
            run_id=run_id,
            actor_id=(reviewer_ref if observation_kind == "D1B_CROSS_REVIEW" else "runtime:codex.exec.d1b"),
            source="runtime.codex.exec.d1b",
            type=EvidenceType.TOOL_EVIDENCE,
            status=EvidenceStatus.PASS if check_runner_exit == 0 and child_exit == 0 else EvidenceStatus.FAIL,
            artifact_refs=(artifact.id,),
            metadata=metadata,
        ))
        artifacts.append(artifact)
    if seen_check_ids != planned_id_set:
        raise _invalid()
    return tuple(evidence), tuple(artifacts)
