"""Static, run-scoped adapter for the locally installed Codex executor.

This adapter is intentionally small and target-specific.  It does not become
the Runtime resolver, does not read a credential store, and does not claim
that a successful CLI exit is a source change.  A result is importable only
after the controlled process has quiesced, the staged boundary is rechecked,
and an allowlisted Git diff is observed and copied into Core-owned storage.
"""
from __future__ import annotations

import asyncio
import hashlib
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
    create_projected_staging,
    executable_digest,
    make_envelope,
)
from polynexus_core.storage.content import ContentStore, MAX_CONTENT_BYTES
from polynexus_core.workspace.ownership import ControlledJob


CODEX_EXECUTABLE_ENV = "POLYNEXUS_CODEX_EXECUTABLE"
CODEX_PROFILE_REF = "codex.local"
CODEX_ADAPTER_ID = "builtin.codex.exec"
_SAFE_VERSION = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MAX_DIFF_BYTES = min(MAX_CONTENT_BYTES, 8 * 1024 * 1024)
_MAX_JSON_RESULT_BYTES = min(MAX_CONTENT_BYTES, 4 * 1024 * 1024)
_NORMALIZED_RESULT_TERMINALS = frozenset({"turn.completed", "result", "task.completed"})
_SAFE_ENVIRONMENT_NAMES = frozenset(
    {
        "COMSPEC",
        "PATHEXT",
        "PATH",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "WINDIR",
    }
)


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
    argv: tuple[str, ...] = ()
    cwd: str = ""
    process_facts: tuple[dict[str, object], ...] = ()
    stdout: bytes = b""
    stderr: bytes = b""
    prompt_sha256: str = ""
    normalized_result: dict[str, object] | None = None


class CodexExecRuntimeAdapter:
    """A static locally installed Codex CLI target behind the existing adapter contract."""

    def __init__(
        self,
        *,
        executable: Path | None = None,
        content_root: Path | None = None,
        job_factory: Callable[[list[str], Path], object] | None = None,
        version_probe: Callable[[Path], str] = probe_codex_version,
    ) -> None:
        self._executable = (executable or resolve_codex_executable()).resolve(strict=True)
        self._version_probe = version_probe
        self._content_root = content_root
        self._job_factory = job_factory or self._managed_job_factory
        self._runs: dict[str, _CodexRun] = {}
        self._run_id: str | None = None
        self._task_id: str | None = None
        self._project_id: str | None = None
        self._version: str | None = None
        self._prelaunch_no_effect = False

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

    @staticmethod
    def _base_arguments() -> tuple[str, ...]:
        return (
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--sandbox",
            "workspace-write",
            "--json",
        )

    @staticmethod
    def _fingerprint(value: object) -> str:
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
                "utf-8"
            )
        ).hexdigest()

    def _configuration_preflight(self, version: str) -> dict[str, object]:
        """Resolve the closed Codex configuration boundary without secrets.

        Codex is launched with user configuration disabled and an explicit
        child-environment allowlist.  The snapshot fingerprints the actual
        executable, flags, environment names/value digests, and explicit
        NONE plugin/MCP/skill state; it never reads a credential or config
        file.  Unknown configuration sources fail closed.
        """

        arguments = self._base_arguments()
        if "--ignore-user-config" not in arguments or "--json" not in arguments:
            raise ExternalContractError("codex_configuration_boundary_invalid")
        environment = self._executor_environment()
        if set(environment) - _SAFE_ENVIRONMENT_NAMES:
            raise ExternalContractError("codex_environment_boundary_invalid")
        environment_value_digests = {
            name: hashlib.sha256(value.encode("utf-8")).hexdigest()
            for name, value in sorted(environment.items())
        }
        environment_fingerprint = self._fingerprint(
            {
                "names": tuple(sorted(environment)),
                "value_sha256": environment_value_digests,
            }
        )
        config_sources = (
            "cli.flags",
            "child.environment.allowlist",
        )
        enabled_plugins = ("NONE",)
        enabled_mcps = ("NONE",)
        remote_skills = "NONE"
        payload = {
            "executable_path": os.path.normcase(str(self._executable)),
            "executable_sha256": executable_digest(self._executable),
            "executable_version": version,
            "arguments": arguments,
            "config_sources": config_sources,
            "child_environment_fingerprint": environment_fingerprint,
            "auth_ownership": AuthOwnership.RUNTIME_MANAGED.value,
            "enabled_plugin_set": enabled_plugins,
            "enabled_mcp_set": enabled_mcps,
            "remote_skill_catalog_state": remote_skills,
            "workspace_scope_mode": "PROJECTED_STAGING",
        }
        return {
            "arguments": arguments,
            "config_sources": config_sources,
            "enabled_plugin_set": enabled_plugins,
            "enabled_mcp_set": enabled_mcps,
            "remote_skill_catalog_state": remote_skills,
            "child_environment_fingerprint": environment_fingerprint,
            "fingerprint": self._fingerprint(payload),
        }

    @staticmethod
    def _permission_fingerprint(
        *,
        allowed_inputs: tuple[str, ...],
        allowed_outputs: tuple[str, ...],
        route_policy_evidence_sha256: str,
    ) -> str:
        if not _SHA256.fullmatch(route_policy_evidence_sha256):
            raise ExternalContractError("policy_preflight_missing")
        return CodexExecRuntimeAdapter._fingerprint(
            {
                "allowed_inputs": allowed_inputs,
                "allowed_outputs": allowed_outputs,
                "route_policy_evidence_sha256": route_policy_evidence_sha256,
                "provider_model_egress": EgressDisposition.RUNTIME_MANAGED.value,
                "agent_extension_egress": EgressDisposition.DENY.value,
                "workspace_scope_mode": "PROJECTED_STAGING",
            }
        )

    async def health(self) -> bool:
        try:
            self._probe()
            return True
        except ExternalContractError:
            return False

    async def readiness(self) -> bool:
        # Readiness is a no-side-effect executable/configuration boundary
        # probe.  It is not live-provider or conformance evidence and never
        # launches a task.
        try:
            self._configuration_preflight(self._probe())
            return True
        except ExternalContractError:
            return False

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
        self._prelaunch_no_effect = False
        version = self._probe()
        facts = dict(context.project_facts)
        workspace_value = facts.get("projected_staging")
        scope_mode = facts.get("workspace_scope_mode", "PROJECTED_STAGING")
        if scope_mode != "PROJECTED_STAGING":
            raise ExternalContractError("workspace_scope_mode_invalid")
        input_value = facts.get("allowed_input_paths", "[]")
        output_value = facts.get("allowed_output_paths", input_value)
        try:
            allowed_inputs = tuple(json.loads(input_value))
            allowed_outputs = tuple(json.loads(output_value))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ExternalContractError("allowlist_invalid") from exc
        if not allowed_outputs:
            raise ExternalContractError("output_allowlist_empty")
        project_id = context.project_id
        policy_digest = facts.get("runtime_policy_evidence_sha256")
        if not isinstance(policy_digest, str) or not _SHA256.fullmatch(policy_digest):
            raise ExternalContractError("policy_preflight_missing")
        preflight = self._configuration_preflight(version)
        if not isinstance(workspace_value, str) or not workspace_value:
            managed_value = facts.get("managed_workspace")
            if not isinstance(managed_value, str) or not managed_value:
                raise ExternalContractError("projected_staging_required")
            managed = Path(managed_value)
            staging_id = "staging_" + hashlib.sha256(
                f"{self._run_id}:{self._task_id}".encode("utf-8")
            ).hexdigest()[:24]
            try:
                workspace_value = str(
                    create_projected_staging(
                        source_root=managed,
                        staging_root=managed.parent / staging_id,
                        allowed_inputs=allowed_inputs,
                        allowed_outputs=allowed_outputs,
                    )
                )
            except Exception:
                # No runtime reference has been published and no child can
                # have launched; expose this narrow proof to the owner so a
                # staging preflight failure is terminal without claiming a
                # generic adapter create failure is harmless.
                self._prelaunch_no_effect = True
                raise
        arguments = tuple(preflight["arguments"])
        config_sources = tuple(preflight["config_sources"])
        enabled_plugins = tuple(preflight["enabled_plugin_set"])
        enabled_mcps = tuple(preflight["enabled_mcp_set"])
        remote_skills = str(preflight["remote_skill_catalog_state"])
        envelope = make_envelope(
            run_id=self._run_id,
            task_id=self._task_id,
            project_id=project_id,
            staging_root=Path(workspace_value),
            allowed_inputs=allowed_inputs,
            allowed_outputs=allowed_outputs,
            executable_path=self._executable,
            executable_version=version,
            arguments=arguments,
            config_sources=config_sources,
            egress={
                EgressChannel.PROVIDER_MODEL: EgressDisposition.RUNTIME_MANAGED,
                EgressChannel.AGENT_EXTENSION: EgressDisposition.DENY,
            },
            effective_runtime_configuration_fingerprint=str(preflight["fingerprint"]),
            permission_policy_fingerprint=self._permission_fingerprint(
                allowed_inputs=allowed_inputs,
                allowed_outputs=allowed_outputs,
                route_policy_evidence_sha256=policy_digest,
            ),
            enabled_plugin_set=enabled_plugins,
            enabled_mcp_set=enabled_mcps,
            remote_skill_catalog_state=remote_skills,
            route_policy_evidence_sha256=policy_digest,
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
        record.envelope.assert_quiescent_input()
        prompt = self._prompt(record, task)
        argv = [
            str(record.envelope.executable_path),
            *record.envelope.arguments,
            "--cd",
            str(record.envelope.staging_root),
            prompt,
        ]
        record.argv = tuple(argv)
        record.cwd = str(record.envelope.staging_root)
        record.prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
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
        self._observe_job(record)
        record.exit_code = self._exit_code(record)
        if record.exit_code != 0:
            record.state = RunState.FAILED
            raise ExternalContractError("codex_process_failed")
        try:
            normalized_result = self._parse_normalized_result(record)
            preflight = self._configuration_preflight(record.envelope.executable_version)
            if preflight["fingerprint"] != record.envelope.effective_runtime_configuration_fingerprint:
                raise ExternalContractError("runtime_configuration_changed")
            record.envelope.verify_staging()
            record.envelope.assert_quiescent_input()
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
                    "workspace_scope_mode": record.envelope.workspace_scope_mode,
                    "effective_runtime_configuration_fingerprint": record.envelope.effective_runtime_configuration_fingerprint,
                    "permission_policy_fingerprint": record.envelope.permission_policy_fingerprint,
                    "route_policy_evidence_sha256": record.envelope.route_policy_evidence_sha256,
                    "config_sources": json.dumps(record.envelope.config_sources, separators=(",", ":")),
                    "enabled_plugin_set": json.dumps(record.envelope.enabled_plugin_set, separators=(",", ":")),
                    "enabled_mcp_set": json.dumps(record.envelope.enabled_mcp_set, separators=(",", ":")),
                    "remote_skill_catalog_state": record.envelope.remote_skill_catalog_state,
                    "child_environment_fingerprint": preflight["child_environment_fingerprint"],
                    "executable_sha256": record.envelope.executable_sha256,
                    "executable_version": record.envelope.executable_version,
                    "exit_code": str(record.exit_code),
                    "argv_json": json.dumps(self._safe_argv(record), ensure_ascii=False, separators=(",", ":")),
                    "cwd": record.cwd,
                    "cwd_scope": record.envelope.workspace_scope_mode,
                    "process_facts_json": json.dumps(self._safe_process_facts(record), sort_keys=True, separators=(",", ":")),
                    "prompt_sha256": record.prompt_sha256,
                    "stdout_sha256": hashlib.sha256(record.stdout).hexdigest(),
                    "stderr_sha256": hashlib.sha256(record.stderr).hexdigest(),
                    "stdout_bytes": str(len(record.stdout)),
                    "stderr_bytes": str(len(record.stderr)),
                    "normalized_result_json": json.dumps(
                        normalized_result, sort_keys=True, separators=(",", ":")
                    ),
                    "normalized_result_sha256": self._fingerprint(normalized_result),
                    "signal": str(record.process_facts[0].get("signal", "unknown"))
                    if record.process_facts else "unknown",
                    "auth_ownership": AuthOwnership.RUNTIME_MANAGED.value,
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
            self._observe_job(record)
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

    def no_effect_failure_verified(self) -> bool:
        """Return the narrow pre-launch projection proof for the owner."""

        return self._prelaunch_no_effect

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
        record.envelope.assert_quiescent_input()
        first = self._git_diff(record)
        first_status = self._git_status_paths(record, allowlisted_only=False)
        if not first:
            raise ExternalContractError("allowlisted_source_change_missing")
        if any(path not in set(record.envelope.allowed_outputs) for path in first_status):
            raise ExternalContractError("output_path_not_allowlisted")
        second = self._git_diff(record)
        second_status = self._git_status_paths(record, allowlisted_only=False)
        record.envelope.assert_quiescent_input()
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
            facts = record.process_facts or (tuple(record.job.facts()) if record.job is not None else ())
            if not facts:
                raise ExternalContractError("codex_exit_observation_missing")
            return int(facts[0]["exit_code"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ExternalContractError("codex_exit_observation_invalid") from exc

    @staticmethod
    def _observe_job(record: _CodexRun) -> None:
        if record.job is None:
            raise ExternalContractError("codex_process_observation_missing")
        try:
            record.process_facts = tuple(record.job.facts())
            output = getattr(record.job, "output", None)
            if callable(output):
                stdout, stderr = output()
                record.stdout = bytes(stdout)
                record.stderr = bytes(stderr)
        except Exception as exc:
            raise ExternalContractError("codex_process_observation_invalid") from exc

    @classmethod
    def _parse_normalized_result(cls, record: _CodexRun) -> dict[str, object]:
        """Require bounded, uncontaminated Codex JSONL terminal output."""

        if not record.stdout or len(record.stdout) > _MAX_JSON_RESULT_BYTES:
            raise ExternalContractError("codex_result_missing_or_oversize")
        try:
            text = record.stdout.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ExternalContractError("codex_result_not_utf8") from exc
        events: list[dict[str, object]] = []
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ExternalContractError("codex_result_malformed") from exc
            if not isinstance(value, dict) or not isinstance(value.get("type"), str):
                raise ExternalContractError("codex_result_schema_invalid")
            if value["type"] in {"error", "turn.failed", "task.failed", "fatal"}:
                raise ExternalContractError("codex_result_failed")
            events.append(value)
        if not events:
            raise ExternalContractError("codex_result_empty")
        terminal = events[-1]
        terminal_type = terminal["type"]
        if terminal_type not in _NORMALIZED_RESULT_TERMINALS:
            raise ExternalContractError("codex_result_terminal_missing")
        if terminal.get("status") in {"failed", "error", "cancelled"}:
            raise ExternalContractError("codex_result_failed")
        normalized = {
            "format": "codex.exec.jsonl.v1",
            "event_count": len(events),
            "terminal_type": terminal_type,
            "terminal_sha256": cls._fingerprint(terminal),
        }
        record.normalized_result = normalized
        return normalized

    @staticmethod
    def _safe_argv(record: _CodexRun) -> tuple[str, ...]:
        values = list(record.argv)
        if values:
            values[-1] = f"<prompt-sha256:{record.prompt_sha256}>"
        return tuple(values)

    @classmethod
    def _safe_process_facts(cls, record: _CodexRun) -> tuple[dict[str, object], ...]:
        safe: list[dict[str, object]] = []
        for fact in record.process_facts:
            item = dict(fact)
            item["argv"] = cls._safe_argv(record)
            safe.append(item)
        return tuple(safe)

    def _managed_job_factory(self, argv: list[str], cwd: Path) -> object:
        return ControlledJob(argv, cwd, environment=self._executor_environment())

    @staticmethod
    def _executor_environment() -> dict[str, str]:
        """Return the explicit non-secret environment given to the child."""

        return {
            name: value
            for name, value in os.environ.items()
            if name in _SAFE_ENVIRONMENT_NAMES
        }

    def _get(self, runtime_ref: str) -> _CodexRun:
        try:
            return self._runs[runtime_ref]
        except KeyError as exc:
            raise ExternalContractError("codex_runtime_reference_unknown") from exc
