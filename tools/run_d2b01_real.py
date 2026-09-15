"""Capture one bounded real OpenCode ACP bug-fix run and independent oracle.

The artifact root is local raw evidence. Publication must separately sanitize
personal paths and scan stdout/stderr before adding it to Git.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "core" / "src"))

from polynexus_core.domain.models import ContextPackage, Task  # noqa: E402
from polynexus_core.runtime.opencode_acp import OpenCodeACPRuntimeAdapter  # noqa: E402


def _captured(argv: list[str], cwd: Path) -> dict[str, object]:
    completed = subprocess.run(argv, cwd=cwd, capture_output=True, check=False, timeout=30)
    return {"argv": argv, "cwd": str(cwd), "exit": completed.returncode,
            "stdout": completed.stdout.decode(errors="replace"),
            "stderr": completed.stderr.decode(errors="replace")}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def _run(artifact_root: Path, executable: Path) -> dict[str, object]:
    source = artifact_root / "synthetic-source"
    source.mkdir(parents=True)
    bug = source / "bug.py"
    bug.write_bytes(b"def answer():\n    return 41\n")
    (source / "test_bug.py").write_bytes(
        b"from bug import answer\n\ndef test_answer_is_fixed():\n    assert answer() == 42\n"
    )
    init = _captured(["git", "init", "-b", "main"], source)
    add = _captured(["git", "add", "bug.py", "test_bug.py"], source)
    baseline = _captured([
        "git", "-c", "user.name=d2b01-real", "-c", "user.email=d2b01@example.invalid",
        "commit", "-m", "synthetic baseline",
    ], source)
    if any(item["exit"] != 0 for item in (init, add, baseline)):
        raise RuntimeError("synthetic Git baseline failed")
    before = _sha(bug)
    baseline_test = _captured([
        sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_bug.py",
    ], source)
    context = ContextPackage(
        project_id="d2b01-real-project", version=1,
        instructions=("Change only bug.py: replace return 41 with return 42. Preserve the file's LF line endings. Do not change any other file.",),
        project_facts={
            "managed_workspace": str(source),
            "workspace_scope_mode": "PROJECTED_STAGING",
            "allowed_input_paths": json.dumps(["bug.py", "test_bug.py"]),
            "allowed_output_paths": json.dumps(["bug.py"]),
            "required_output_sha256": json.dumps({
                "bug.py": hashlib.sha256(b"def answer():\n    return 42\n").hexdigest(),
            }),
            "runtime_policy_evidence_sha256": hashlib.sha256(b"d2b01-free-model-policy").hexdigest(),
        },
    )
    task = Task(
        id="d2b01-real-task", project_id=context.project_id,
        title="Fix the synthetic answer function in bug.py",
        workflow_id="review-minimal", workflow_version=1,
    )
    adapter = OpenCodeACPRuntimeAdapter(executable=executable, content_root=artifact_root / "core-content")
    adapter.bind_run_identity(run_id="d2b01-real-run", task_id=task.id)
    runtime_ref = await adapter.create_run(context)
    record = adapter._get(runtime_ref)
    result_status = "FAIL"
    error = ""
    result = None
    try:
        await adapter.submit(runtime_ref, task)
        result = await asyncio.wait_for(adapter.result(runtime_ref), timeout=180)
        result_status = "PASS"
    except Exception as exc:
        error = type(exc).__name__ + ":" + str(exc)
        if record.job is not None and not record.job.stopped():
            await adapter.cancel(runtime_ref)
    finally:
        if record.job is not None and record.job.stopped():
            try:
                stdout, stderr = record.job.output()
                (artifact_root / "acp.stdout.jsonl").write_bytes(stdout)
                (artifact_root / "acp.stderr.log").write_bytes(stderr)
            except Exception:
                pass
        cleanup = await adapter.cleanup(runtime_ref) if record.job is not None else False
    staging_bug = record.envelope.staging_root / "bug.py"
    after = _sha(staging_bug) if staging_bug.is_file() else None
    post = _captured([
        sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_bug.py",
    ], record.envelope.staging_root) if result_status == "PASS" else None
    if post is not None:
        (artifact_root / "postcondition.stdout.log").write_text(post["stdout"], encoding="utf-8")
        (artifact_root / "postcondition.stderr.log").write_text(post["stderr"], encoding="utf-8")
    changed = _captured(["git", "status", "--porcelain=v1", "--untracked-files=all"], record.envelope.staging_root)
    return {
        "status": result_status, "error": error,
        "executable": str(executable), "version": adapter.version_info(),
        "executable_sha256": record.envelope.executable_sha256,
        "source_cwd": str(source), "staging_cwd": str(record.envelope.staging_root),
        "source_before_sha256": before, "staging_after_sha256": after,
        "original_source_unchanged": _sha(bug) == before,
        "actual_changed_paths": changed,
        "terminal": record.terminal, "child_exit": record.exit_code,
        "process_facts": record.process_facts,
        "cleanup_verified": cleanup, "session_update_count": len(record.transport.events) if record.transport else 0,
        "baseline_test": baseline_test, "postcondition_test": post,
        "artifact_sha256": result.artifacts[0].sha256 if result else None,
        "evidence_metadata": dict(result.evidence[0].metadata) if result else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--executable", required=True, type=Path)
    args = parser.parse_args()
    artifact_root = args.artifact_root.resolve(strict=False)
    if artifact_root.exists():
        raise RuntimeError("artifact root must be new")
    artifact_root.mkdir(parents=True)
    result = asyncio.run(_run(artifact_root, args.executable.resolve(strict=True)))
    (artifact_root / "real-run.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print("REAL_TARGET_STATUS=" + result["status"])
    print("REAL_TARGET_CHILD_EXIT=" + str(result["child_exit"]))
    print("REAL_TARGET_POSTCONDITION_EXIT=" + str(result["postcondition_test"]["exit"] if result["postcondition_test"] else "NOT_RUN"))
    print("REAL_TARGET_CLEANUP=" + str(result["cleanup_verified"]))
    return 0 if result["status"] == "PASS" and result["postcondition_test"] and result["postcondition_test"]["exit"] == 0 and result["cleanup_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
