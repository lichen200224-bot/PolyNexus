"""D2a contract tests for the fresh external-envelope/Codex target path.

These tests are deterministic contract tests.  They do not substitute for the
real installed-executor W2 gate, which is recorded separately with its actual
CLI result.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from polynexus_core.domain.enums import RunState
from polynexus_core.domain.models import ContextPackage, Run, Task
from polynexus_core.runtime.codex_exec import CodexExecRuntimeAdapter
from polynexus_core.extensions.manifest import ModuleError
from polynexus_core.runtime.external_contracts import (
    EgressChannel,
    EgressDisposition,
    ExecutionEnvelope,
    ExternalContractError,
    create_projected_staging,
    make_envelope,
)
from polynexus_core.storage.content import ContentStore
from polynexus_core.runtime.registry import build_default_registry
from polynexus_core.runtime.supervisor import RunSupervisor
from polynexus_core.workspace.ownership import ControlledJob


class _FakeJob:
    def __init__(self, argv: list[str], cwd: Path, *, changed_path: str | None = "bug.py") -> None:
        self.argv = argv
        self.cwd = cwd
        self.changed_path = changed_path
        self._stopped = False
        self._disposed = False
        if changed_path is not None:
            (cwd / changed_path).write_text("def answer():\n    return 42\n", encoding="utf-8")
        self._stopped = True

    def stopped(self) -> bool:
        return self._stopped

    def stop(self, timeout: int = 10) -> int:
        del timeout
        self._stopped = True
        return 0

    def facts(self) -> list[dict[str, object]]:
        return [{"pid": 1, "exit_code": 0, "stopped": self._stopped}]

    def output(self) -> tuple[bytes, bytes]:
        return b'{"type":"turn.completed"}\n', b""

    def dispose(self) -> None:
        self._disposed = True


class _LongJob(_FakeJob):
    def __init__(self, argv: list[str], cwd: Path) -> None:
        self.argv = argv
        self.cwd = cwd
        self.changed_path = None
        self._stopped = False
        self._disposed = False


class _MalformedResultJob(_FakeJob):
    def output(self) -> tuple[bytes, bytes]:
        return b"not-json\n", b""


def _git(cwd: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", "-c", "user.name=d2a", "-c", "user.email=d2a@example.invalid", *args],
        cwd=cwd,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")


def _repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "bug.py").write_text("def answer():\n    return 41\n", encoding="utf-8")
    (repo / "test_bug.py").write_text("assert True\n", encoding="utf-8")
    _git(repo, "init", "-b", "main")
    _git(repo, "add", "bug.py", "test_bug.py")
    _git(repo, "commit", "-m", "baseline")
    return repo, tmp_path / "content"


def _adapter(
    repo: Path,
    content: Path,
    *,
    changed_path: str | None = "bug.py",
) -> CodexExecRuntimeAdapter:
    executable = Path(sys.executable)
    return CodexExecRuntimeAdapter(
        executable=executable,
        content_root=content,
        version_probe=lambda _path: "codex-cli-0.0.0",
        job_factory=lambda argv, cwd: _FakeJob(argv, cwd, changed_path=changed_path),
    )


def _context(
    repo: Path,
    *,
    paths: tuple[str, ...] = ("bug.py",),
    output_paths: tuple[str, ...] | None = None,
) -> ContextPackage:
    outputs = output_paths or paths
    staging = create_projected_staging(
        source_root=repo,
        staging_root=repo.parent / "projected-staging",
        allowed_inputs=paths,
        allowed_outputs=outputs,
    )
    return ContextPackage(
        project_id="project_1",
        version=1,
        instructions=("Fix the failing synthetic test.",),
        project_facts={
            "projected_staging": str(staging),
            "allowed_input_paths": json.dumps(paths),
            "allowed_output_paths": json.dumps(outputs),
            "runtime_policy_evidence_sha256": hashlib.sha256(
                b"synthetic-policy-allow"
            ).hexdigest(),
        },
    )


def _task() -> Task:
    return Task(
        id="task_1",
        project_id="project_1",
        title="Fix the synthetic bug",
        workflow_id="review-minimal",
        workflow_version=1,
    )


def test_envelope_is_immutable_and_scoped_to_allowlisted_paths(tmp_path: Path) -> None:
    repo, _content = _repo(tmp_path)
    executable = Path(sys.executable)
    envelope = make_envelope(
        run_id="run_1",
        task_id="task_1",
        project_id="project_1",
        staging_root=repo,
        allowed_inputs=("bug.py",),
        allowed_outputs=("bug.py",),
        executable_path=executable,
        executable_version="codex-cli-0.0.0",
        arguments=("exec", "--sandbox", "workspace-write"),
        config_sources=("cli.flags",),
        egress={
            EgressChannel.PROVIDER_MODEL: EgressDisposition.RUNTIME_MANAGED,
            EgressChannel.AGENT_EXTENSION: EgressDisposition.DENY,
        },
    )
    assert len(envelope.envelope_sha256) == 64
    with pytest.raises(TypeError):
        envelope.egress[EgressChannel.PROVIDER_MODEL] = EgressDisposition.DENY  # type: ignore[index]
    with pytest.raises(AttributeError):
        envelope.allowed_outputs = ("other.py",)  # type: ignore[misc]
    with pytest.raises(ExternalContractError, match="relative_path"):
        make_envelope(
            run_id="run_1",
            task_id="task_1",
            project_id="project_1",
            staging_root=repo,
            allowed_inputs=("../bug.py",),
            allowed_outputs=("../bug.py",),
            executable_path=executable,
            executable_version="codex-cli-0.0.0",
            arguments=(),
            config_sources=(),
            egress={
                EgressChannel.PROVIDER_MODEL: EgressDisposition.RUNTIME_MANAGED,
                EgressChannel.AGENT_EXTENSION: EgressDisposition.DENY,
            },
        )


def test_codex_adapter_observes_real_allowlisted_diff_and_core_blob(tmp_path: Path) -> None:
    repo, content = _repo(tmp_path)
    adapter = _adapter(repo, content)
    task = _task()
    context = _context(repo)
    adapter.bind_run_identity(run_id="run_1", task_id=task.id)

    async def execute():
        runtime_ref = await adapter.create_run(context)
        await adapter.submit(runtime_ref, task)
        assert (await adapter.status(runtime_ref)).state is RunState.RUNNING
        result = await adapter.result(runtime_ref)
        assert result.artifacts
        assert result.artifacts[0].storage_ref == "core-blob:" + result.artifacts[0].sha256
        assert result.artifacts[0].run_id == "run_1"
        assert result.evidence[0].metadata["source_before_manifest_sha256"] != result.evidence[0].metadata["source_after_manifest_sha256"]
        assert await adapter.cleanup(runtime_ref) is True
        assert (await adapter.status(runtime_ref)).state is RunState.COMPLETED
        return result

    result = asyncio.run(execute())
    artifact = result.artifacts[0]
    diff = ContentStore(content).read_artifact(artifact)
    assert b"return 42" in diff
    assert artifact.sha256 == hashlib.sha256(diff).hexdigest()


def test_codex_adapter_rejects_non_allowlisted_change_and_resume(tmp_path: Path) -> None:
    repo, content = _repo(tmp_path)
    adapter = _adapter(repo, content, changed_path="test_bug.py")
    task = _task()
    adapter.bind_run_identity(run_id="run_2", task_id=task.id)

    async def execute():
        ref = await adapter.create_run(_context(repo))
        await adapter.submit(ref, task)
        with pytest.raises(ExternalContractError, match="allowlisted_source_change_missing"):
            await adapter.result(ref)
        with pytest.raises(ExternalContractError, match="resume"):
            await adapter.resume(ref)
        return ref

    ref = asyncio.run(execute())
    assert asyncio.run(adapter.status(ref)).state is RunState.FAILED


def test_timeout_cleanup_target_is_private_and_distinct_from_cancel(tmp_path: Path) -> None:
    repo, content = _repo(tmp_path)
    adapter = _adapter(repo, content)
    task = _task()
    adapter.bind_run_identity(run_id="run_3", task_id=task.id)

    async def execute():
        ref = await adapter.create_run(_context(repo))
        await adapter.submit(ref, task)
        adapter.set_cleanup_target(ref, RunState.TIMED_OUT)
        await adapter.cancel(ref)
        assert (await adapter.status(ref)).state is RunState.TIMED_OUT
        assert await adapter.cleanup(ref) is True

    asyncio.run(execute())


def test_output_mutation_between_quiescence_reads_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, content = _repo(tmp_path)
    adapter = _adapter(repo, content)
    task = _task()
    adapter.bind_run_identity(run_id="run_4", task_id=task.id)
    calls = 0
    original = adapter._git_diff

    def changing(record):
        nonlocal calls
        calls += 1
        current = original(record)
        if calls == 1:
            (record.envelope.staging_root / "bug.py").write_text("def answer():\n    return 43\n", encoding="utf-8")
        return current

    monkeypatch.setattr(adapter, "_git_diff", changing)

    async def execute():
        ref = await adapter.create_run(_context(repo))
        await adapter.submit(ref, task)
        with pytest.raises(ExternalContractError, match="output_changed_during_import"):
            await adapter.result(ref)

    asyncio.run(execute())


def test_codex_adapter_separates_empty_inputs_from_approved_outputs(tmp_path: Path) -> None:
    repo, content = _repo(tmp_path)
    adapter = _adapter(repo, content)
    task = _task()
    adapter.bind_run_identity(run_id="run_5", task_id=task.id)

    async def execute():
        context = _context(repo, paths=(), output_paths=("bug.py",))
        ref = await adapter.create_run(context)
        await adapter.submit(ref, task)
        result = await adapter.result(ref)
        assert result.artifacts

    asyncio.run(execute())


def test_codex_adapter_rejects_malformed_json_result(tmp_path: Path) -> None:
    repo, content = _repo(tmp_path)
    adapter = CodexExecRuntimeAdapter(
        executable=Path(sys.executable),
        content_root=content,
        version_probe=lambda _path: "codex-cli-0.0.0",
        job_factory=lambda argv, cwd: _MalformedResultJob(argv, cwd),
    )
    task = _task()
    adapter.bind_run_identity(run_id="run_malformed", task_id=task.id)

    async def execute():
        ref = await adapter.create_run(_context(repo))
        await adapter.submit(ref, task)
        with pytest.raises(ExternalContractError, match="codex_result_malformed"):
            await adapter.result(ref)
        return ref

    ref = asyncio.run(execute())
    assert asyncio.run(adapter.status(ref)).state is RunState.FAILED


def test_projected_staging_rejects_nested_reparse_path(tmp_path: Path) -> None:
    repo, _content = _repo(tmp_path)
    nested = repo / "nested"
    nested.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        os.symlink(outside, nested / "linked", target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is unavailable in this Windows test environment")
    with pytest.raises(ExternalContractError, match="path_(escape|reparse_unsupported)"):
        create_projected_staging(
            source_root=repo,
            staging_root=repo.parent / "projected-reparse",
            allowed_inputs=("nested/linked/bug.py",),
            allowed_outputs=("nested/linked/bug.py",),
        )


def test_controlled_job_observes_output_and_excludes_unallowlisted_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("POLYNEXUS_TEST_SECRET", "must-not-cross-child-boundary")
    script = (
        "import os,sys;"
        "print('stdout-observed');"
        "print('stderr-observed', file=sys.stderr);"
        "print('secret-present' if 'POLYNEXUS_TEST_SECRET' in os.environ else 'secret-absent')"
    )
    job = ControlledJob([sys.executable, "-B", "-c", script], tmp_path)
    deadline = time.monotonic() + 10
    while not job.stopped():
        assert time.monotonic() < deadline
        time.sleep(0.01)
    facts = job.facts()
    stdout, stderr = job.output()
    job.dispose()
    assert facts and facts[0]["stopped"] is True
    assert b"stdout-observed" in stdout
    assert b"stderr-observed" in stderr
    assert b"secret-absent" in stdout


def test_supervisor_timeout_sets_target_terminal_state_and_verifies_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, content = _repo(tmp_path)
    adapter = CodexExecRuntimeAdapter(
        executable=Path(sys.executable),
        content_root=content,
        version_probe=lambda _path: "codex-cli-0.0.0",
        job_factory=_LongJob,
    )
    task = _task()
    context = _context(repo)
    from polynexus_core.workflows.models import WorkflowDefinition, WorkflowStep

    workflow = WorkflowDefinition(
        id=task.workflow_id,
        version=task.workflow_version,
        steps=(WorkflowStep(id="step", type="TOOL"),),
    )
    monkeypatch.setattr("polynexus_core.runtime.supervisor._DEFAULT_OPERATION_TIMEOUT_SECONDS", 0.01)
    run = Run(
        task_id=task.id,
        workflow_id=workflow.id,
        workflow_version=workflow.version,
        context_package_id=context.id,
    )
    execution = asyncio.run(RunSupervisor(adapter).execute_run(run, task, context, workflow))
    assert execution.run.state is RunState.TIMED_OUT


def test_static_codex_module_uses_existing_registry_and_isolation() -> None:
    registry = build_default_registry()
    modules = registry.static_module_registry  # type: ignore[attr-defined]
    assert modules.contains("module.codex")
    assert registry.resolve("codex.local").adapter_id == "builtin.codex.exec"
    modules.set_enabled("module.codex", False)
    with pytest.raises(ModuleError):
        registry.create_adapter(registry.resolve("codex.local"))
    assert registry.create_adapter(registry.resolve("reference.local")) is not None
