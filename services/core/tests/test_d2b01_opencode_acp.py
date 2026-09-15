"""D2B-01 bounded ACP/Core contract tests; real target is a separate gate."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from polynexus_core.domain.enums import RunState
from polynexus_core.domain.models import ContextPackage, Task
from polynexus_core.runtime.acp_transport import ACPTransport
from polynexus_core.runtime.external_contracts import ExternalContractError
from polynexus_core.runtime.opencode_acp import OpenCodeACPRuntimeAdapter
from polynexus_core.runtime.registry import build_default_registry
from polynexus_core.storage.content import ContentStore
from polynexus_core.workspace.ownership import ControlledJob


def _git(cwd: Path, *arguments: str) -> None:
    completed = subprocess.run(
        ["git", "-c", "user.name=d2b01", "-c", "user.email=d2b01@example.invalid", *arguments],
        cwd=cwd, capture_output=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode(errors="replace")


def _source(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    source.mkdir()
    (source / "bug.py").write_text("def answer():\n    return 41\n", encoding="utf-8")
    (source / "test_bug.py").write_text("from bug import answer\ndef test_answer(): assert answer() == 42\n", encoding="utf-8")
    _git(source, "init", "-b", "main")
    _git(source, "add", "bug.py", "test_bug.py")
    _git(source, "commit", "-m", "baseline")
    return source


def _context(source: Path, *, inputs=("bug.py",), outputs=("bug.py",), expected=True) -> ContextPackage:
    correct = hashlib.sha256(b"def answer():\n    return 42\n").hexdigest()
    return ContextPackage(
        project_id="project_1", version=1,
        instructions=("Fix answer() to return 42.",),
        project_facts={
            "managed_workspace": str(source),
            "workspace_scope_mode": "PROJECTED_STAGING",
            "allowed_input_paths": json.dumps(inputs),
            "allowed_output_paths": json.dumps(outputs),
            "required_output_sha256": json.dumps({"bug.py": correct} if expected else {}),
            "runtime_policy_evidence_sha256": hashlib.sha256(b"policy-allow").hexdigest(),
        },
    )


def _task() -> Task:
    return Task(id="task_1", project_id="project_1", title="Fix answer() to return 42", workflow_id="review-minimal", workflow_version=1)


class _ACPJob:
    def __init__(self, cwd: Path, *, mode="correct", exit_code=0) -> None:
        self.cwd = cwd
        self.mode = mode
        self.exit_code = exit_code
        self.lines: list[bytes] = []
        self.requests: list[dict] = []
        self.closed = False
        self.disposed = False
        self._output_truncated = False

    def send_line(self, payload: bytes) -> None:
        request = json.loads(payload)
        self.requests.append(request)
        method = request["method"]
        if method == "initialize":
            result = {"protocolVersion": 2 if self.mode == "version" else 1, "agentCapabilities": {}}
        elif method == "session/new":
            result = {"sessionId": "sess_1", "configOptions": [] if self.mode == "missing-model" else [{"category": "model", "currentValue": "opencode/paid-model" if self.mode == "fallback" else "opencode/mimo-v2.5-free"}]}
        elif method == "session/prompt":
            if self.mode == "correct":
                (self.cwd / "bug.py").write_bytes(b"def answer():\n    return 42\n")
            elif self.mode == "other-path":
                (self.cwd / "other.py").write_text("bad", encoding="utf-8")
            elif self.mode == "wrong-output":
                (self.cwd / "bug.py").write_bytes(b"def answer():\n    return 43\n")
            result = {"stopReason": "end_turn"}
        else:
            raise AssertionError(method)
        response = {"jsonrpc": "2.0", "id": request["id"], "result": result}
        if self.mode == "mismatch" and method == "session/prompt":
            response["id"] += 1
        if self.mode == "timeout" and method == "session/prompt":
            return
        if self.mode == "malformed" and method == "session/prompt":
            self.lines.append(b"not-json\n")
        else:
            self.lines.append(json.dumps(response).encode() + b"\n")

    def read_line(self, timeout: float) -> bytes:
        del timeout
        if self.lines:
            return self.lines.pop(0)
        raise TimeoutError("no ACP response")

    def close_stdin(self) -> None:
        self.closed = True

    def stopped(self) -> bool:
        return self.closed

    def facts(self) -> list[dict]:
        return [{"pid": 1, "stopped": self.closed, "exit_code": self.exit_code}]

    def output(self) -> tuple[bytes, bytes]:
        return b"ACP fixture observations", b""

    def stop(self, timeout=10) -> int:
        del timeout
        self.closed = True
        return self.exit_code

    def dispose(self) -> None:
        self.disposed = True


def _adapter(source: Path, tmp_path: Path, *, mode="correct", exit_code=0):
    captured: list[_ACPJob] = []

    def factory(_argv, cwd, _environment):
        job = _ACPJob(cwd, mode=mode, exit_code=exit_code)
        captured.append(job)
        return job

    adapter = OpenCodeACPRuntimeAdapter(
        executable=Path(sys.executable), content_root=tmp_path / "content",
        job_factory=factory, version_probe=lambda _path: "1.18.31",
    )
    adapter.bind_run_identity(run_id="run_1", task_id="task_1")
    return adapter, captured


async def _execute(adapter: OpenCodeACPRuntimeAdapter, context: ContextPackage):
    ref = await adapter.create_run(context)
    await adapter.submit(ref, _task())
    return ref, await adapter.result(ref)


def test_real_adapter_registers_without_implicit_fallback() -> None:
    registry = build_default_registry()
    profile = registry.resolve("opencode.acp.local")
    assert profile.adapter_id == "builtin.opencode.acp"
    assert registry.resolve("reference.local").adapter_id == "builtin.reference"
    with pytest.raises(Exception):
        registry.resolve("opencode.acp.unknown")


def test_acp_exchange_imports_only_allowlisted_diff_and_core_blob(tmp_path: Path) -> None:
    source = _source(tmp_path)
    adapter, jobs = _adapter(source, tmp_path)
    ref, result = asyncio.run(_execute(adapter, _context(source)))
    assert result.artifacts[0].storage_ref == "core-blob:" + result.artifacts[0].sha256
    assert b"return 42" in ContentStore(tmp_path / "content").read_artifact(result.artifacts[0])
    assert (source / "bug.py").read_text(encoding="utf-8").endswith("return 41\n")
    assert jobs[0].requests[0]["method"] == "initialize"
    assert jobs[0].requests[1]["params"]["cwd"] == str(jobs[0].cwd)
    assert jobs[0].requests[1]["params"]["mcpServers"] == []
    assert jobs[0].requests[2]["method"] == "session/prompt"
    assert result.evidence[0].metadata["exit_code"] == "0"
    assert asyncio.run(adapter.cleanup(ref)) is True


@pytest.mark.parametrize("mode,reason", [
    ("malformed", "acp_message_malformed"),
    ("timeout", "acp_response_timeout"),
    ("version", "acp_version_unsupported"),
    ("missing-model", "opencode_model_state_invalid"),
    ("mismatch", "acp_response_mismatch"),
    ("fallback", "opencode_model_fallback_forbidden"),
    ("other-path", "opencode_output_containment_failed"),
    ("wrong-output", "opencode_postcondition_missing"),
    ("no-change", "opencode_source_change_missing"),
])
def test_acp_and_output_fail_closed(tmp_path: Path, mode: str, reason: str) -> None:
    source = _source(tmp_path)
    adapter, jobs = _adapter(source, tmp_path, mode=mode)

    async def execute():
        ref = await adapter.create_run(_context(source))
        await adapter.submit(ref, _task())
        with pytest.raises(ExternalContractError, match=reason):
            await adapter.result(ref)
        assert (await adapter.status(ref)).state is RunState.FAILED
        assert jobs[0].closed

    asyncio.run(execute())


def test_child_nonzero_exit_is_not_success(tmp_path: Path) -> None:
    source = _source(tmp_path)
    adapter, _jobs = _adapter(source, tmp_path, exit_code=7)

    async def execute():
        ref = await adapter.create_run(_context(source))
        await adapter.submit(ref, _task())
        with pytest.raises(ExternalContractError, match="opencode_process_failed"):
            await adapter.result(ref)

    asyncio.run(execute())


def test_path_traversal_and_secret_like_prompt_are_rejected_before_launch(tmp_path: Path) -> None:
    source = _source(tmp_path)
    adapter, jobs = _adapter(source, tmp_path)

    async def execute():
        with pytest.raises(ExternalContractError, match="relative_path_invalid"):
            await adapter.create_run(_context(source, outputs=("../outside.py",)))
        safe = await adapter.create_run(_context(source))
        task = _task()
        task.title = "Use token in task"  # mutable Task fixture only
        with pytest.raises(ExternalContractError, match="opencode_prompt_sensitive"):
            await adapter.submit(safe, task)

    asyncio.run(execute())
    assert not jobs


def test_config_and_policy_fingerprint_drift_reject_before_dispatch(tmp_path: Path) -> None:
    source = _source(tmp_path)
    adapter, jobs = _adapter(source, tmp_path)

    async def execute():
        ref = await adapter.create_run(_context(source))
        record = adapter._get(ref)
        record.expected_output_hashes["bug.py"] = "0" * 64
        with pytest.raises(ExternalContractError, match="opencode_policy_fingerprint_drift"):
            await adapter.submit(ref, _task())
        record.expected_output_hashes["bug.py"] = hashlib.sha256(b"def answer():\n    return 42\n").hexdigest()
        original = adapter._configuration
        adapter._configuration = lambda: {"model": "opencode/paid-model"}
        try:
            with pytest.raises(ExternalContractError, match="opencode_config_fingerprint_drift"):
                await adapter.submit(ref, _task())
        finally:
            adapter._configuration = original

    asyncio.run(execute())
    assert not jobs


def test_unavailable_executable_is_explicit_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("POLYNEXUS_OPENCODE_EXECUTABLE", raising=False)
    monkeypatch.setattr("polynexus_core.runtime.opencode_acp.shutil.which", lambda _name: None)
    with pytest.raises(ExternalContractError, match="opencode_executable_unavailable"):
        OpenCodeACPRuntimeAdapter()


def test_session_notification_mismatch_and_agent_request_are_rejected() -> None:
    class QueueJob:
        def __init__(self, message):self.message = message
        def send_line(self, _payload):pass
        def read_line(self, _timeout):return json.dumps(self.message).encode()+b"\n"
    for message, reason in [
        ({"jsonrpc":"2.0","method":"session/update","params":{"sessionId":"wrong","update":{}}}, "acp_session_mismatch"),
        ({"jsonrpc":"2.0","id":44,"method":"session/request_permission","params":{}}, "acp_agent_request_unsupported"),
    ]:
        transport = ACPTransport(QueueJob(message))
        transport.session_id = "sess_1"
        with pytest.raises(ExternalContractError, match=reason):
            asyncio.run(transport.request("session/prompt", {}, timeout=1))


def test_cleanup_failure_is_reported_and_not_success(tmp_path: Path) -> None:
    source = _source(tmp_path)
    adapter, jobs = _adapter(source, tmp_path)

    async def execute():
        ref, _result = await _execute(adapter, _context(source))
        jobs[0].facts = lambda: [{"pid": 1, "stopped": False, "exit_code": 0}]
        assert await adapter.cleanup(ref) is False

    asyncio.run(execute())


def test_output_mutation_during_import_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = _source(tmp_path)
    adapter, _jobs = _adapter(source, tmp_path)
    original = ContentStore.put
    def changing(store, data):
        result = original(store, data)
        record = next(iter(adapter._runs.values()))
        (record.envelope.staging_root / "bug.py").write_bytes(b"def answer():\n    return 43\n")
        return result
    monkeypatch.setattr(ContentStore, "put", changing)

    async def execute():
        ref = await adapter.create_run(_context(source))
        await adapter.submit(ref, _task())
        with pytest.raises(ExternalContractError, match="opencode_postcondition_missing|opencode_output_changed_during_import"):
            await adapter.result(ref)

    asyncio.run(execute())


def test_extension_and_secret_controls_are_bound_before_dispatch(tmp_path: Path) -> None:
    source = _source(tmp_path)
    adapter, jobs = _adapter(source, tmp_path)

    async def execute():
        ref = await adapter.create_run(_context(source))
        record = adapter._get(ref)
        config = json.loads(adapter._child_environment()["OPENCODE_CONFIG_CONTENT"])
        assert config["plugin"] == [] and config["mcp"] == {}
        for tool in ("bash", "task", "skill", "webfetch", "websearch", "external_directory"):
            assert config["permission"][tool] == "deny"
        assert record.envelope.enabled_plugin_set == ("NONE",)
        assert record.envelope.enabled_mcp_set == ("NONE",)
        assert record.envelope.remote_skill_catalog_state == "NONE"
        assert record.envelope.arguments == ("--pure", "acp")
        assert not any("token" in arg or "sk-" in arg for arg in record.envelope.arguments)
        original = adapter._configuration
        adapter._configuration = lambda: {**original(), "plugin": ["unexpected"]}
        try:
            with pytest.raises(ExternalContractError, match="opencode_config_fingerprint_drift"):
                await adapter.submit(ref, _task())
        finally:
            adapter._configuration = original

    asyncio.run(execute())
    assert not jobs


@pytest.mark.skipif(os.name != "nt", reason="Windows retained Job handles are required")
def test_owned_duplex_job_exchanges_lines_and_verifies_stop(tmp_path: Path) -> None:
    job = ControlledJob(
        [sys.executable, "-u", "-c", "import sys; line=sys.stdin.readline(); sys.stdout.write(line); sys.stdout.flush()"],
        tmp_path, interactive=True,
    )
    try:
        job.send_line(b'{"jsonrpc":"2.0","id":1}\n')
        assert json.loads(job.read_line(5))["id"] == 1
        job.close_stdin()
        for _ in range(100):
            if job.stopped():break
            import time
            time.sleep(0.01)
        assert job.stopped()
        assert job.facts()[0]["exit_code"] == 0
        assert job.output()[0].endswith(b"\n")
    finally:
        job.dispose()
