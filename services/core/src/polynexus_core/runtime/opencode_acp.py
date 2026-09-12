"""OpenCode ACP v1 external runtime adapter (MCF-02-I01).

This is intentionally separate from the deterministic ``opencode.py``
conformance adapter.  It launches one explicitly configured, preinstalled
``opencode acp`` child inside a Core-created PROJECTED_STAGING workspace.
Fake ACP tests prove this adapter boundary only; they are not live-vendor or
production certification evidence.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import signal
import subprocess
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from polynexus_core.domain.enums import (
    ArtifactType,
    AuthOwnership,
    EvidenceStatus,
    EvidenceType,
    ExecutionTarget,
    ResumeMode,
    RunState,
    TransportKind,
    UsageVisibility,
)
from polynexus_core.domain.models import Artifact, ContextPackage, Evidence, Task
from polynexus_core.domain.runtime_binding import RuntimeBindingSnapshot, RuntimeProfile
from polynexus_core.runtime.contracts import RuntimeCapabilities, RuntimeResult, RuntimeStatus
from polynexus_core.runtime.external_contracts import (
    MAX_FRAME_BYTES,
    MAX_STAGING_FILE_BYTES,
    ControlledExecutionEnvelope,
    EgressChannel,
    EgressDeclaration,
    EgressDisposition,
    ExternalContractError,
    ExternalRuntimeDescriptor,
    ExternalSessionHandle,
    LaunchMode,
    ProtocolKind,
    binding_fingerprint,
    is_link_or_junction,
    project_scope_digest,
    validate_current_envelope,
)
from polynexus_core.runtime.routing_policy import evaluate_external_egress


_ADAPTER_VERSION = "opencode-acp-adapter/0.1"
_SAFE_FAILURE = "OpenCode ACP runtime boundary failed"
_SAFE_RESULT = "External runtime returned candidate output"
_NO_RESUME = "OpenCode ACP native resume is not implemented"
_MAX_EVENTS = 1024
_MAX_ARTIFACTS = 64


class AcpBoundaryError(RuntimeError):
    """Fixed-message ACP transport failure; raw output is never included."""


class _Stream(Protocol):
    async def readline(self) -> bytes: ...
    async def read(self, size: int = -1) -> bytes: ...


class _Writer(Protocol):
    def write(self, data: bytes) -> None: ...
    async def drain(self) -> None: ...
    def close(self) -> None: ...
    async def wait_closed(self) -> None: ...


class _Process(Protocol):
    pid: int
    returncode: int | None
    stdin: _Writer | None
    stdout: _Stream | None
    stderr: _Stream | None

    def terminate(self) -> None: ...
    def kill(self) -> None: ...
    async def wait(self) -> int: ...


ProcessLauncher = Callable[
    [tuple[str, ...], Path, Mapping[str, str]], Awaitable[_Process]
]
VersionProbe = Callable[[Path, Mapping[str, str]], Awaitable[str]]
TreeCleanup = Callable[[_Process, float], Awaitable[bool]]


@dataclass(slots=True)
class _AcpRun:
    context: ContextPackage
    handle: ExternalSessionHandle
    vendor_session_id: str
    task: Task | None = None
    state: RunState = RunState.CREATED
    response: Mapping[str, object] | None = None
    events: list[Mapping[str, object]] = field(default_factory=list)
    artifacts: tuple[Artifact, ...] = ()


def build_opencode_acp_descriptor(
    envelope: ControlledExecutionEnvelope,
) -> ExternalRuntimeDescriptor:
    return ExternalRuntimeDescriptor(
        contract_version=1,
        module_id="module.opencode-acp",
        module_version="1.0.0",
        provider_id="opencode",
        runtime_id="opencode-acp",
        adapter_id="external.opencode-acp",
        runtime_profile_ref="opencode.acp.local",
        protocol_kind=ProtocolKind.ACP,
        protocol_version=1,
        launch_mode=LaunchMode.LOCAL_CHILD,
        capabilities=(
            "artifact_import",
            "cancel",
            "cleanup",
            "egress_declaration",
            "event_stream",
            "health",
            "input_dispatch",
            "permission_requests",
            "readiness",
            "result_capture",
            "session_attach",
            "session_create",
            "version_probe",
        ),
        permissions=(
            "process_execute",
            "provider_model_egress",
            "workspace_read",
            "workspace_write",
        ),
        egress=(
            EgressDeclaration(
                EgressChannel.PROVIDER_MODEL_EGRESS,
                EgressDisposition.APPROVAL_REQUIRED,
                "opencode.provider",
            ),
            EgressDeclaration(
                EgressChannel.AGENT_EXTENSION_EGRESS,
                EgressDisposition.DENY,
            ),
        ),
        auth_ownership=AuthOwnership.RUNTIME_MANAGED,
        conformance_ref="mcf02.fake-acp",
        execution_envelope_ref=envelope.execution_envelope_ref,
    )


def build_opencode_acp_profile() -> RuntimeProfile:
    return RuntimeProfile(
        provider_id="opencode",
        transport_kind=TransportKind.LOCAL,
        runtime_id="opencode-acp",
        adapter_id="external.opencode-acp",
        execution_target=ExecutionTarget.LOCAL,
        runtime_profile_ref="opencode.acp.local",
        profile_revision=1,
        auth_ownership=AuthOwnership.RUNTIME_MANAGED,
        secret_ref_id=None,
        usage_visibility=UsageVisibility.UNAVAILABLE,
    )


async def _default_launcher(
    args: tuple[str, ...], cwd: Path, environment: Mapping[str, str]
) -> _Process:
    kwargs: dict[str, object] = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    return await asyncio.create_subprocess_exec(
        *args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(cwd),
        env=dict(environment),
        **kwargs,
    )


async def _default_version_probe(path: Path, environment: Mapping[str, str]) -> str:
    try:
        process = await asyncio.create_subprocess_exec(
            str(path),
            "--version",
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            cwd=str(path.parent),
            env=dict(environment),
        )
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=5.0)
        if process.returncode != 0 or len(stdout) > 256:
            raise ValueError
        value = stdout.decode("utf-8", errors="strict").strip()
        if not value or any(char in value for char in "\r\n\x00"):
            raise ValueError
        return value
    except Exception:
        raise AcpBoundaryError(_SAFE_FAILURE) from None


async def _default_tree_cleanup(process: _Process, timeout: float) -> bool:
    """Terminate the owned process tree with a platform-verifiable primitive."""
    try:
        if process.returncode is not None:
            # A root that disappeared before containment cleanup does not prove
            # descendants stopped.  The default path therefore fails closed.
            return False
        if os.name == "nt":
            killer = await asyncio.create_subprocess_exec(
                "taskkill",
                "/PID",
                str(process.pid),
                "/T",
                "/F",
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            code = await asyncio.wait_for(killer.wait(), timeout=timeout)
            await asyncio.wait_for(process.wait(), timeout=timeout)
            return code == 0 and process.returncode is not None
        pgid = os.getpgid(process.pid)
        os.killpg(pgid, signal.SIGTERM)
        try:
            await asyncio.wait_for(process.wait(), timeout=timeout / 2)
        except asyncio.TimeoutError:
            os.killpg(pgid, signal.SIGKILL)
            await asyncio.wait_for(process.wait(), timeout=timeout / 2)
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return process.returncode is not None
        return False
    except Exception:
        return False


class OpenCodeAcpRuntimeAdapter:
    """One-run external ACP adapter with a controlled execution envelope."""

    def __init__(
        self,
        *,
        staging_root: Path,
        envelope: ControlledExecutionEnvelope,
        descriptor: ExternalRuntimeDescriptor | None = None,
        provider_model_approved: bool = False,
        operation_timeout: float = 10.0,
        process_launcher: ProcessLauncher = _default_launcher,
        version_probe: VersionProbe = _default_version_probe,
        tree_cleanup: TreeCleanup = _default_tree_cleanup,
    ) -> None:
        if type(operation_timeout) not in (int, float) or not 0 < operation_timeout <= 120:
            raise ExternalContractError("Invalid ACP operation timeout")
        self.staging_root = Path(staging_root).resolve(strict=True)
        self.envelope = envelope
        self.descriptor = descriptor or build_opencode_acp_descriptor(envelope)
        if self.descriptor.execution_envelope_ref != envelope.execution_envelope_ref:
            raise ExternalContractError("External descriptor and envelope do not match")
        self._provider_model_approved = provider_model_approved
        self._operation_timeout = float(operation_timeout)
        self._process_launcher = process_launcher
        self._version_probe = version_probe
        self._tree_cleanup = tree_cleanup
        self._snapshot: RuntimeBindingSnapshot | None = None
        self._binding_fingerprint: str | None = None
        self._process: _Process | None = None
        self._stderr_task: asyncio.Task[bytes] | None = None
        self._stderr_oversize = False
        self._next_id = 1
        self._runs: dict[str, _AcpRun] = {}
        self._request_lock = asyncio.Lock()

    def bind_core_run(self, snapshot: RuntimeBindingSnapshot) -> None:
        if self._snapshot is not None:
            raise ExternalContractError("External adapter is already bound")
        if (
            snapshot.provider_id != self.descriptor.provider_id
            or snapshot.runtime_id != self.descriptor.runtime_id
            or snapshot.adapter_id != self.descriptor.adapter_id
            or snapshot.runtime_profile_ref != self.descriptor.runtime_profile_ref
            or snapshot.adapter_version != self.descriptor.binding_version_token
        ):
            raise ExternalContractError("External adapter binding identity mismatch")
        self._snapshot = snapshot
        self._binding_fingerprint = binding_fingerprint(snapshot)

    async def health(self) -> bool:
        try:
            validate_current_envelope(self.envelope, self.staging_root)
            return True
        except Exception:
            return False

    async def readiness(self) -> bool:
        try:
            validate_current_envelope(self.envelope, self.staging_root)
            observed = await self._version_probe(
                Path(self.envelope.executable_identity.resolved_path),
                self._controlled_environment(),
            )
            return observed == self.envelope.executable_identity.observed_runtime_version
        except Exception:
            return False

    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(
            cancel=True,
            resume=ResumeMode.NONE,
            artifacts=True,
            timeout_cleanup_verified=True,
            usage_visibility=UsageVisibility.UNAVAILABLE,
            auth_ownership=self.descriptor.auth_ownership,
            external_sessions=True,
            event_stream=True,
            permission_requests=True,
            egress_declaration=True,
        )

    async def create_run(self, context: ContextPackage) -> str:
        if self._snapshot is None or self._binding_fingerprint is None:
            raise AcpBoundaryError(_SAFE_FAILURE)
        if not context.project_id:
            raise AcpBoundaryError(_SAFE_FAILURE)
        if not await self.readiness():
            raise AcpBoundaryError(_SAFE_FAILURE)
        # Allocate a Core-scoped reference before launching any child. This
        # lets RunSupervisor retain cleanup ownership if ACP initialization or
        # session creation later fails during submit().
        safe_id = "session-" + hashlib.sha256(
            (
                self._snapshot.run_id
                + self._binding_fingerprint
                + self.envelope.execution_envelope_ref
            ).encode("utf-8")
        ).hexdigest()[:32]
        handle = ExternalSessionHandle(
            external_session_id=safe_id,
            project_scope_digest=project_scope_digest(context),
            binding_fingerprint=self._binding_fingerprint,
            execution_envelope_fingerprint=self.envelope.execution_envelope_ref,
            created_by_run_id=self._snapshot.run_id,
        )
        runtime_ref = "opencode-acp:" + hashlib.sha256(
            (safe_id + self._snapshot.run_id).encode("utf-8")
        ).hexdigest()[:32]
        self._runs[runtime_ref] = _AcpRun(context, handle, "")
        return runtime_ref

    async def submit(self, runtime_ref: str, task: Task) -> None:
        record = self._get(runtime_ref)
        self._validate_attached(record)
        if record.state is not RunState.CREATED or task.project_id != record.context.project_id:
            raise AcpBoundaryError(_SAFE_FAILURE)
        decision = evaluate_external_egress(
            self.descriptor,
            provider_model_approved=self._provider_model_approved,
        )
        if not decision.dispatch_allowed:
            raise AcpBoundaryError(_SAFE_FAILURE)
        validate_current_envelope(self.envelope, self.staging_root)
        record.task = task
        record.state = RunState.RUNNING
        try:
            await self._ensure_process()
            initialize = await self._request(
                "initialize",
                {
                    "protocolVersion": 1,
                    # The adapter does not implement ACP client-side filesystem
                    # or terminal callbacks. Advertising them would overclaim a
                    # bypass-capable surface, even inside projected staging.
                    "clientCapabilities": {},
                },
            )
            if initialize.get("protocolVersion") != 1:
                raise AcpBoundaryError(_SAFE_FAILURE)
            created = await self._request(
                "session/new",
                {"cwd": str(self.staging_root), "mcpServers": []},
            )
            vendor_session_id = created.get("sessionId")
            if type(vendor_session_id) is not str or not vendor_session_id:
                raise AcpBoundaryError(_SAFE_FAILURE)
            safe_id = "session-" + hashlib.sha256(
                vendor_session_id.encode("utf-8")
            ).hexdigest()[:32]
            record.vendor_session_id = vendor_session_id
            record.handle = ExternalSessionHandle(
                external_session_id=safe_id,
                project_scope_digest=record.handle.project_scope_digest,
                binding_fingerprint=record.handle.binding_fingerprint,
                execution_envelope_fingerprint=(
                    record.handle.execution_envelope_fingerprint
                ),
                created_by_run_id=record.handle.created_by_run_id,
                attach_generation=record.handle.attach_generation,
            )
            record.response = await self._request(
                "session/prompt",
                {
                    "sessionId": record.vendor_session_id,
                    "prompt": [{"type": "text", "text": task.title}],
                },
                event_sink=record.events,
            )
            record.state = RunState.COMPLETED
        except Exception:
            if record.state not in {RunState.CANCEL_REQUESTED, RunState.CANCELLED}:
                record.state = RunState.FAILED
            raise AcpBoundaryError(_SAFE_FAILURE) from None

    async def status(self, runtime_ref: str) -> RuntimeStatus:
        record = self._get(runtime_ref)
        return RuntimeStatus(
            state=record.state,
            error=_SAFE_FAILURE if record.state is RunState.FAILED else None,
        )

    async def result(self, runtime_ref: str) -> RuntimeResult:
        record = self._get(runtime_ref)
        if record.state is not RunState.COMPLETED or record.response is None or record.task is None:
            raise AcpBoundaryError(_SAFE_FAILURE)
        output = self._candidate_output(record.response)
        output_digest = hashlib.sha256(output.encode("utf-8")).hexdigest()
        evidence = Evidence(
            task_id=record.task.id,
            run_id=record.handle.created_by_run_id,
            actor_id="external:opencode-acp",
            source="external-runtime-candidate",
            type=EvidenceType.AI_OPINION,
            status=EvidenceStatus.OBSERVED,
            metadata={
                "output_sha256": output_digest,
                "output_size_bytes": len(output.encode("utf-8")),
                "external_session_ref": record.handle.external_session_id,
                "execution_envelope_ref": self.envelope.execution_envelope_ref,
                "runtime_profile_ref": self.descriptor.runtime_profile_ref,
                "adapter_id": self.descriptor.adapter_id,
                "module_version": self.descriptor.module_version,
                "protocol": (
                    f"{self.descriptor.protocol_kind.value}/"
                    f"{self.descriptor.protocol_version}"
                ),
                "sanitization": "HASH_ONLY_CANDIDATE_OUTPUT",
                "provider_model_egress": "HUMAN_APPROVED",
                "agent_extension_egress": "DENIED",
            },
        )
        record.artifacts = self._capture_artifacts(record)
        cleanup_ok = await self._stop_process()
        if not cleanup_ok:
            record.state = RunState.ORPHANED
            raise AcpBoundaryError(_SAFE_FAILURE)
        record.state = RunState.COMPLETED
        return RuntimeResult(summary=_SAFE_RESULT, evidence=(evidence,), artifacts=record.artifacts)

    async def cancel(self, runtime_ref: str) -> None:
        record = self._get(runtime_ref)
        if record.state in {RunState.CREATED, RunState.RUNNING}:
            if self._process is None:
                record.state = RunState.CANCEL_REQUESTED
                return
            try:
                await self._notify(
                    "session/cancel", {"sessionId": record.vendor_session_id}
                )
            except Exception:
                raise AcpBoundaryError(_SAFE_FAILURE) from None
            record.state = RunState.CANCEL_REQUESTED

    async def resume(self, runtime_ref: str, checkpoint: str | None = None) -> None:
        del checkpoint
        self._get(runtime_ref)
        raise NotImplementedError(_NO_RESUME)

    async def artifacts(self, runtime_ref: str) -> tuple[Artifact, ...]:
        return self._get(runtime_ref).artifacts

    async def cleanup(self, runtime_ref: str) -> bool:
        record = self._get(runtime_ref)
        stopped = await self._stop_process()
        if stopped:
            record.state = (
                RunState.TIMED_OUT
                if record.state is RunState.TIMED_OUT
                else RunState.CANCELLED
            )
        return stopped

    def version_info(self) -> str:
        return f"{_ADAPTER_VERSION}+runtime.{self.envelope.executable_identity.observed_runtime_version}"

    def session_handle(self, runtime_ref: str) -> ExternalSessionHandle:
        return self._get(runtime_ref).handle

    def observed_events(self, runtime_ref: str) -> tuple[Mapping[str, object], ...]:
        return tuple(self._get(runtime_ref).events)

    def _validate_attached(self, record: _AcpRun) -> None:
        if self._snapshot is None or self._binding_fingerprint is None:
            raise AcpBoundaryError(_SAFE_FAILURE)
        if (
            record.handle.created_by_run_id != self._snapshot.run_id
            or record.handle.binding_fingerprint != self._binding_fingerprint
            or record.handle.execution_envelope_fingerprint != self.envelope.execution_envelope_ref
            or record.handle.project_scope_digest != project_scope_digest(record.context)
        ):
            raise AcpBoundaryError(_SAFE_FAILURE)
        validate_current_envelope(self.envelope, self.staging_root)

    async def _ensure_process(self) -> _Process:
        if self._process is not None and self._process.returncode is None:
            return self._process
        args = (self.envelope.executable_identity.resolved_path, "acp")
        try:
            process = await self._process_launcher(
                args, self.staging_root, self._controlled_environment()
            )
            if process.stdin is None or process.stdout is None or process.stderr is None:
                raise ValueError
        except Exception:
            raise AcpBoundaryError(_SAFE_FAILURE) from None
        self._process = process
        self._stderr_task = asyncio.create_task(self._drain_stderr(process.stderr))
        return process

    def _controlled_environment(self) -> dict[str, str]:
        environment = {"NO_COLOR": "1", "OPENCODE_DISABLE_AUTO_UPDATE": "1"}
        if os.name == "nt":
            for name in ("SystemRoot", "ComSpec", "WINDIR", "TEMP", "TMP"):
                value = os.environ.get(name)
                if value:
                    environment[name] = value
        else:
            for name in ("LANG", "LC_ALL", "TMPDIR"):
                value = os.environ.get(name)
                if value:
                    environment[name] = value
        return environment

    async def _request(
        self,
        method: str,
        params: Mapping[str, object],
        *,
        event_sink: list[Mapping[str, object]] | None = None,
    ) -> Mapping[str, object]:
        async with self._request_lock:
            process = self._process
            if process is None or process.stdin is None or process.stdout is None:
                raise AcpBoundaryError(_SAFE_FAILURE)
            request_id = self._next_id
            self._next_id += 1
            payload = json.dumps(
                {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params},
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("ascii") + b"\n"
            if len(payload) > MAX_FRAME_BYTES:
                raise AcpBoundaryError(_SAFE_FAILURE)
            try:
                process.stdin.write(payload)
                await asyncio.wait_for(process.stdin.drain(), self._operation_timeout)
                while True:
                    raw = await asyncio.wait_for(process.stdout.readline(), self._operation_timeout)
                    if not raw or len(raw) > MAX_FRAME_BYTES:
                        raise ValueError
                    message = json.loads(raw)
                    if type(message) is not dict or message.get("jsonrpc") != "2.0":
                        raise ValueError
                    if "id" not in message:
                        if event_sink is not None:
                            if len(event_sink) >= _MAX_EVENTS:
                                raise ValueError
                            event_sink.append(self._sanitize_event(message))
                        continue
                    if message.get("id") != request_id or "error" in message:
                        raise ValueError
                    result = message.get("result")
                    if type(result) is not dict:
                        raise ValueError
                    return result
            except Exception:
                raise AcpBoundaryError(_SAFE_FAILURE) from None

    async def _notify(self, method: str, params: Mapping[str, object]) -> None:
        process = self._process
        if process is None or process.stdin is None:
            raise AcpBoundaryError(_SAFE_FAILURE)
        payload = json.dumps(
            {"jsonrpc": "2.0", "method": method, "params": params},
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii") + b"\n"
        if len(payload) > MAX_FRAME_BYTES:
            raise AcpBoundaryError(_SAFE_FAILURE)
        process.stdin.write(payload)
        await asyncio.wait_for(process.stdin.drain(), self._operation_timeout)

    @staticmethod
    def _sanitize_event(message: Mapping[str, object]) -> Mapping[str, object]:
        method = message.get("method")
        return {
            "method": method if type(method) is str and len(method) <= 128 else "unknown",
            "observed": True,
        }

    @staticmethod
    def _candidate_output(response: Mapping[str, object]) -> str:
        value = response.get("output", "")
        if type(value) is not str or len(value.encode("utf-8")) > MAX_FRAME_BYTES:
            raise AcpBoundaryError(_SAFE_FAILURE)
        return value

    def _capture_artifacts(self, record: _AcpRun) -> tuple[Artifact, ...]:
        raw = record.response.get("artifacts", ()) if record.response is not None else ()
        if type(raw) not in (list, tuple) or len(raw) > _MAX_ARTIFACTS:
            raise AcpBoundaryError(_SAFE_FAILURE)
        captured: list[Artifact] = []
        root = self.staging_root.resolve(strict=True)
        for value in raw:
            expected_hash: str | None = None
            expected_size: int | None = None
            if type(value) is str:
                relative_value = value
            elif type(value) is dict and set(value) == {"path", "sha256", "size"}:
                relative_value = value.get("path")
                expected_hash = value.get("sha256")
                expected_size = value.get("size")
                if (
                    type(expected_hash) is not str
                    or len(expected_hash) != 64
                    or any(char not in "0123456789abcdef" for char in expected_hash)
                    or type(expected_size) is not int
                    or expected_size < 0
                ):
                    raise AcpBoundaryError(_SAFE_FAILURE)
            else:
                raise AcpBoundaryError(_SAFE_FAILURE)
            if type(relative_value) is not str or not relative_value or os.path.isabs(relative_value):
                raise AcpBoundaryError(_SAFE_FAILURE)
            candidate = root / relative_value
            if is_link_or_junction(candidate):
                raise AcpBoundaryError(_SAFE_FAILURE)
            try:
                resolved = candidate.resolve(strict=True)
                resolved.relative_to(root)
            except Exception:
                raise AcpBoundaryError(_SAFE_FAILURE) from None
            before = resolved.stat()
            if not resolved.is_file() or before.st_size > MAX_STAGING_FILE_BYTES:
                raise AcpBoundaryError(_SAFE_FAILURE)
            data = resolved.read_bytes()
            after = resolved.stat()
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
            ):
                raise AcpBoundaryError(_SAFE_FAILURE)
            digest = hashlib.sha256(data).hexdigest()
            if (expected_hash is not None and expected_hash != digest) or (
                expected_size is not None and expected_size != len(data)
            ):
                raise AcpBoundaryError(_SAFE_FAILURE)
            captured.append(
                Artifact(
                    project_id=record.context.project_id,
                    task_id=record.task.id if record.task else None,
                    run_id=record.handle.created_by_run_id,
                    artifact_type=ArtifactType.RAW_AI_OUTPUT,
                    mime_type="application/octet-stream",
                    source_type="external-runtime-candidate",
                    storage_ref=str(resolved),
                    sha256=digest,
                    size=len(data),
                )
            )
        return tuple(captured)

    async def _drain_stderr(self, stream: _Stream) -> bytes:
        try:
            value = await stream.read(MAX_FRAME_BYTES + 1)
            if len(value) > MAX_FRAME_BYTES:
                self._stderr_oversize = True
            return b""
        except Exception:
            self._stderr_oversize = True
            return b""

    async def _stop_process(self) -> bool:
        process = self._process
        if process is None:
            return True
        try:
            if process.stdin is not None:
                process.stdin.close()
                try:
                    await asyncio.wait_for(process.stdin.wait_closed(), timeout=1.0)
                except Exception:
                    pass
            stopped = await self._tree_cleanup(process, self._operation_timeout)
            if self._stderr_task is not None:
                try:
                    await asyncio.wait_for(self._stderr_task, timeout=1.0)
                except Exception:
                    stopped = False
            stopped = stopped and process.returncode is not None and not self._stderr_oversize
            self._process = None
            return stopped
        except Exception:
            return False

    def _get(self, runtime_ref: str) -> _AcpRun:
        if type(runtime_ref) is not str:
            raise KeyError("Unknown OpenCode ACP runtime reference")
        record = self._runs.get(runtime_ref)
        if record is None:
            raise KeyError("Unknown OpenCode ACP runtime reference")
        return record
