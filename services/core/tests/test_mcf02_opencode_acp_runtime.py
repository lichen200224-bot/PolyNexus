"""Deterministic fake-ACP tests; never live OpenCode compatibility evidence."""
from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timezone, timedelta
from dataclasses import replace
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
    PreparedExternalRun,
    ExternalRuntimeDefinition,
    ExternalContractError,
    build_controlled_execution_envelope,
    create_projected_staging,
)
from polynexus_core.runtime.opencode_acp import (
    AcpBoundaryError,
    controlled_config,
    normalized_config_digest,
    configuration_sources_clear,
    OpenCodeAcpRuntimeAdapter,
    build_opencode_acp_descriptor,
    build_opencode_acp_profile,
)
from polynexus_core.runtime.contracts import RuntimeStatus
from polynexus_core.runtime.registry import RUNTIME_PROFILE_ENV, RuntimeRegistry
from polynexus_core.runtime.routing_policy import (
    RunScopedPolicyAuthorization, DataClassification, ExecutionMode, DestinationTrust,
)
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


async def config_probe(_path, _cwd, _environment):
    return json.dumps(controlled_config()).encode()


def policy_for(prepared):
    return RunScopedPolicyAuthorization.issue(
        run_id=prepared.run_id, task_id=prepared.task_id, project_id=prepared.project_id,
        destination_ref="opencode.provider", envelope_ref=prepared.envelope.execution_envelope_ref,
        classifications=(DataClassification.PUBLIC,), execution_mode=ExecutionMode.STANDARD,
        destination_trust=DestinationTrust.TRUSTED_EXTERNAL,
    )


async def version_probe(_path: Path, _cwd: Path, _environment) -> str:
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
    (staging / ".polynexus-run").write_text("run-mcf02-acp", encoding="utf-8")
    executable = tmp_path / "opencode-bin"
    executable.write_bytes(b"opencode executable v1")
    envelope = build_controlled_execution_envelope(
        staging_root=staging,
        executable_path=executable,
        observed_runtime_version="1.0.0",
        effective_config_digest=normalized_config_digest(json.dumps(controlled_config()).encode()),
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

    prepared = PreparedExternalRun(
        "run-mcf02-acp", task.id, task.project_id, context.id, staging, envelope, descriptor
    )
    adapter = OpenCodeAcpRuntimeAdapter(
        staging_root=staging,
        envelope=envelope,
        descriptor=descriptor,
        prepared=prepared,
        authorization=policy_for(prepared) if approved else None,
        config_probe=config_probe,
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
    assert environment["HOME"] == str(staging / ".runtime-home")
    assert environment["USERPROFILE"] == environment["HOME"]
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
    run = Run(id="run-mcf02-acp", task_id=task.id, workflow_id=task.workflow_id,
              workflow_version=1, context_package_id=context.id)
    run.transition(RunState.STARTING)
    execution = asyncio.run(supervisor.execute_claimed_run(run, task, context, workflow))
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
    assert adapter.capabilities().permission_requests is False
    assert "live" not in adapter.version_info().lower()
    assert "certified" not in adapter.version_info().lower()
    assert "production" not in adapter.version_info().lower()


@pytest.mark.parametrize("same_project", [False, True])
def test_same_profile_two_runs_two_projects_have_durable_isolated_envelopes(tmp_path, monkeypatch, same_project):
    database = create_engine(f"sqlite:///{tmp_path / 'mcf02.db'}")
    Base.metadata.create_all(database)
    prepared_runs = []
    factories = []
    executable = tmp_path / "opencode-core-path-bin"
    executable.write_bytes(b"explicit executable")
    from polynexus_core.runtime.external_contracts import build_executable_identity
    # Template sentinel cannot be executed or mistaken for a Run envelope.
    template_root = create_projected_staging(tmp_path, inputs()[1])
    template_envelope = build_controlled_execution_envelope(
        staging_root=template_root, executable_path=executable, observed_runtime_version="1.0.0"
    )
    template = replace(build_opencode_acp_descriptor(template_envelope), execution_envelope_ref="0" * 64)
    definition = ExternalRuntimeDefinition(
        template, build_executable_identity(executable, "1.0.0"), tmp_path,
        normalized_config_digest(json.dumps(controlled_config()).encode()),
    )

    def factory(prepared):
        with Session(database) as observer:
            binding = SqlRuntimeBindingSnapshotRepository(observer).get_by_run(prepared.run_id)
            assert binding is not None
            prepared.validate(binding)
            factories.append(binding)
        process = FakeProcess()
        async def launch(args, cwd, environment):
            assert cwd == prepared.staging_root
            return process
        async def cleanup(proc, timeout):
            process.returncode = 0
            return True
        prepared_runs.append(prepared)
        return OpenCodeAcpRuntimeAdapter(
            staging_root=prepared.staging_root, envelope=prepared.envelope,
            descriptor=prepared.descriptor, prepared=prepared, authorization=policy_for(prepared),
            process_launcher=launch, version_probe=version_probe, config_probe=config_probe,
            tree_cleanup=cleanup,
        )

    registry = RuntimeRegistry()
    profile = build_opencode_acp_profile()
    registry.register_external(profile, factory, definition)
    try:
        with Session(database) as session:
            for _ in range(2):
                task, context = inputs()
                if same_project and prepared_runs:
                    context = replace(context, project_id=prepared_runs[0].project_id)
                    task = replace(task, project_id=context.project_id)
                project = Project(id=context.project_id, name="isolated")
                run = Run(task_id=task.id, workflow_id=task.workflow_id,
                          workflow_version=1, context_package_id=context.id)
                for repo, entity in ((SqlProjectRepository, project),
                                     (SqlContextPackageRepository, context),
                                     (SqlTaskRepository, task), (SqlRunRepository, run)):
                    if repo is SqlProjectRepository and same_project and prepared_runs:
                        continue
                    repo(session).add(entity)
                session.commit()
                monkeypatch.setenv(RUNTIME_PROFILE_ENV, profile.runtime_profile_ref)
                result = asyncio.run(ExecutionService(session, registry).execute_existing_run(run.id))
                assert result.run.state is RunState.COMPLETED
        a, b = prepared_runs
        assert a.staging_root != b.staging_root
        assert a.envelope.execution_envelope_ref != b.envelope.execution_envelope_ref
        assert (a.project_id == b.project_id) is same_project
        assert a.context_id not in (b.staging_root / "context.json").read_text()
        (a.staging_root / "private-artifact").write_text("run a only")
        assert not (b.staging_root / "private-artifact").exists()
        with pytest.raises(ExternalContractError):
            replace(b, staging_root=a.staging_root, envelope=a.envelope).validate(factories[1])
        assert not hasattr(registry, "_external_envelopes")
    finally:
        database.dispose()


@pytest.mark.parametrize("field,value", [
    ("plugin", ["npm:unapproved"]),
    ("plugin", ["file:///global/plugins/evil.js"]),
    ("mcp", {"global": {"type": "local", "command": ["evil"]}}),
    ("mcp", {"remote": {"type": "remote", "url": "https://invalid.example"}}),
    ("permission", {"*": "allow"}),
    ("permission", {"*": "deny", "external_directory": "allow"}),
    ("agent", {"build": {"permission": {"*": "allow"}}}),
    ("skills", {"urls": ["https://invalid.example/catalog"]}),
    ("autoApprove", True),
    ("managed", {"permission": "allow"}),
    ("remote", {"url": "https://invalid.example/config"}),
])
def test_final_resolver_expansion_denies_readiness_and_launch(tmp_path, field, value):
    adapter, task, context, _, _, _, launch = build_adapter(tmp_path)
    runtime_ref = create(adapter, context)
    effective = controlled_config()
    effective[field] = value
    async def injected(path, cwd, env):
        return json.dumps(effective).encode()
    adapter._config_probe = injected
    assert asyncio.run(adapter.readiness()) is False
    with pytest.raises(AcpBoundaryError):
        asyncio.run(adapter.submit(runtime_ref, task))
    assert launch == {}


@pytest.mark.parametrize("raw", [b"{}", b"not-json", b'{"permission":{},"permission":{}}', b"x" * (MAX_FRAME_BYTES + 1)], ids=["missing", "malformed", "duplicate", "oversize"])
def test_unparseable_or_incomplete_effective_config_is_not_safe(tmp_path, raw):
    adapter, _, _, _, _, _, _ = build_adapter(tmp_path)
    async def invalid(*args):
        return raw
    adapter._config_probe = invalid
    assert asyncio.run(adapter.readiness()) is False


@pytest.mark.parametrize("source", ["global", "global-plugin", "global-mcp", "managed", "project", "remote-auth"])
def test_source_inventory_rejects_expansion_before_resolver(tmp_path, monkeypatch, source):
    import polynexus_core.runtime.opencode_acp as module
    adapter, _, _, staging, _, _, _ = build_adapter(tmp_path)
    monkeypatch.setattr(module.sys, "platform", "win32")
    managed_parent = tmp_path / "program-data"
    managed_parent.mkdir()
    monkeypatch.setenv("ProgramData", str(managed_parent))
    env = adapter._controlled_environment()
    assert configuration_sources_clear(staging, env)
    targets = {
        "global": staging / ".runtime-home/config/opencode/opencode.json",
        "global-plugin": staging / ".runtime-home/config/opencode/plugins/evil.js",
        "global-mcp": staging / ".runtime-home/config/opencode/mcp.json",
        "managed": managed_parent / "opencode/opencode.json",
        "project": tmp_path / "opencode.json",
        "remote-auth": staging / ".runtime-home/data/opencode/auth.json",
    }
    target = targets[source]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}")
    assert configuration_sources_clear(staging, env) is False


@pytest.mark.parametrize("mismatch", ["run_id", "task_id", "project_id", "destination_ref", "envelope_ref", "missing-ref", "expired", "boolean", "human-required"])
def test_policy_authorization_is_run_scoped_and_never_infers_human_approval(tmp_path, mismatch):
    adapter, task, context, _, _, _, launch = build_adapter(tmp_path)
    ref = create(adapter, context)
    authorization = adapter._authorization
    if mismatch == "boolean":
        authorization = True
    elif mismatch == "missing-ref":
        authorization = replace(authorization, policy_decision_ref="")
    elif mismatch == "expired":
        authorization = replace(authorization, expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
        authorization = replace(authorization, policy_decision_ref=authorization.reference())
    elif mismatch == "human-required":
        authorization = replace(authorization, classifications=(DataClassification.CONFIDENTIAL,))
        authorization = replace(authorization, policy_decision_ref=authorization.reference())
    else:
        authorization = replace(authorization, **{mismatch: "other"})
        authorization = replace(authorization, policy_decision_ref=authorization.reference())
    adapter._authorization = authorization
    with pytest.raises(AcpBoundaryError):
        asyncio.run(adapter.submit(ref, task))
    assert launch == {}


@pytest.mark.parametrize("params", [
    {"sessionId": "current", "options": [{"kind": "allow_once"}]},
    {"sessionId": "current", "options": [{"kind": "reject_once"}]},
    {"sessionId": "stale", "options": []},
    None,
])
def test_option_b_incoming_permission_request_never_becomes_response(tmp_path, params):
    adapter, task, context, _, _, process, _ = build_adapter(tmp_path)
    ref = create(adapter, context)
    original = process.stdin.write
    def incoming(data):
        message = json.loads(data)
        if message.get("method") == "session/prompt":
            process.stdout.queue.put_nowait(json.dumps({
                "jsonrpc": "2.0", "id": message["id"],
                "method": "session/request_permission", "params": params,
                "result": {"output": "PASS"},
            }).encode() + b"\n")
        else:
            original(data)
    process.stdin.write = incoming
    assert adapter.capabilities().permission_requests is False
    with pytest.raises(AcpBoundaryError):
        asyncio.run(adapter.submit(ref, task))
    assert asyncio.run(adapter.cleanup(ref)) is True


def test_artifact_changed_during_process_cleanup_rejects_original_claim(tmp_path):
    payload = b"before"
    claim = {"path": "out.bin", "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    adapter, task, context, staging, _, process, _ = build_adapter(
        tmp_path, prompt_result={"output": "ok", "artifacts": [claim]}
    )
    ref = create(adapter, context)
    async def modifying_cleanup(proc, timeout):
        (staging / "out.bin").write_bytes(b"after!")
        process.returncode = 0
        return True
    adapter._tree_cleanup = modifying_cleanup
    asyncio.run(adapter.submit(ref, task))
    with pytest.raises(AcpBoundaryError):
        asyncio.run(adapter.result(ref))


def test_imported_artifact_storage_is_core_snapshot_not_staging(tmp_path):
    payload = b"candidate"
    claim = {"path": "out.bin", "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    adapter, task, context, staging, _, process, _ = build_adapter(
        tmp_path, prompt_result={"output": "ok", "artifacts": [claim]}
    )
    ref = create(adapter, context)
    asyncio.run(adapter.submit(ref, task))
    assert process.returncode == 0
    (staging / "out.bin").write_bytes(payload)
    result = asyncio.run(adapter.result(ref))
    stored = Path(result.artifacts[0].storage_ref)
    assert staging not in stored.parents
    (staging / "out.bin").write_bytes(b"later overwrite")
    assert stored.read_bytes() == payload
    assert hashlib.sha256(stored.read_bytes()).hexdigest() == result.artifacts[0].sha256
    assert result.evidence[0].metadata["provider_model_egress"] == "CORE_POLICY_ALLOWED"
    assert result.evidence[0].metadata["policy_decision_ref"].startswith("policy-")
    assert "HUMAN_APPROVED" not in repr(result)


def test_default_resolver_uses_bound_binary_and_identical_cwd_environment(tmp_path, monkeypatch):
    import polynexus_core.runtime.opencode_acp as module
    adapter, _, _, staging, executable, _, _ = build_adapter(tmp_path)
    observed = []
    class ProbeStream:
        def __init__(self, value):
            self.value = value
        async def read(self, size):
            value, self.value = self.value[:min(size, 7)], self.value[min(size, 7):]
            return value
    class ProbeProcess:
        returncode = 0
        stdout = ProbeStream(json.dumps(controlled_config()).encode())
        stderr = ProbeStream(b"synthetic secret discarded")
        async def wait(self):
            return 0
    async def launcher(args, cwd, environment):
        observed.append((args, cwd, environment))
        return ProbeProcess()
    monkeypatch.setattr(module, "_default_launcher", launcher)
    monkeypatch.setattr(module, "configuration_sources_clear", lambda cwd, env: True)
    environment = adapter._controlled_environment()
    raw = asyncio.run(module._default_config_probe(executable, staging, environment))
    assert observed == [((str(executable), "debug", "config"), staging, environment)]
    assert normalized_config_digest(raw) == adapter.envelope.effective_runtime_configuration_fingerprint


def test_unknown_source_inventory_does_not_launch_resolver(tmp_path, monkeypatch):
    import polynexus_core.runtime.opencode_acp as module
    adapter, _, _, staging, executable, _, _ = build_adapter(tmp_path)
    calls = []
    async def launcher(*args):
        calls.append(args)
        raise AssertionError("must not launch")
    monkeypatch.setattr(module, "_default_launcher", launcher)
    monkeypatch.setattr(module, "configuration_sources_clear", lambda cwd, env: False)
    with pytest.raises(AcpBoundaryError):
        asyncio.run(module._default_config_probe(executable, staging, adapter._controlled_environment()))
    assert calls == []


def test_artifact_mutation_after_first_read_is_rejected(tmp_path, monkeypatch):
    payload = b"original"
    claim = {"path": "out.bin", "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    adapter, task, context, staging, _, _, _ = build_adapter(
        tmp_path, prompt_result={"output": "ok", "artifacts": [claim]}
    )
    ref = create(adapter, context)
    asyncio.run(adapter.submit(ref, task))
    path = staging / "out.bin"
    path.write_bytes(payload)
    original = Path.read_bytes
    changed = []
    def racing_read(self):
        data = original(self)
        if self == path and not changed:
            changed.append(True)
            self.write_bytes(b"modified")
        return data
    monkeypatch.setattr(Path, "read_bytes", racing_read)
    with pytest.raises(AcpBoundaryError):
        asyncio.run(adapter.result(ref))
