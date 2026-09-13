"""Static, run-scoped adapter for the locally installed Codex executor.

This adapter is intentionally small and target-specific.  It does not become
the Runtime resolver, does not read a credential store, and does not claim
that a successful CLI exit is a source change.  A result is importable only
after the controlled process has quiesced, the staged boundary is rechecked,
and an allowlisted Git diff is observed and copied into Core-owned storage.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from uuid import uuid4

from polynexus_core.domain.enums import (
    ArtifactType,
    AuthOwnership,
    EvidenceStatus,
    EvidenceType,
    ResumeMode,
    RunState,
    UsageVisibility,
)
from polynexus_core.domain.models import Artifact, ContextPackage, Evidence, Task
from polynexus_core.runtime.contracts import (
    RuntimeCapabilities,
    RuntimeResult,
    RuntimeStatus,
)
from polynexus_core.runtime.external_contracts import (
    EgressChannel,
    EgressDisposition,
    ExecutionEnvelope,
    ExternalContractError,
    make_envelope,
)
from polynexus_core.storage.content import ContentStore, MAX_CONTENT_BYTES
from polynexus_core.workspace.ownership import ControlledJob


CODEX_EXECUTABLE_ENV = "POLYNEXUS_CODEX_EXECUTABLE"
CODEX_PROFILE_REF = "codex.local"
CODEX_ADAPTER_ID = "builtin.codex.exec"
_SAFE_VERSION = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_MAX_DIFF_BYTES = min(MAX_CONTENT_BYTES, 8 * 1024 * 1024)


def _safe_version(value: str) -> str:
    value = "-".join(value.strip().split())
    if not _SAFE_VERSION.fullmatch(value):
        raise ExternalContractError("executor_version_invalid")
    return value


def resolve_codex_executable(value: str | None = None) -> Path:
    """Resolve only an installed executable; never download or fall back."""

    candidate = value or os.environ.get(CODEX_EXECUTABLE_ENV)
    resolved = Path(candidate) if candidate else None
    if resolved is None:
        found = shutil.which("codex")
        resolved = Path(found) if found else None
    if resolved is None or not resolved.is_absolute() or not resolved.is_file():
        raise ExternalContractError("codex_executable_unavailable")
    return resolved.resolve(strict=True)


def probe_codex_version(executable: Path, *, timeout: float = 10.0) -> str:
    """Read a bounded version line without loading user config or secrets."""

    try:
        completed = subprocess.run(
            [str(executable), "--version"],
            capture_output=True,
            check=False,
            timeout=timeout,
            text=True,
            env={"PATH": os.environ.get("PATH", "")},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ExternalContractError("codex_version_probe_failed") from exc
    if completed.returncode != 0:
        raise ExternalContractError("codex_version_probe_failed")
    line = next((line.strip() for line in completed.stdout.splitlines() if line.strip()), "")
    if line.lower().startswith("codex "):
        line = line[6:]
    return _safe_version(line)


@dataclass
class _CodexRun:
    context: ContextPackage
    envelope: ExecutionEnvelope
    task_id: str
    project_id: str
    state: RunState = RunState.CREATED
    job: object | None = None
    exit_code: int | None = None
    cleanup_target: RunState = RunState.CANCELLED
    cleanup_verified: bool = False
    result: RuntimeResult | None = None
    artifacts: tuple[Artifact, ...] = ()


class CodexExecRuntimeAdapter:
    """A static locally installed Codex CLI target behind the existing adapter contract."""

    def __init__(
        self,
        *,
        executable: Path | None = None,
        content_root: Path | None = None,
        job_factory: Callable[[list[str], Path], object] = ControlledJob,
        version_probe: Callable[[Path], str] = probe_codex_version,
    ) -> None:
        self._executable = (executable or resolve_codex_executable()).resolve(strict=True)
        self._version_probe = version_probe
        self._content_root = content_root
        self._job_factory = job_factory
        self._runs: dict[str, _CodexRun] = {}
        self._run_id: str | None = None
        self._task_id: str | None = None
        self._project_id: str | None = None
        self._version: str | None = None

    def bind_run_identity(self, *, run_id: str, task_id: str) -> None:
        """Private supervisor seam; called before workflow dispatch."""

        if not run_id or not task_id:
            raise ExternalContractError("run_identity_invalid")
        if self._run_id is not None and (self._run_id, self._task_id) != (run_id, task_id):
            raise ExternalContractError("run_identity_rebind")
        self._run_id, self._task_id = run_id, task_id

    def _probe(self) -> str:
        if self._version is None:
            self._version = self._version_probe(self._executable)
        return self._version

    async def health(self) -> bool:
        try:
            self._probe()
            return True
        except ExternalContractError:
            return False

    async def readiness(self) -> bool:
        # Readiness is only the bounded executable identity probe.  It is not a
        # live-provider or conformance verdict and never launches a task.
        return await self.health()

    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(
            cancel=True,
            resume=ResumeMode.NONE,
            artifacts=True,
            # This remains false until the first real W2 target has passed the
            # child/grandchild timeout and cleanup gate.
            timeout_cleanup_verified=False,
            usage_visibility=UsageVisibility.UNAVAILABLE,
            auth_ownership=AuthOwnership.RUNTIME_MANAGED,
        )

    async def create_run(self, context: ContextPackage) -> str:
        if self._run_id is None or self._task_id is None:
            raise ExternalContractError("binding_identity_missing")
        version = self._probe()
        facts = dict(context.project_facts)
        workspace_value = facts.get("managed_workspace")
        if not isinstance(workspace_value, str) or not workspace_value:
            raise ExternalContractError("managed_workspace_required")
        input_value = facts.get("allowed_input_paths", "[]")
        output_value = facts.get("allowed_output_paths", input_value)
        try:
            allowed_inputs = tuple(json.loads(input_value))
            allowed_outputs = tuple(json.loads(output_value))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ExternalContractError("allowlist_invalid") from exc
        if not allowed_inputs or not allowed_outputs:
            raise ExternalContractError("allowlist_empty")
        project_id = context.project_id
        envelope = make_envelope(
            run_id=self._run_id,
            task_id=self._task_id,
            project_id=project_id,
            staging_root=Path(workspace_value),
            allowed_inputs=allowed_inputs,
            allowed_outputs=allowed_outputs,
            executable_path=self._executable,
            executable_version=version,
            arguments=(
                "exec",
                "--ephemeral",
                "--ignore-user-config",
                "--sandbox",
                "workspace-write",
                "--json",
            ),
            config_sources=("cli.flags", "runtime-managed-auth"),
            egress={
                EgressChannel.PROVIDER_MODEL: EgressDisposition.RUNTIME_MANAGED,
                EgressChannel.AGENT_EXTENSION: EgressDisposition.DENY,
            },
        )
        runtime_ref = f"codex-exec:{uuid4().hex}"
        self._runs[runtime_ref] = _CodexRun(
            context=context,
            envelope=envelope,
            task_id=self._task_id,
            project_id=project_id,
        )
        return runtime_ref

    async def submit(self, runtime_ref: str, task: Task) -> None:
        record = self._get(runtime_ref)
        if record.state is not RunState.CREATED:
            raise ExternalContractError("codex_submit_state_invalid")
        if task.id != record.task_id or task.project_id != record.project_id:
            raise ExternalContractError("codex_task_scope_invalid")
        record.envelope.verify_staging()
        prompt = self._prompt(record, task)
        argv = [
            str(record.envelope.executable_path),
            *record.envelope.arguments,
            "--cd",
            str(record.envelope.staging_root),
            prompt,
        ]
        try:
            record.job = self._job_factory(argv, record.envelope.staging_root)
        except Exception as exc:
            raise ExternalContractError("codex_process_start_failed") from exc
        record.state = RunState.RUNNING

    async def status(self, runtime_ref: str) -> RuntimeStatus:
        record = self._get(runtime_ref)
        if record.state in {
            RunState.CANCELLED,
            RunState.TIMED_OUT,
            RunState.FAILED,
            RunState.COMPLETED,
        }:
            return RuntimeStatus(record.state)
        if record.job is not None and bool(record.job.stopped()):
            record.exit_code = self._exit_code(record)
            if record.exit_code != 0:
                record.state = RunState.FAILED
        return RuntimeStatus(record.state)

    async def result(self, runtime_ref: str) -> RuntimeResult:
        record = self._get(runtime_ref)
        if record.state not in {RunState.RUNNING, RunState.COMPLETED} or record.job is None:
            raise ExternalContractError("codex_result_unavailable")
        while not bool(record.job.stopped()):
            await asyncio.sleep(0.05)
        record.exit_code = self._exit_code(record)
        if record.exit_code != 0:
            record.state = RunState.FAILED
            raise ExternalContractError("codex_process_failed")
        try:
            record.envelope.verify_staging()
            diff, source_after_manifest = self._stable_allowlisted_diff(record)
            if not diff:
                raise ExternalContractError("allowlisted_source_change_missing")
            store = self._content_store()
            digest, size = store.put(diff)
            artifact = Artifact(
                project_id=record.project_id,
                task_id=record.task_id,
                run_id=self._run_id,
                artifact_type=ArtifactType.CODE_DIFF,
                mime_type="text/x-diff",
                source_type="codex.exec",
                storage_ref=f"core-blob:{digest}",
                sha256=digest,
                size=size,
            )
            evidence = Evidence(
                task_id=record.task_id,
                run_id=self._run_id or "",
                actor_id="runtime:codex.exec",
                source="runtime.codex.exec",
                type=EvidenceType.RUNTIME_EVIDENCE,
                status=EvidenceStatus.OBSERVED,
                artifact_refs=(artifact.id,),
                metadata={
                    "envelope_sha256": record.envelope.envelope_sha256,
                    "executable_sha256": record.envelope.executable_sha256,
                    "executable_version": record.envelope.executable_version,
                    "exit_code": str(record.exit_code),
                    "cwd_scope": "managed-workspace",
                    "provider_model_egress": EgressDisposition.RUNTIME_MANAGED.value,
                    "agent_extension_egress": EgressDisposition.DENY.value,
                    "source_change": "allowlisted-diff-observed",
                    "source_before_manifest_sha256": record.envelope.input_manifest_sha256,
                    "source_after_manifest_sha256": source_after_manifest,
                },
            )
            record.artifacts = (artifact,)
            record.state = RunState.COMPLETED
            record.result = RuntimeResult(
                summary="Codex executor produced an allowlisted source change",
                evidence=(evidence,),
                artifacts=record.artifacts,
            )
            return record.result
        except ExternalContractError:
            record.state = RunState.FAILED
            raise

    async def cancel(self, runtime_ref: str) -> None:
        record = self._get(runtime_ref)
        if record.state in {
            RunState.CANCELLED,
            RunState.TIMED_OUT,
            RunState.FAILED,
            RunState.COMPLETED,
        }:
            return
        if record.job is None:
            raise ExternalContractError("codex_process_handle_missing")
        try:
            record.job.stop(timeout=10)
        except Exception as exc:
            raise ExternalContractError("codex_process_stop_unverified") from exc
        record.exit_code = self._exit_code(record)
        record.state = record.cleanup_target

    async def resume(self, runtime_ref: str, checkpoint: str | None = None) -> None:
        del checkpoint
        self._get(runtime_ref)
        raise ExternalContractError("codex_resume_unsupported")

    async def artifacts(self, runtime_ref: str) -> tuple[Artifact, ...]:
        return self._get(runtime_ref).artifacts

    async def cleanup(self, runtime_ref: str) -> bool:
        record = self._get(runtime_ref)
        if record.job is None:
            return False
        try:
            stopped = bool(record.job.stopped())
            if not stopped:
                return False
            facts = tuple(record.job.facts())
            if not facts or not all(bool(item.get("stopped")) for item in facts):
                return False
            dispose = getattr(record.job, "dispose", None)
            if callable(dispose):
                dispose()
            record.cleanup_verified = True
            return True
        except Exception:
            return False

    def version_info(self) -> str:
        version = self._version or self._probe()
        numeric = re.search(r"\d+(?:\.\d+)*", version)
        return f"codex-exec/{numeric.group(0) if numeric else '0.0.0'}"

    def set_cleanup_target(self, runtime_ref: str, target: RunState) -> None:
        """Private supervisor seam; keeps timeout and cancel terminal states distinct."""

        if target not in {RunState.CANCELLED, RunState.TIMED_OUT}:
            raise ExternalContractError("cleanup_target_invalid")
        self._get(runtime_ref).cleanup_target = target

    def _content_store(self) -> ContentStore:
        root = self._content_root
        if root is None:
            configured = os.environ.get("POLYNEXUS_CONTENT_ROOT")
            if not configured:
                raise ExternalContractError("content_store_unavailable")
            root = Path(configured)
        return ContentStore(root)

    @staticmethod
    def _prompt(record: _CodexRun, task: Task) -> str:
        instructions = "\n".join(str(value) for value in record.context.instructions)
        constraints = "\n".join(str(value) for value in record.context.constraints)
        paths = ", ".join(record.envelope.allowed_outputs)
        return (
            "Work only in this synthetic or Core-managed repository.\n"
            f"Task: {task.title}\n"
            f"Instructions:\n{instructions[:12000]}\n"
            f"Constraints:\n{constraints[:6000]}\n"
            f"Only modify these allowlisted relative paths: {paths}.\n"
            "Do not access parent directories, credentials, secrets, network services, "
            "or files outside the staged workspace.\n"
            "Make the source change and report a concise result."
        )

    def _stable_allowlisted_diff(self, record: _CodexRun) -> tuple[bytes, str]:
        record.envelope.verify_staging()
        first = self._git_diff(record)
        first_status = self._git_status_paths(record, allowlisted_only=False)
        if not first:
            raise ExternalContractError("allowlisted_source_change_missing")
        if any(path not in set(record.envelope.allowed_outputs) for path in first_status):
            raise ExternalContractError("output_path_not_allowlisted")
        second = self._git_diff(record)
        second_status = self._git_status_paths(record, allowlisted_only=False)
        if first != second or first_status != second_status:
            raise ExternalContractError("output_changed_during_import")
        if len(first) > _MAX_DIFF_BYTES:
            raise ExternalContractError("output_too_large")
        return first, record.envelope.current_input_manifest()

    @staticmethod
    def _git_diff(record: _CodexRun) -> bytes:
        try:
            result = subprocess.run(
                [
                    "git",
                    "--no-optional-locks",
                    "-c",
                    "core.fsmonitor=false",
                    "-C",
                    str(record.envelope.staging_root),
                    "diff",
                    "--binary",
                    "--no-ext-diff",
                    "--",
                    *record.envelope.allowed_outputs,
                ],
                capture_output=True,
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ExternalContractError("output_observation_failed") from exc
        if result.returncode != 0:
            raise ExternalContractError("output_observation_failed")
        return result.stdout

    @staticmethod
    def _git_status_paths(record: _CodexRun, *, allowlisted_only: bool = True) -> tuple[str, ...]:
        pathspec = ["--", *record.envelope.allowed_outputs] if allowlisted_only else ["--"]
        try:
            result = subprocess.run(
                [
                    "git",
                    "--no-optional-locks",
                    "-c",
                    "core.fsmonitor=false",
                    "-C",
                    str(record.envelope.staging_root),
                    "status",
                    "--porcelain=v1",
                    "-z",
                    "--untracked-files=all",
                    *pathspec,
                ],
                capture_output=True,
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ExternalContractError("output_observation_failed") from exc
        if result.returncode != 0:
            raise ExternalContractError("output_observation_failed")
        paths: list[str] = []
        for record_bytes in result.stdout.split(b"\0"):
            if not record_bytes:
                continue
            if len(record_bytes) < 4:
                raise ExternalContractError("output_status_invalid")
            flags = record_bytes[:2].decode("ascii", errors="strict")
            if any(value in flags for value in ("R", "C", "U")):
                raise ExternalContractError("output_status_invalid")
            raw = record_bytes[3:].decode("utf-8", errors="strict")
            paths.append(raw)
        return tuple(sorted(paths))

    @staticmethod
    def _exit_code(record: _CodexRun) -> int:
        try:
            facts = tuple(record.job.facts()) if record.job is not None else ()
            if not facts:
                raise ExternalContractError("codex_exit_observation_missing")
            return int(facts[0]["exit_code"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ExternalContractError("codex_exit_observation_invalid") from exc

    def _get(self, runtime_ref: str) -> _CodexRun:
        try:
            return self._runs[runtime_ref]
        except KeyError as exc:
            raise ExternalContractError("codex_runtime_reference_unknown") from exc
