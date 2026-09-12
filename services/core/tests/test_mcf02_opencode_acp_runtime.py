"""Deterministic fake-ACP tests; never live OpenCode compatibility evidence."""
from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from polynexus_core.domain.enums import EvidenceStatus, EvidenceType, ResumeMode, RunState
from polynexus_core.domain.models import ContextPackage, Project, Run, Task
from polynexus_core.execution_service import ExecutionService
from polynexus_core.persistence.models import Base
from polynexus_core.persistence.repository import (
    SqlContextPackageRepository,
    SqlProjectRepository,
    SqlRunRepository,
    SqlRuntimeBindingSnapshotRepository,
    SqlTaskRepository,
)
from polynexus_core.runtime.external_contracts import (
    MAX_FRAME_BYTES,
    ExternalContractError,
    build_controlled_execution_envelope,
    create_projected_staging,
)
from polynexus_core.runtime.opencode_acp import (
    AcpBoundaryError,
    OpenCodeAcpRuntimeAdapter,
    build_opencode_acp_descriptor,
    build_opencode_acp_profile,
)
from polynexus_core.runtime.contracts import RuntimeStatus
from polynexus_core.runtime.registry import RUNTIME_PROFILE_ENV, RuntimeRegistry
from polynexus_core.runtime.supervisor import RunSupervisor
from polynexus_core.workflows.loader import load_workflow_definition


ROOT = Path(__file__).resolve().parents[3]
SECRET = "Bearer FAKE_MCF02_COOKIE_TOKEN_API_KEY"


class FakeStdout:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[bytes | BaseException] = asyncio.Queue()

    async def readline(self) -> bytes:
        value = await self.queue.get()
        if isinstance(value, BaseException):
            raise value
        return value

    async def read(self, size: int = -1) -> bytes:
        del size
        return b""


class FakeStderr:
    def __init__(self, payload: bytes = b"") -> None:
        self.payload = payload

    async def readline(self) -> bytes:
        return b""

    async def read(self, size: int = -1) -> bytes:
        del size
        return self.payload


class FakeWriter:
    def __init__(self, process: "FakeProcess", mode: str) -> None:
        self.process = process
        self.mode = mode
        self.closed = False
        self.writes: list[dict[str, object]] = []
        self.prompt_started = asyncio.Event()

    def write(self, data: bytes) -> None:
        message = json.loads(data)
        self.writes.append(message)
        method = message["method"]
        if "id" not in message:
            return
        request_id = message["id"]
        if method == "initialize":
            if self.mode == "initialize-malformed":
                self.process.stdout.queue.put_nowait(b"not-json\n")
                return
            if self.mode == "initialize-version-mismatch":
                result = {"protocolVersion": 999, "agentCapabilities": {}}
            else:
                result = {"protocolVersion": 1, "agentCapabilities": {}}
        elif method == "session/new":
            if self.mode == "session-eof":
                self.process.stdout.queue.put_nowait(b"")
                return
            result = {"sessionId": f"vendor-session-{SECRET}"}
        elif method == "session/prompt":
            self.prompt_started.set()
            if self.mode == "malformed":
                self.process.stdout.queue.put_nowait(b"not-json\n")
                return
            if self.mode == "contamination":
                self.process.stdout.queue.put_nowait(b"OpenCode banner\n")
                return
            if self.mode == "oversize":
                self.process.stdout.queue.put_nowait(b"x" * (MAX_FRAME_BYTES + 1))
                return
            if self.mode == "eof":
                self.process.stdout.queue.put_nowait(b"")
                return
            if self.mode == "disconnect":
                self.process.stdout.queue.put_nowait(ConnectionError(SECRET))
                return
            if self.mode in {"timeout", "hold"}:
                return
            if self.mode == "error":
                self.process.stdout.queue.put_nowait(
                    json.dumps({"jsonrpc": "2.0", "id": request_id, "error": {"message": SECRET}}).encode() + b"\n"
                )
                return
            self.process.stdout.queue.put_nowait(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "method": "session/update",
                        "params": {"content": SECRET},
                    }
                ).encode()
                + b"\n"
            )
            result = dict(self.process.prompt_result)
        else:
            result = {}
        self.process.stdout.queue.put_nowait(
            json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}).encode() + b"\n"
        )

    async def drain(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        return None


class FakeProcess:
    def __init__(
        self,
        *,
        mode: str = "normal",
        stderr: bytes = b"",
        prompt_result: dict[str, object] | None = None,
    ) -> None:
        self.pid = 4242
        self.returncode: int | None = None
        self.stdout = FakeStdout()
        self.stderr = FakeStderr(stderr)
        self.prompt_result = prompt_result or {"output": "PASS", "artifacts": []}
        self.stdin = FakeWriter(self, mode)
        self.terminated = False
        self.killed = False

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    async def wait(self) -> int:
        while self.returncode is None:
            await asyncio.sleep(0)
        return self.returncode


def inputs() -> tuple[Task, ContextPackage]:
    project = Project(name="MCF02 ACP")
    context = ContextPackage(project_id=project.id, version=1, source_refs=("fixture:mcf02",))
    task = Task(
        project_id=project.id,
        title="Perform projected review",
        workflow_id="review-minimal",
        workflow_version=1,
        context_package_id=context.id,
    )
    return task, context


async def version_probe(_path: Path, _environment) -> str:
    return "1.0.0"


def build_adapter(
    tmp_path: Path,
    *,
    mode: str = "normal",
    approved: bool = True,
    cleanup_failure: str | None = None,
    stderr: bytes = b"",
    prompt_result: dict[str, object] | None = None,
    timeout: float = 1.0,
):
    task, context = inputs()
    staging = create_projected_staging(tmp_path, context)
    executable = tmp_path / "opencode-bin"
    executable.write_bytes(b"opencode executable v1")
    envelope = build_controlled_execution_envelope(
        staging_root=staging,
        executable_path=executable,
        observed_runtime_version="1.0.0",
    )
    descriptor = build_opencode_acp_descriptor(envelope)
    process = FakeProcess(mode=mode, stderr=stderr, prompt_result=prompt_result)
    launch_observation: dict[str, object] = {}

    async def launcher(args, cwd, environment):
        launch_observation.update(args=args, cwd=cwd, environment=dict(environment))
        return process

    async def cleanup(proc, _timeout):
        assert proc is process
        if cleanup_failure is None:
            process.returncode = 0
            process.stdout.queue.put_nowait(b"")
            return True
        if cleanup_failure == "child-remains":
            # A helper claiming success cannot override a live root process.
            return True
        if cleanup_failure == "descendant-remains":
            # Root exit alone is insufficient when tree verification fails.
            process.returncode = 0
            return False
        if cleanup_failure == "forced-kill-failure":
            process.terminate()
            process.kill()
            return False
        return False

    adapter = OpenCodeAcpRuntimeAdapter(
        staging_root=staging,
        envelope=envelope,
        descriptor=descriptor,
        provider_model_approved=approved,
        operation_timeout=timeout,
        process_launcher=launcher,
        version_probe=version_probe,
        tree_cleanup=cleanup,
    )
    profile = build_opencode_acp_profile()
    snapshot = profile.bind(
        run_id="run-mcf02-acp",
        resolved_at=datetime.now(timezone.utc),
        adapter_version=descriptor.binding_version_token,
    )
    adapter.bind_core_run(snapshot)
    return adapter, task, context, staging, executable, process, launch_observation


def create(adapter: OpenCodeAcpRuntimeAdapter, context: ContextPackage) -> str:
    return asyncio.run(adapter.create_run(context))


def test_fake_acp_create_dispatch_stream_result_and_candidate_evidence(tmp_path: Path) -> None:
    adapter, task, context, staging, _, process, launch = build_adapter(tmp_path)
    runtime_ref = create(adapter, context)
    asyncio.run(adapter.submit(runtime_ref, task))
    assert asyncio.run(adapter.status(runtime_ref)).state is RunState.COMPLETED
    result = asyncio.run(adapter.result(runtime_ref))
    assert result.summary == "External runtime returned candidate output"
    assert len(result.evidence) == 1
    assert result.evidence[0].type is EvidenceType.AI_OPINION
    assert result.evidence[0].status is EvidenceStatus.OBSERVED
    assert "PASS" not in repr(result)
    assert SECRET not in repr(result)
    assert adapter.observed_events(runtime_ref) == ({"method": "session/update", "observed": True},)
    methods = [item["method"] for item in process.stdin.writes]
    assert methods == ["initialize", "session/new", "session/prompt"]
    assert process.stdin.writes[0]["params"]["clientCapabilities"] == {}
    assert launch["args"] == (str(adapter.envelope.executable_identity.resolved_path), "acp")
    assert launch["cwd"] == staging
    environment = launch["environment"]
    assert "HOME" not in environment and "USERPROFILE" not in environment
    assert process.returncode == 0


def test_session_handle_binds_core_run_project_binding_and_envelope_without_raw_vendor_id(tmp_path: Path) -> None:
    adapter, _, context, _, _, _, _ = build_adapter(tmp_path)
    runtime_ref = create(adapter, context)
    handle = adapter.session_handle(runtime_ref)
    assert handle.created_by_run_id == "run-mcf02-acp"
    assert len(handle.project_scope_digest) == 64
    assert len(handle.binding_fingerprint) == 64
    assert handle.execution_envelope_fingerprint == adapter.envelope.execution_envelope_ref
    assert SECRET not in repr(handle)


def test_provider_egress_requires_matching_human_approval(tmp_path: Path) -> None:
    adapter, task, context, _, _, _, _ = build_adapter(tmp_path, approved=False)
    runtime_ref = create(adapter, context)
    with pytest.raises(AcpBoundaryError):
        asyncio.run(adapter.submit(runtime_ref, task))
    assert asyncio.run(adapter.status(runtime_ref)).state is RunState.CREATED
    asyncio.run(adapter.cancel(runtime_ref))
    assert asyncio.run(adapter.cleanup(runtime_ref)) is True


@pytest.mark.parametrize("mode", ["malformed", "contamination", "oversize", "eof", "disconnect", "error"])
def test_malformed_contaminated_oversize_eof_disconnect_and_error_frames_fail_closed(
    tmp_path: Path, mode: str
) -> None:
    adapter, task, context, _, _, _, _ = build_adapter(tmp_path, mode=mode)
    runtime_ref = create(adapter, context)
    with pytest.raises(AcpBoundaryError, match="boundary failed") as caught:
        asyncio.run(adapter.submit(runtime_ref, task))
    assert SECRET not in str(caught.value)
    assert asyncio.run(adapter.status(runtime_ref)).state is RunState.FAILED
    assert asyncio.run(adapter.cleanup(runtime_ref)) is True


def test_protocol_timeout_is_bounded_and_sanitized(tmp_path: Path) -> None:
    adapter, task, context, _, _, _, _ = build_adapter(tmp_path, mode="timeout", timeout=0.01)
    runtime_ref = create(adapter, context)
    with pytest.raises(AcpBoundaryError, match="boundary failed"):
        asyncio.run(adapter.submit(runtime_ref, task))
    assert asyncio.run(adapter.cleanup(runtime_ref)) is True


@pytest.mark.parametrize(
    "mode", ["initialize-malformed", "initialize-version-mismatch", "session-eof"]
)
def test_initialization_failure_retains_safe_ref_for_supervisor_cleanup(
    tmp_path: Path, mode: str
) -> None:
    adapter, task, context, _, _, _, _ = build_adapter(tmp_path, mode=mode)
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    run = Run(
        id="run-mcf02-acp",
        task_id=task.id,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=context.id,
    )
    run.transition(RunState.STARTING)
    execution = asyncio.run(
        RunSupervisor(adapter).execute_claimed_run(run, task, context, workflow)
    )
    assert execution.run.runtime_ref is not None
    assert execution.run.state is RunState.FAILED


def test_initialization_cleanup_uncertainty_is_orphaned(tmp_path: Path) -> None:
    adapter, task, context, _, _, process, _ = build_adapter(
        tmp_path,
        mode="initialize-version-mismatch",
        cleanup_failure="child-remains",
    )
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    run = Run(
        id="run-mcf02-acp",
        task_id=task.id,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=context.id,
    )
    run.transition(RunState.STARTING)
    execution = asyncio.run(
        RunSupervisor(adapter).execute_claimed_run(run, task, context, workflow)
    )
    assert process.returncode is None
    assert execution.run.state is RunState.ORPHANED


def test_raw_stderr_secret_is_drained_not_persisted(tmp_path: Path) -> None:
    adapter, task, context, _, _, _, _ = build_adapter(tmp_path, stderr=SECRET.encode())
    runtime_ref = create(adapter, context)
    asyncio.run(adapter.submit(runtime_ref, task))
    result = asyncio.run(adapter.result(runtime_ref))
    assert SECRET not in repr(result)
    assert SECRET not in repr(adapter.observed_events(runtime_ref))


def test_cancel_before_dispatch_and_duplicate_cancel_verify_cleanup(tmp_path: Path) -> None:
    adapter, _, context, _, _, _, _ = build_adapter(tmp_path)
    runtime_ref = create(adapter, context)
    asyncio.run(adapter.cancel(runtime_ref))
    asyncio.run(adapter.cancel(runtime_ref))
    assert asyncio.run(adapter.cleanup(runtime_ref)) is True
    assert asyncio.run(adapter.status(runtime_ref)).state is RunState.CANCELLED


def test_cancel_during_stream_interrupts_and_cleans_owned_process(tmp_path: Path) -> None:
    async def scenario() -> None:
        adapter, task, context, _, _, process, _ = build_adapter(tmp_path, mode="hold", timeout=1.0)
        runtime_ref = await adapter.create_run(context)
        submitting = asyncio.create_task(adapter.submit(runtime_ref, task))
        await process.stdin.prompt_started.wait()
        await adapter.cancel(runtime_ref)
        assert await adapter.cleanup(runtime_ref) is True
        with pytest.raises(AcpBoundaryError):
            await submitting
        assert (await adapter.status(runtime_ref)).state is RunState.CANCELLED

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "failure_kind",
    ["child-remains", "descendant-remains", "cleanup-false", "forced-kill-failure"],
)
def test_cleanup_uncertainty_is_orphaned_by_run_supervisor(
    tmp_path: Path, failure_kind: str
) -> None:
    adapter, task, context, _, _, process, _ = build_adapter(
        tmp_path, cleanup_failure=failure_kind
    )
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    supervisor = RunSupervisor(adapter)
    session = asyncio.run(supervisor.start(task, context, workflow))
    execution = asyncio.run(supervisor.cancel(session))
    assert execution.run.state is RunState.ORPHANED
    assert execution.run.events[-1].to_state is RunState.ORPHANED
    if failure_kind == "child-remains":
        assert process.returncode is None
    elif failure_kind == "descendant-remains":
        assert process.returncode == 0
    elif failure_kind == "forced-kill-failure":
        assert process.terminated and process.killed


def test_cleanup_success_with_status_still_running_is_orphaned(tmp_path: Path) -> None:
    adapter, task, context, _, _, _, _ = build_adapter(tmp_path)
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    session = asyncio.run(RunSupervisor(adapter).start(task, context, workflow))

    async def lying_cleanup(_runtime_ref: str) -> bool:
        return True

    async def still_running(_runtime_ref: str) -> RuntimeStatus:
        return RuntimeStatus(state=RunState.RUNNING)

    adapter.cleanup = lying_cleanup  # type: ignore[method-assign]
    adapter.status = still_running  # type: ignore[method-assign]
    execution = asyncio.run(RunSupervisor(adapter).cancel(session))
    assert execution.run.state is RunState.ORPHANED


def test_resume_mode_is_none_and_native_resume_rejected(tmp_path: Path) -> None:
    adapter, _, context, _, _, _, _ = build_adapter(tmp_path)
    runtime_ref = create(adapter, context)
    assert adapter.capabilities().resume is ResumeMode.NONE
    with pytest.raises(NotImplementedError):
        asyncio.run(adapter.resume(runtime_ref, "checkpoint"))


@pytest.mark.parametrize("drift", ["config", "executable"])
def test_config_and_executable_drift_reject_dispatch_and_resume(tmp_path: Path, drift: str) -> None:
    adapter, task, context, staging, executable, _, _ = build_adapter(tmp_path)
    runtime_ref = create(adapter, context)
    if drift == "config":
        (staging / "context.json").write_text('{"drift":true}', encoding="utf-8")
    else:
        executable.write_bytes(b"replaced executable")
    assert asyncio.run(adapter.readiness()) is False
    with pytest.raises(ExternalContractError):
        asyncio.run(adapter.submit(runtime_ref, task))
    with pytest.raises(NotImplementedError):
        asyncio.run(adapter.resume(runtime_ref))


def test_project_drift_is_rejected(tmp_path: Path) -> None:
    adapter, task, context, _, _, _, _ = build_adapter(tmp_path)
    runtime_ref = create(adapter, context)
    other = Project(name="other")
    wrong_task = Task(
        project_id=other.id,
        title=task.title,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=context.id,
    )
    with pytest.raises(AcpBoundaryError):
        asyncio.run(adapter.submit(runtime_ref, wrong_task))


def test_missing_session_rejected_without_echo(tmp_path: Path) -> None:
    adapter, _, _, _, _, _, _ = build_adapter(tmp_path)
    poisoned = f"missing-{SECRET}"
    with pytest.raises(KeyError) as caught:
        asyncio.run(adapter.status(poisoned))
    assert SECRET not in str(caught.value)


def test_artifact_import_hash_size_provenance_and_spoofed_ids(tmp_path: Path) -> None:
    payload = b"candidate output"
    artifact_claim = {
        "path": "output.bin",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size": len(payload),
    }
    response = {
        "output": "VERIFIED CERTIFIED PASS",
        "artifacts": [artifact_claim],
        "artifactId": "spoofed-artifact",
        "evidenceId": "spoofed-evidence",
    }
    adapter, task, context, staging, _, _, _ = build_adapter(tmp_path, prompt_result=response)
    runtime_ref = create(adapter, context)
    asyncio.run(adapter.submit(runtime_ref, task))
    (staging / "output.bin").write_bytes(payload)
    result = asyncio.run(adapter.result(runtime_ref))
    assert result.summary == "External runtime returned candidate output"
    assert result.evidence[0].type is EvidenceType.AI_OPINION
    assert result.evidence[0].status is EvidenceStatus.OBSERVED
    assert result.evidence[0].metadata["external_session_ref"].startswith("session-")
    assert result.evidence[0].metadata["sanitization"] == "HASH_ONLY_CANDIDATE_OUTPUT"
    assert result.evidence[0].metadata["agent_extension_egress"] == "DENIED"
    assert result.artifacts[0].sha256 == artifact_claim["sha256"]
    assert result.artifacts[0].project_id == context.project_id
    assert "spoofed" not in repr(result)


@pytest.mark.parametrize(
    "artifact",
    [
        {"path": "output.bin", "sha256": "0" * 64, "size": 1},
        {"path": "../outside.bin", "sha256": "0" * 64, "size": 1},
        {"path": "output.bin", "sha256": "0" * 64, "size": 1, "project_id": "other"},
    ],
)
def test_artifact_hash_cross_project_metadata_and_path_escape_fail_closed(
    tmp_path: Path, artifact: dict[str, object]
) -> None:
    adapter, task, context, staging, _, _, _ = build_adapter(
        tmp_path, prompt_result={"output": "ok", "artifacts": [artifact]}
    )
    (tmp_path / "outside.bin").write_bytes(b"x")
    runtime_ref = create(adapter, context)
    asyncio.run(adapter.submit(runtime_ref, task))
    (staging / "output.bin").write_bytes(b"x")
    with pytest.raises(AcpBoundaryError):
        asyncio.run(adapter.result(runtime_ref))


def test_fake_acp_is_not_live_compatibility_or_certification(tmp_path: Path) -> None:
    adapter, _, _, _, _, _, _ = build_adapter(tmp_path)
    assert adapter.version_info().startswith("opencode-acp-adapter/")
    assert "live" not in adapter.version_info().lower()
    assert "certified" not in adapter.version_info().lower()
    assert "production" not in adapter.version_info().lower()


def test_execution_service_commits_external_binding_before_factory_and_keeps_supervisor_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = create_engine(f"sqlite:///{tmp_path / 'mcf02.db'}")
    Base.metadata.create_all(database)
    try:
        task, context = inputs()
        project = Project(id=context.project_id, name="MCF02 Core path")
        run = Run(
            task_id=task.id,
            workflow_id=task.workflow_id,
            workflow_version=task.workflow_version,
            context_package_id=context.id,
        )
        staging = create_projected_staging(tmp_path, context)
        executable = tmp_path / "opencode-core-path-bin"
        executable.write_bytes(b"opencode executable v1")
        envelope = build_controlled_execution_envelope(
            staging_root=staging,
            executable_path=executable,
            observed_runtime_version="1.0.0",
        )
        descriptor = build_opencode_acp_descriptor(envelope)
        profile = build_opencode_acp_profile()
        current_run_id = run.id
        factory_observations: list[str] = []

        def factory() -> OpenCodeAcpRuntimeAdapter:
            # A separate connection proves the immutable binding was committed
            # before the external process adapter could be constructed.
            with Session(database) as observer:
                snapshot = SqlRuntimeBindingSnapshotRepository(observer).get_by_run(
                    current_run_id
                )
                assert snapshot is not None
                assert snapshot.adapter_version == descriptor.binding_version_token
                factory_observations.append(snapshot.run_id)
            process = FakeProcess()

            async def launcher(args, cwd, environment):
                del args, cwd, environment
                return process

            async def cleanup(proc, _timeout):
                assert proc is process
                process.returncode = 0
                process.stdout.queue.put_nowait(b"")
                return True

            return OpenCodeAcpRuntimeAdapter(
                staging_root=staging,
                envelope=envelope,
                descriptor=descriptor,
                provider_model_approved=True,
                process_launcher=launcher,
                version_probe=version_probe,
                tree_cleanup=cleanup,
            )

        registry = RuntimeRegistry()
        registry.register_external(profile, factory, descriptor, envelope)
        with Session(database) as session:
            for repository, entity in (
                (SqlProjectRepository, project),
                (SqlContextPackageRepository, context),
                (SqlTaskRepository, task),
                (SqlRunRepository, run),
            ):
                repository(session).add(entity)
            session.commit()
            monkeypatch.setenv(RUNTIME_PROFILE_ENV, profile.runtime_profile_ref)
            execution = asyncio.run(
                ExecutionService(session, registry).execute_existing_run(run.id)
            )
            assert execution.run.state is RunState.COMPLETED
            assert execution.run.runtime_ref.startswith("opencode-acp:")
            assert factory_observations == [run.id]
            snapshot = SqlRuntimeBindingSnapshotRepository(session).get_by_run(run.id)
            assert snapshot is not None
            assert snapshot.adapter_version == descriptor.binding_version_token
            assert [event.to_state for event in execution.run.events][-1] is RunState.COMPLETED
    finally:
        database.dispose()
