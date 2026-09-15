"""Real OpenCode ACP target behind the existing Core RuntimeAdapter contract.

The legacy deterministic OpenCode fixture adapter remains separate. This
adapter launches only a pinned installed `opencode` executable, into a fresh
Core PROJECTED_STAGING workspace, and imports only a stable allowlisted diff.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from uuid import uuid4

from polynexus_core.domain.enums import (
    ArtifactType, AuthOwnership, EvidenceStatus, EvidenceType,
    ResumeMode, RunState, UsageVisibility,
)
from polynexus_core.domain.models import Artifact, ContextPackage, Evidence, Task
from polynexus_core.runtime.acp_transport import ACPTransport
from polynexus_core.runtime.contracts import RuntimeCapabilities, RuntimeResult, RuntimeStatus
from polynexus_core.runtime.external_contracts import (
    EgressChannel, EgressDisposition, ExecutionEnvelope, ExternalContractError,
    create_projected_staging, executable_digest, make_envelope, relative_path,
)
from polynexus_core.storage.content import ContentStore, MAX_CONTENT_BYTES
from polynexus_core.workspace.ownership import ControlledJob


OPENCODE_EXECUTABLE_ENV = "POLYNEXUS_OPENCODE_EXECUTABLE"
OPENCODE_PROFILE_REF = "opencode.acp.local"
OPENCODE_ADAPTER_ID = "builtin.opencode.acp"
_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:[-.][a-zA-Z0-9.]+)?$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SECRET_LIKE = re.compile(r"(?i)(sk-[a-z0-9_-]{8,}|token|secret|password|cookie|api[_-]?key|credential)")
_MAX_DIFF = min(MAX_CONTENT_BYTES, 8 * 1024 * 1024)
_FREE_MODEL = "opencode/mimo-v2.5-free"


def resolve_opencode_executable(value: str | None = None) -> Path:
    candidate = value or os.environ.get(OPENCODE_EXECUTABLE_ENV) or shutil.which("opencode")
    if not candidate:
        raise ExternalContractError("opencode_executable_unavailable")
    path = Path(candidate)
    if not path.is_absolute() or not path.is_file() or path.suffix.lower() != ".exe":
        raise ExternalContractError("opencode_executable_unavailable")
    return path.resolve(strict=True)


def probe_opencode_version(executable: Path, *, timeout: float = 10.0) -> str:
    try:
        with tempfile.TemporaryDirectory(prefix="polynexus-opencode-version-") as config:
            names = ("COMSPEC", "PATHEXT", "PATH", "SYSTEMDRIVE", "SYSTEMROOT", "TEMP", "TMP", "WINDIR", "USERPROFILE", "APPDATA", "LOCALAPPDATA")
            environment = {name: os.environ[name] for name in names if name in os.environ}
            environment.update({"XDG_CONFIG_HOME": config, "OPENCODE_CONFIG_DIR": config})
            completed = subprocess.run(
                [str(executable), "--version"], capture_output=True, text=True,
                check=False, timeout=timeout, env=environment,
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ExternalContractError("opencode_version_probe_failed") from exc
    version = completed.stdout.strip().splitlines()
    if completed.returncode != 0 or len(version) != 1 or not _VERSION.fullmatch(version[0]):
        raise ExternalContractError("opencode_version_probe_failed")
    return version[0]


def _fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


@dataclass
class _ACPRun:
    context: ContextPackage
    envelope: ExecutionEnvelope
    task_id: str
    project_id: str
    expected_output_hashes: dict[str, str]
    state: RunState = RunState.CREATED
    job: object | None = None
    exchange: asyncio.Task[dict[str, object]] | None = None
    transport: ACPTransport | None = None
    exit_code: int | None = None
    cleanup_target: RunState = RunState.CANCELLED
    cleanup_verified: bool = False
    result_value: RuntimeResult | None = None
    artifacts_value: tuple[Artifact, ...] = ()
    prompt_sha256: str = ""
    terminal: dict[str, object] = field(default_factory=dict)
    stdout: bytes = b""
    stderr: bytes = b""
    process_facts: tuple[dict[str, object], ...] = ()


class OpenCodeACPRuntimeAdapter:
    def __init__(
        self, *, executable: Path | None = None, content_root: Path | None = None,
        job_factory: Callable[[list[str], Path, dict[str, str]], object] | None = None,
        version_probe: Callable[[Path], str] = probe_opencode_version,
    ) -> None:
        self._executable = (executable or resolve_opencode_executable()).resolve(strict=True)
        self._content_root = content_root
        self._job_factory = job_factory or self._managed_job_factory
        self._version_probe = version_probe
        self._version: str | None = None
        self._runs: dict[str, _ACPRun] = {}
        self._run_id: str | None = None
        self._task_id: str | None = None
        self._expected_runtime_ref: str | None = None
        self._prelaunch_no_effect = False

    def bind_run_identity(self, *, run_id: str, task_id: str, expected_runtime_ref: str | None = None) -> None:
        if not run_id or not task_id:
            raise ExternalContractError("binding_identity_missing")
        if self._run_id is not None and (self._run_id, self._task_id) != (run_id, task_id):
            raise ExternalContractError("binding_identity_rebind")
        if expected_runtime_ref is not None and not expected_runtime_ref.startswith("opencode-acp:"):
            raise ExternalContractError("runtime_identity_invalid")
        self._run_id, self._task_id = run_id, task_id
        self._expected_runtime_ref = expected_runtime_ref

    def _probe(self) -> str:
        if self._version is None:
            self._version = self._version_probe(self._executable)
        return self._version

    @staticmethod
    def _configuration() -> dict[str, object]:
        return {
            "model": _FREE_MODEL,
            "plugin": [], "mcp": {}, "instructions": [],
            "permission": {
                "*": "deny", "read": "allow", "glob": "allow", "grep": "allow",
                "edit": "allow", "external_directory": "deny", "bash": "deny",
                "task": "deny", "skill": "deny", "webfetch": "deny", "websearch": "deny",
            },
        }

    def _child_environment(self) -> dict[str, str]:
        if self._content_root is None:
            raise ExternalContractError("opencode_content_root_required")
        isolated_config = self._content_root / "opencode-config"
        isolated_config.mkdir(parents=True, exist_ok=True)
        names = ("COMSPEC", "PATHEXT", "PATH", "SYSTEMDRIVE", "SYSTEMROOT", "TEMP", "TMP", "WINDIR", "USERPROFILE", "APPDATA", "LOCALAPPDATA")
        environment = {name: os.environ[name] for name in names if name in os.environ}
        environment.update({
            "XDG_CONFIG_HOME": str(isolated_config),
            "OPENCODE_CONFIG_DIR": str(isolated_config),
            "OPENCODE_CONFIG_CONTENT": json.dumps(self._configuration(), sort_keys=True, separators=(",", ":")),
            "OPENCODE_DISABLE_AUTOUPDATE": "1", "OPENCODE_AUTO_SHARE": "0",
        })
        return environment

    async def health(self) -> bool:
        try:
            self._probe()
            return True
        except ExternalContractError:
            return False

    async def readiness(self) -> bool:
        try:
            self._probe()
            self._child_environment()
            return True
        except ExternalContractError:
            return False

    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(
            cancel=True, resume=ResumeMode.NONE, artifacts=True,
            timeout_cleanup_verified=True, usage_visibility=UsageVisibility.UNAVAILABLE,
            auth_ownership=AuthOwnership.RUNTIME_MANAGED,
        )

    def operation_timeout_seconds(self) -> float:
        """Request the Core-owned bounded ACP turn deadline, not provider control."""

        return 120.0

    async def create_run(self, context: ContextPackage) -> str:
        if self._run_id is None or self._task_id is None:
            raise ExternalContractError("binding_identity_missing")
        self._prelaunch_no_effect = False
        version = self._probe()
        facts = dict(context.project_facts)
        if facts.get("projected_staging") or facts.get("workspace_scope_mode", "PROJECTED_STAGING") != "PROJECTED_STAGING":
            raise ExternalContractError("projected_staging_injected")
        try:
            allowed_inputs = tuple(json.loads(facts.get("allowed_input_paths", "[]")))
            allowed_outputs = tuple(json.loads(facts.get("allowed_output_paths", "[]")))
            expected = dict(json.loads(facts.get("required_output_sha256", "{}")))
        except (TypeError, ValueError) as exc:
            raise ExternalContractError("allowlist_invalid") from exc
        if not allowed_outputs or any(not _SHA256.fullmatch(value) for value in expected.values()):
            raise ExternalContractError("output_postcondition_invalid")
        allowed_inputs = tuple(relative_path(path) for path in allowed_inputs)
        allowed_outputs = tuple(relative_path(path) for path in allowed_outputs)
        if not set(expected).issubset(allowed_outputs):
            raise ExternalContractError("output_postcondition_invalid")
        source = facts.get("managed_workspace")
        policy = facts.get("runtime_policy_evidence_sha256")
        if not isinstance(source, str) or not source or not isinstance(policy, str) or not _SHA256.fullmatch(policy):
            raise ExternalContractError("opencode_scope_policy_missing")
        environment = self._child_environment()
        staging_id = "staging_" + hashlib.sha256(f"{self._run_id}:{self._task_id}".encode()).hexdigest()[:24]
        try:
            staging = create_projected_staging(
                source_root=Path(source), staging_root=Path(source).parent / staging_id,
                allowed_inputs=allowed_inputs, allowed_outputs=allowed_outputs,
            )
        except Exception:
            self._prelaunch_no_effect = True
            raise
        config_fingerprint = _fingerprint({
            "executable": executable_digest(self._executable), "version": version,
            "argv": ("--pure", "acp"), "environment": {key: _fingerprint(value) for key, value in environment.items()},
            "plugin": "NONE", "mcp": "NONE", "skill": "NONE", "model": _FREE_MODEL,
        })
        permission_fingerprint = _fingerprint({
            "inputs": allowed_inputs, "outputs": allowed_outputs, "expected": expected,
            "policy": policy, "provider_model_egress": EgressDisposition.RUNTIME_MANAGED.value,
            "agent_extension_egress": EgressDisposition.DENY.value,
        })
        envelope = make_envelope(
            run_id=self._run_id, task_id=self._task_id, project_id=context.project_id,
            staging_root=staging, allowed_inputs=allowed_inputs, allowed_outputs=allowed_outputs,
            executable_path=self._executable, executable_version="opencode-" + version,
            arguments=("--pure", "acp"), config_sources=("cli.pure", "env.inline", "xdg.config.isolated"),
            egress={EgressChannel.PROVIDER_MODEL: EgressDisposition.RUNTIME_MANAGED,
                    EgressChannel.AGENT_EXTENSION: EgressDisposition.DENY},
            effective_runtime_configuration_fingerprint=config_fingerprint,
            permission_policy_fingerprint=permission_fingerprint,
            enabled_plugin_set=("NONE",), enabled_mcp_set=("NONE",),
            remote_skill_catalog_state="NONE", route_policy_evidence_sha256=policy,
        )
        runtime_ref = self._expected_runtime_ref or f"opencode-acp:{uuid4().hex}"
        self._runs[runtime_ref] = _ACPRun(context, envelope, self._task_id, context.project_id, expected)
        return runtime_ref

    async def submit(self, runtime_ref: str, task: Task) -> None:
        record = self._get(runtime_ref)
        if record.state is not RunState.CREATED or task.id != record.task_id or task.project_id != record.project_id:
            raise ExternalContractError("opencode_submit_scope_invalid")
        record.envelope.verify_staging()
        record.envelope.assert_quiescent_input()
        self._assert_configuration_unchanged(record)
        prompt = self._prompt(record, task)
        record.prompt_sha256 = hashlib.sha256(prompt.encode()).hexdigest()
        environment = self._child_environment()
        argv = [str(record.envelope.executable_path), *record.envelope.arguments]
        try:
            record.job = self._job_factory(argv, record.envelope.staging_root, environment)
            record.transport = ACPTransport(record.job)
            record.exchange = asyncio.create_task(self._exchange(record, prompt))
        except Exception as exc:
            raise ExternalContractError("opencode_process_start_failed") from exc
        record.state = RunState.RUNNING

    async def _exchange(self, record: _ACPRun, prompt: str) -> dict[str, object]:
        assert record.transport is not None
        try:
            initialize = await record.transport.initialize()
            session = await record.transport.new_session(str(record.envelope.staging_root))
            self._assert_free_model(session)
            terminal = await record.transport.prompt(prompt)
            record.terminal = {"protocolVersion": initialize["protocolVersion"],
                               "sessionId": record.transport.session_id or "", "stopReason": terminal["stopReason"]}
            return record.terminal
        finally:
            record.transport.close_input()

    @staticmethod
    def _assert_free_model(session: dict[str, object]) -> None:
        options = session.get("configOptions")
        if not isinstance(options, list):
            raise ExternalContractError("opencode_model_state_invalid")
        observed = False
        for option in options:
            if isinstance(option, dict) and option.get("category") == "model":
                observed = True
                current = option.get("currentValue")
                if current != _FREE_MODEL:
                    raise ExternalContractError("opencode_model_fallback_forbidden")
        if not observed:
            raise ExternalContractError("opencode_model_state_invalid")

    async def status(self, runtime_ref: str) -> RuntimeStatus:
        record = self._get(runtime_ref)
        if record.state in {RunState.CANCELLED, RunState.TIMED_OUT, RunState.FAILED, RunState.COMPLETED}:
            return RuntimeStatus(record.state)
        if record.exchange is not None and record.exchange.done():
            try:
                record.exchange.result()
            except Exception:
                record.state = RunState.FAILED
        return RuntimeStatus(record.state)

    async def result(self, runtime_ref: str) -> RuntimeResult:
        record = self._get(runtime_ref)
        if record.state is not RunState.RUNNING or record.exchange is None or record.job is None:
            raise ExternalContractError("opencode_result_unavailable")
        try:
            await record.exchange
            for _ in range(200):
                if record.job.stopped():break
                await asyncio.sleep(0.05)
            if not record.job.stopped():
                raise ExternalContractError("opencode_output_not_quiescent")
            facts = tuple(record.job.facts())
            if not facts or not all(bool(item.get("stopped")) for item in facts):
                raise ExternalContractError("opencode_cleanup_unverified")
            record.process_facts = facts
            record.exit_code = int(facts[0]["exit_code"])
            record.stdout, record.stderr = record.job.output()
            if record.exit_code != 0 or getattr(record.job, "_output_truncated", False):
                raise ExternalContractError("opencode_process_failed")
            self._assert_configuration_unchanged(record)
            record.envelope.verify_staging()
            record.envelope.assert_quiescent_input()
            diff, paths, before_hashes, after_hashes = await self._stable_diff(record)
            store = ContentStore(self._content_root)
            digest, size = store.put(diff)
            again, again_paths, _, again_hashes = await self._stable_diff(record)
            if again != diff or again_paths != paths or again_hashes != after_hashes:
                raise ExternalContractError("opencode_output_changed_during_import")
            artifact = Artifact(
                project_id=record.project_id, task_id=record.task_id, run_id=self._run_id,
                artifact_type=ArtifactType.CODE_DIFF, mime_type="text/x-diff",
                source_type="opencode.acp", storage_ref=f"core-blob:{digest}", sha256=digest, size=size,
            )
            evidence = Evidence(
                task_id=record.task_id, run_id=self._run_id or "", actor_id="runtime:opencode.acp",
                source="runtime.opencode.acp", type=EvidenceType.RUNTIME_EVIDENCE,
                status=EvidenceStatus.OBSERVED, artifact_refs=(artifact.id,),
                metadata={
                    "envelope_sha256": record.envelope.envelope_sha256,
                    "effective_runtime_configuration_fingerprint": record.envelope.effective_runtime_configuration_fingerprint,
                    "permission_policy_fingerprint": record.envelope.permission_policy_fingerprint,
                    "route_policy_evidence_sha256": record.envelope.route_policy_evidence_sha256,
                    "workspace_scope_mode": record.envelope.workspace_scope_mode,
                    "enabled_plugin_set": "NONE", "enabled_mcp_set": "NONE", "remote_skill_catalog_state": "NONE",
                    "executable_sha256": record.envelope.executable_sha256,
                    "executable_version": record.envelope.executable_version,
                    "cwd": str(record.envelope.staging_root), "argv_json": json.dumps(record.envelope.arguments),
                    "exit_code": str(record.exit_code), "protocol_version": "1",
                    "session_id_sha256": hashlib.sha256(record.terminal["sessionId"].encode()).hexdigest(),
                    "stop_reason": str(record.terminal["stopReason"]),
                    "source_changed_paths_json": json.dumps(paths),
                    "source_before_hashes_json": json.dumps(before_hashes, sort_keys=True),
                    "source_after_hashes_json": json.dumps(after_hashes, sort_keys=True),
                    "stdout_sha256": hashlib.sha256(record.stdout).hexdigest(),
                    "stderr_sha256": hashlib.sha256(record.stderr).hexdigest(),
                    "auth_ownership": AuthOwnership.RUNTIME_MANAGED.value,
                    "provider_model_egress": EgressDisposition.RUNTIME_MANAGED.value,
                    "agent_extension_egress": EgressDisposition.DENY.value,
                },
            )
            record.artifacts_value = (artifact,)
            record.state = RunState.COMPLETED
            record.result_value = RuntimeResult("OpenCode ACP produced an allowlisted source change", (evidence,), artifacts=(artifact,))
            return record.result_value
        except Exception as exc:
            record.state = RunState.FAILED
            if isinstance(exc, ExternalContractError):raise
            raise ExternalContractError("opencode_result_failed") from exc

    async def _stable_diff(self, record: _ACPRun) -> tuple[bytes, tuple[str, ...], dict[str, str], dict[str, str]]:
        staging = record.envelope.staging_root
        first = self._output_hashes(record)
        await asyncio.sleep(0.05)
        second = self._output_hashes(record)
        if first != second:
            raise ExternalContractError("opencode_output_not_quiescent")
        status = self._git(staging, "status", "--porcelain=v1", "-z", "--untracked-files=all")
        entries = tuple(item for item in status.split(b"\0") if item)
        changed: list[str] = []
        for entry in entries:
            if len(entry) < 4 or entry[:2] in {b"R ", b" R", b"C ", b" C"}:
                raise ExternalContractError("opencode_output_containment_failed")
            path = entry[3:].decode("utf-8", errors="strict")
            if path not in record.envelope.allowed_outputs:
                raise ExternalContractError("opencode_output_containment_failed")
            changed.append(path)
        if not changed:
            raise ExternalContractError("opencode_source_change_missing")
        diff = self._git(staging, "diff", "--binary", "HEAD", "--", *record.envelope.allowed_outputs)
        if not diff or len(diff) > _MAX_DIFF:
            raise ExternalContractError("opencode_source_change_missing")
        third = self._output_hashes(record)
        if third != second:
            raise ExternalContractError("opencode_output_changed_during_import")
        for path, expected in record.expected_output_hashes.items():
            if third.get(path) != expected:
                raise ExternalContractError("opencode_postcondition_missing")
        before = {path: hashlib.sha256(self._git(staging, "show", f"HEAD:{path}")).hexdigest()
                  for path in changed if path in record.envelope.allowed_inputs}
        return diff, tuple(sorted(changed)), before, third

    @staticmethod
    def _output_hashes(record: _ACPRun) -> dict[str, str]:
        hashes: dict[str, str] = {}
        for relative in record.envelope.allowed_outputs:
            path = record.envelope.staging_root / relative
            if path.is_symlink() or (path.exists() and not path.is_file()):
                raise ExternalContractError("opencode_output_containment_failed")
            if path.exists():
                hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        return hashes

    @staticmethod
    def _git(cwd: Path, *arguments: str) -> bytes:
        completed = subprocess.run(["git", *arguments], cwd=cwd, capture_output=True, check=False, timeout=15,
                                   env={"PATH": os.environ.get("PATH", ""), "GIT_CONFIG_GLOBAL": os.devnull,
                                        "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0"})
        if completed.returncode != 0:
            raise ExternalContractError("opencode_git_observation_failed")
        return completed.stdout

    def _assert_configuration_unchanged(self, record: _ACPRun) -> None:
        environment = self._child_environment()
        expected = _fingerprint({
            "executable": executable_digest(record.envelope.executable_path),
            "version": self._probe(), "argv": record.envelope.arguments,
            "environment": {key: _fingerprint(value) for key, value in environment.items()},
            "plugin": "NONE", "mcp": "NONE", "skill": "NONE", "model": _FREE_MODEL,
        })
        if expected != record.envelope.effective_runtime_configuration_fingerprint:
            raise ExternalContractError("opencode_config_fingerprint_drift")
        policy = _fingerprint({
            "inputs": record.envelope.allowed_inputs, "outputs": record.envelope.allowed_outputs,
            "expected": record.expected_output_hashes,
            "policy": record.envelope.route_policy_evidence_sha256,
            "provider_model_egress": EgressDisposition.RUNTIME_MANAGED.value,
            "agent_extension_egress": EgressDisposition.DENY.value,
        })
        if policy != record.envelope.permission_policy_fingerprint:
            raise ExternalContractError("opencode_policy_fingerprint_drift")

    @staticmethod
    def _prompt(record: _ACPRun, task: Task) -> str:
        text = task.title + "\n" + "\n".join(record.context.instructions)
        if _SECRET_LIKE.search(text) or len(text) > 12000:
            raise ExternalContractError("opencode_prompt_sensitive")
        return (text + "\nOnly inspect and edit these input/output paths in the current staging cwd: "
                + ", ".join(record.envelope.allowed_outputs)
                + ". Do not use bash, network tools, subagents, MCP, plugins, or skills.")

    async def cancel(self, runtime_ref: str) -> None:
        record = self._get(runtime_ref)
        if record.state in {RunState.CANCELLED, RunState.TIMED_OUT, RunState.COMPLETED}:
            return
        if record.job is None:
            raise ExternalContractError("opencode_process_handle_missing")
        if record.exchange is not None and not record.exchange.done():
            record.exchange.cancel()
        try:
            record.job.close_stdin()
            record.job.stop(timeout=10)
            record.exit_code = int(record.job.facts()[0]["exit_code"])
            record.state = record.cleanup_target
        except Exception as exc:
            raise ExternalContractError("opencode_process_stop_unverified") from exc

    async def resume(self, runtime_ref: str, checkpoint: str | None = None) -> None:
        del checkpoint
        self._get(runtime_ref)
        raise ExternalContractError("opencode_resume_unsupported")

    async def artifacts(self, runtime_ref: str) -> tuple[Artifact, ...]:
        return self._get(runtime_ref).artifacts_value

    async def cleanup(self, runtime_ref: str) -> bool:
        record = self._get(runtime_ref)
        if record.job is None:
            return False
        try:
            if not record.job.stopped():return False
            facts = tuple(record.job.facts())
            if not facts or not all(bool(item.get("stopped")) for item in facts):return False
            record.job.dispose()
            record.cleanup_verified = True
            return True
        except Exception:
            return False

    def set_cleanup_target(self, runtime_ref: str, target: RunState) -> None:
        if target not in {RunState.CANCELLED, RunState.TIMED_OUT}:
            raise ExternalContractError("cleanup_target_invalid")
        self._get(runtime_ref).cleanup_target = target

    def no_effect_failure_verified(self) -> bool:
        return self._prelaunch_no_effect

    def version_info(self) -> str:
        return "opencode-acp/" + self._probe()

    def _get(self, runtime_ref: str) -> _ACPRun:
        try:return self._runs[runtime_ref]
        except KeyError as exc:raise ExternalContractError("opencode_runtime_ref_unknown") from exc

    @staticmethod
    def _managed_job_factory(argv: list[str], cwd: Path, environment: dict[str, str]) -> object:
        return ControlledJob(argv, cwd, environment=environment, interactive=True)
