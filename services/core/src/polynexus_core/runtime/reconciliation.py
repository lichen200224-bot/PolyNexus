"""Fail-closed reconciliation of non-terminal Runs after process restart.

This module is deliberately narrower than execution.  Startup never creates a
new Run, calls ``create_run()``, or calls ``submit()``.  It reloads the existing
Run-owned binding, asks the resolved adapter for status, and either records a
truthful terminal outcome or moves the Run through
``CANCEL_REQUESTED -> ORPHANED`` when cleanup cannot be verified.
"""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, replace

from sqlalchemy.orm import Session

from polynexus_core.domain.enums import (
    EvidenceStatus,
    EvidenceType,
    RunState,
)
from polynexus_core.domain.models import (
    Artifact,
    Evidence,
    Finding,
    Run,
    RunResult,
)
from polynexus_core.domain.runtime_binding import RuntimeBindingSnapshot
from polynexus_core.domain.run_lifecycle import TERMINAL_STATES
from polynexus_core.persistence.repository import (
    SqlArtifactRepository,
    SqlEvidenceRepository,
    SqlFindingRepository,
    SqlRunRepository,
    SqlRuntimeBindingSnapshotRepository,
)
from polynexus_core.runtime.contracts import RuntimeAdapter, RuntimeResult
from polynexus_core.runtime.registry import (
    RuntimeRegistry,
    _validate_v1_profile,
    build_default_registry,
)


_UNBOUND_RUN_REASON = "Startup reconciliation requires an immutable runtime binding"
_CREATED_BOUND_REASON = "CREATED Run cannot own an execution binding"
_BINDING_UNAVAILABLE_REASON = "Run orphaned because its runtime binding is unavailable"
_STATUS_UNAVAILABLE_REASON = "Run orphaned because runtime status could not be verified"
_CLEANUP_UNVERIFIED_REASON = "Run orphaned because restart cleanup could not be verified"
_CONFLICTING_CANCEL_REASON = "Run orphaned because cancellation and runtime completion conflicted"
_RUNTIME_FAILED_REASON = "Runtime failure observed during restart reconciliation"
_COMPLETED_OBSERVED_REASON = "Runtime completion observed during restart reconciliation"
_COMPLETED_SUMMARY = "Run completed after restart reconciliation"
_SENSITIVE_MARKERS = (
    "secret",
    "token",
    "password",
    "credential",
    "authorization",
    "bearer",
    "api_key",
    "private key",
)
_SAFE_ADAPTER_VERSION = re.compile(
    r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*/[0-9]+(?:\.[0-9]+)*$"
)
_CANCELLED_REASON = "Run cancelled and restart cleanup verified"
_TIMED_OUT_REASON = "Run timed out and restart cleanup verified"
_RECOVERY_EVIDENCE_ACTOR = "system:restart-reconciliation"
_CANCELLED_SUMMARY = "Run cancelled and restart cleanup verified"


class RestartReconciliationError(RuntimeError):
    """Raised when startup cannot safely inspect a non-terminal Run."""


@dataclass(frozen=True)
class ReconciliationReport:
    """Deterministic summary of one startup reconciliation pass."""

    examined: int
    reconciled: int
    orphaned: int


@dataclass(frozen=True)
class _RecoveryOutputs:
    result: RunResult | None = None
    findings: tuple[Finding, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    artifacts: tuple[Artifact, ...] = ()


async def reconcile_non_terminal_runs(
    session: Session,
    registry: RuntimeRegistry | None = None,
) -> ReconciliationReport:
    """Reconcile all non-terminal durable Runs without resubmission.

    Missing or legacy-only bindings on a claimed Run are a startup stop
    condition.  An unclaimed CREATED Run is durable pending intent and is
    deliberately left unchanged.  Claimed Runs are
    preflighted before any Run mutation so one bad row cannot leave a partial
    reconciliation pass.  A present binding whose adapter/status/cleanup is
    unavailable is instead persisted as ORPHANED through the legal lifecycle
    path; raw adapter exception text is never persisted.

    The caller owns the transaction and must commit the returned pass.  Any
    exception, including :class:`RestartReconciliationError`, must roll back.
    """
    run_repo = SqlRunRepository(session)
    binding_repo = SqlRuntimeBindingSnapshotRepository(session)
    runs = tuple(run_repo.list_non_terminal())
    if not runs:
        return ReconciliationReport(examined=0, reconciled=0, orphaned=0)

    # Preflight the immutable binding boundary before mutating any Run.  A
    # legacy backfill is intentionally not treated as a resolved runtime fact:
    # it has no profile reference from which an adapter can be reconstructed.
    bindings: dict[str, RuntimeBindingSnapshot] = {}
    for run in runs:
        binding = binding_repo.get_by_run(run.id)
        if run.state is RunState.CREATED:
            if binding is None or binding.legacy_backfill:
                # A create-without-execute request has not crossed the execution
                # claim boundary.  Restart must preserve it without fabricating a
                # binding, contacting an adapter, or launching duplicate work.
                continue
            raise RestartReconciliationError(_CREATED_BOUND_REASON)
        if (
            binding is None
            or binding.legacy_backfill
            or binding.runtime_profile_ref is None
        ):
            raise RestartReconciliationError(_UNBOUND_RUN_REASON)
        bindings[run.id] = binding

    registry = registry or build_default_registry()
    finding_repo = SqlFindingRepository(session)
    evidence_repo = SqlEvidenceRepository(session)
    artifact_repo = SqlArtifactRepository(session)
    reconciled = 0
    orphaned = 0

    for run in runs:
        if run.id not in bindings:
            continue
        binding = bindings[run.id]
        try:
            profile = registry.resolve(binding.runtime_profile_ref)
            _validate_v1_profile(
                profile,
                static_registered=registry.is_registered_dispatch_tool(profile),
            )
            if not _profile_matches_snapshot(profile, binding):
                raise RuntimeError("runtime binding/profile mismatch")
            adapter = registry.create_adapter(profile)
        except Exception:
            _orphan(run, _BINDING_UNAVAILABLE_REASON)
            run_repo.update(run)
            orphaned += 1
            continue

        try:
            outputs = await _reconcile_one(run, adapter, binding)
        except asyncio.CancelledError:
            # Preserve the outer interruption contract: the current Run is
            # durably marked before the startup owner commits and re-raises.
            _orphan(run, _CLEANUP_UNVERIFIED_REASON)
            run_repo.update(run)
            session.flush()
            raise
        run_repo.update(run)
        if outputs is None:
            if run.state is RunState.ORPHANED:
                orphaned += 1
            else:
                reconciled += 1
            continue

        for finding in outputs.findings:
            finding_repo.add(finding)
        for evidence in outputs.evidence:
            evidence_repo.add(evidence)
        for artifact in outputs.artifacts:
            artifact_repo.add(artifact)
        reconciled += 1

    return ReconciliationReport(
        examined=len(runs),
        reconciled=reconciled,
        orphaned=orphaned,
    )


async def _reconcile_one(
    run: Run,
    adapter: RuntimeAdapter,
    binding: RuntimeBindingSnapshot,
) -> _RecoveryOutputs | None:
    """Reconcile one bound Run; adapter errors fail closed to ORPHANED."""
    if not run.runtime_ref:
        _orphan(run, _STATUS_UNAVAILABLE_REASON)
        return None

    try:
        status = await adapter.status(run.runtime_ref)
    except asyncio.CancelledError:
        if _external_task_cancellation_requested():
            raise
        _orphan(run, _STATUS_UNAVAILABLE_REASON)
        return None
    except Exception:
        _orphan(run, _STATUS_UNAVAILABLE_REASON)
        return None

    if status.state is RunState.COMPLETED:
        if run.state is RunState.CANCEL_REQUESTED:
            _orphan(run, _CONFLICTING_CANCEL_REASON)
            return None
        try:
            # Fetching these values proves the completed runtime is readable,
            # and the normalized payload is retained only after the restart
            # boundary validates its ownership and public-safe shape.
            runtime_result = await adapter.result(run.runtime_ref)
            adapter_artifacts = await adapter.artifacts(run.runtime_ref)
            runtime_version = adapter.version_info()
        except asyncio.CancelledError:
            if _external_task_cancellation_requested():
                raise
            _orphan(run, _STATUS_UNAVAILABLE_REASON)
            return None
        except Exception:
            _orphan(run, _STATUS_UNAVAILABLE_REASON)
            return None
        if not _safe_adapter_version(runtime_version):
            _orphan(run, _STATUS_UNAVAILABLE_REASON)
            return None
        if not _mark_completed(run):
            return None
        return _build_completed_outputs(
            run,
            binding,
            runtime_result,
            adapter_artifacts,
            runtime_version,
        )

    if status.state is RunState.FAILED:
        if run.state in {RunState.STARTING, RunState.RUNNING}:
            run.transition(RunState.FAILED, reason=_RUNTIME_FAILED_REASON)
        else:
            _orphan(run, _STATUS_UNAVAILABLE_REASON)
        return None

    if status.state is RunState.TIMED_OUT:
        if (
            run.state is RunState.RUNNING
            and await _cleanup_and_verify(
                adapter,
                run.runtime_ref,
                expected_state=RunState.TIMED_OUT,
            )
        ):
            run.transition(RunState.TIMED_OUT, reason=_TIMED_OUT_REASON)
        else:
            _orphan(run, _CLEANUP_UNVERIFIED_REASON)
        return None

    # CANCELLED, CANCEL_REQUESTED, and an active runtime all require a fresh
    # cancel/cleanup/status proof after restart.  ORPHANED cannot be repaired.
    if status.state is RunState.ORPHANED:
        _orphan(run, _CLEANUP_UNVERIFIED_REASON)
        return None

    if await _cleanup_and_verify(
        adapter,
        run.runtime_ref,
        expected_state=RunState.CANCELLED,
    ):
        if run.state is not RunState.CANCEL_REQUESTED:
            if run.state not in {
                RunState.CREATED,
                RunState.STARTING,
                RunState.RUNNING,
            }:
                _orphan(run, _CLEANUP_UNVERIFIED_REASON)
                return None
            run.transition(RunState.CANCEL_REQUESTED)
        run.transition(RunState.CANCELLED, reason=_CANCELLED_REASON)
        return _RecoveryOutputs(
            result=RunResult(
                run_id=run.id,
                status=RunState.CANCELLED,
                summary=_CANCELLED_SUMMARY,
            )
        )

    _orphan(run, _CLEANUP_UNVERIFIED_REASON)
    return None


async def _cleanup_and_verify(
    adapter: RuntimeAdapter,
    runtime_ref: str,
    *,
    expected_state: RunState,
) -> bool:
    """Run the restart cleanup proof without leaking adapter errors."""
    try:
        if not adapter.capabilities().cancel:
            return False
        target_setter = getattr(adapter, "set_cleanup_target", None)
        if callable(target_setter):
            target_setter(runtime_ref, expected_state)
        await adapter.cancel(runtime_ref)
        if not await adapter.cleanup(runtime_ref):
            return False
        post_cleanup = await adapter.status(runtime_ref)
    except asyncio.CancelledError:
        if _external_task_cancellation_requested():
            raise
        return False
    except Exception:
        return False
    return post_cleanup.state is expected_state


def _orphan(run: Run, reason: str) -> None:
    """Move any non-terminal Run through the legal fail-closed path."""
    if run.state in TERMINAL_STATES:
        return
    if run.state is not RunState.CANCEL_REQUESTED:
        run.transition(RunState.CANCEL_REQUESTED)
    run.transition(RunState.ORPHANED, reason=reason)
    run.result = None


def _mark_completed(run: Run) -> bool:
    """Advance only states for which adapter completion is not contradictory."""
    if run.state is RunState.STARTING:
        run.transition(RunState.RUNNING, reason=_COMPLETED_OBSERVED_REASON)
    elif run.state is RunState.RUNNING:
        pass
    else:
        _orphan(run, _CONFLICTING_CANCEL_REASON)
        return False
    run.transition(RunState.COMPLETED, reason=_COMPLETED_OBSERVED_REASON)
    return True


def _profile_matches_snapshot(profile, snapshot: RuntimeBindingSnapshot) -> bool:
    """Reject silent rebind when registry configuration differs from history."""
    return (
        profile.provider_id == snapshot.provider_id
        and profile.transport_kind is snapshot.transport_kind
        and profile.runtime_id == snapshot.runtime_id
        and profile.adapter_id == snapshot.adapter_id
        and profile.execution_target is snapshot.execution_target
        and profile.runtime_profile_ref == snapshot.runtime_profile_ref
        and profile.profile_revision == snapshot.profile_revision
        and profile.auth_ownership is snapshot.auth_ownership
        and profile.secret_ref_id == snapshot.secret_ref_id
        and profile.usage_visibility is snapshot.usage_visibility
    )


def _external_task_cancellation_requested() -> bool:
    """Distinguish task cancellation from an adapter-raised cancellation error."""
    task = asyncio.current_task()
    return task is not None and task.cancelling() > 0


def _build_completed_outputs(
    run: Run,
    binding: RuntimeBindingSnapshot,
    runtime_result: RuntimeResult,
    adapter_artifacts: tuple[Artifact, ...],
    runtime_version: str,
) -> _RecoveryOutputs:
    """Retain normalized adapter output after a public-safe boundary check."""
    safe_result = _normalize_runtime_result(run, runtime_result)
    safe_artifacts = _normalize_artifacts(run, adapter_artifacts)
    evidence = tuple(safe_result.evidence) + (
        Evidence(
            task_id=run.task_id,
            run_id=run.id,
            actor_id=_RECOVERY_EVIDENCE_ACTOR,
            source="runtime-adapter",
            type=EvidenceType.RUNTIME_EVIDENCE,
            status=EvidenceStatus.PASS,
            metadata={
                "reconciled_after_restart": True,
                "provider_id": binding.provider_id,
                "runtime_id": binding.runtime_id,
                "adapter_id": binding.adapter_id,
                "runtime_profile_ref": binding.runtime_profile_ref,
                "profile_revision": binding.profile_revision,
                "adapter_version": runtime_version,
            },
        ),
    )
    artifacts = tuple(safe_result.artifacts) + tuple(
        artifact
        for artifact in safe_artifacts
        if artifact.id not in {item.id for item in safe_result.artifacts}
    )
    result = RunResult(
        run_id=run.id,
        status=RunState.COMPLETED,
        summary=safe_result.summary,
        finding_ids=tuple(finding.id for finding in safe_result.findings),
        evidence_ids=tuple(item.id for item in evidence),
        artifact_ids=tuple(artifact.id for artifact in artifacts),
    )
    run.result = result
    return _RecoveryOutputs(
        result=result,
        findings=safe_result.findings,
        evidence=evidence,
        artifacts=artifacts,
    )


def _normalize_runtime_result(run: Run, runtime_result: RuntimeResult) -> RuntimeResult:
    """Keep only typed, Run-owned, public-safe normalized adapter outputs."""
    if not isinstance(runtime_result, RuntimeResult):
        return RuntimeResult(summary=_COMPLETED_SUMMARY)

    findings = tuple(
        replace(finding)
        for finding in runtime_result.findings
        if finding.task_id == run.task_id
        and finding.run_id == run.id
        and _public_safe_text(finding.title)
        and _public_safe_text(finding.description)
    )
    evidence = tuple(
        replace(evidence, metadata=dict(evidence.metadata))
        for evidence in runtime_result.evidence
        if evidence.task_id == run.task_id
        and evidence.run_id == run.id
        and _public_safe_text(evidence.actor_id)
        and _public_safe_text(evidence.source)
        and _public_safe_metadata(evidence.metadata)
    )
    artifacts = _normalize_artifacts(run, runtime_result.artifacts)
    return RuntimeResult(
        # RuntimeResult.summary is an arbitrary adapter string.  There is no
        # classification/secret proof in this frozen contract, so only the
        # Core-owned fixed summary is safe to persist during restart recovery.
        summary=_COMPLETED_SUMMARY,
        evidence=evidence,
        findings=findings,
        artifacts=artifacts,
    )


def _normalize_artifacts(run: Run, artifacts: tuple[Artifact, ...]) -> tuple[Artifact, ...]:
    """Retain only owned artifacts whose references contain no secret material."""
    normalized: list[Artifact] = []
    for artifact in artifacts:
        if not isinstance(artifact, Artifact):
            continue
        if artifact.task_id not in (None, run.task_id):
            continue
        if artifact.run_id not in (None, run.id):
            continue
        if not all(
            _public_safe_text(value)
            for value in (artifact.storage_ref, artifact.mime_type, artifact.source_type)
        ):
            continue
        normalized.append(
            replace(artifact, task_id=run.task_id, run_id=run.id)
        )
    return tuple(normalized)


def _public_safe_metadata(metadata: object) -> bool:
    if not isinstance(metadata, dict):
        return False
    return all(
        _public_safe_text(key) and _public_safe_text(value)
        for key, value in metadata.items()
    )


def _public_safe_text(value: object) -> bool:
    if not isinstance(value, str) or not value.strip() or len(value) > 4096:
        return False
    lowered = value.casefold()
    return not any(marker in lowered for marker in _SENSITIVE_MARKERS)


def _safe_adapter_version(value: object) -> str | None:
    """Allow only a bounded public adapter/version identity at the boundary."""
    if not isinstance(value, str) or len(value) > 128:
        return None
    if not _SAFE_ADAPTER_VERSION.fullmatch(value):
        return None
    return value
