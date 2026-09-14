"""B01-TECH evidence tests.

The real-executor source change is driven by ``tools/run_b01_tech.ps1``.  The
tests in this module cover the Core-owned reliability and portability seams
that the runner must prove.  They use real Windows Job Objects and child
processes; they do not use a PID scan, a cancellation flag, or a fake runtime
for the process-tree evidence.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from polynexus_core.domain.enums import RunState
from polynexus_core.domain.generation import GenerationConflict, WorkGenerationRef
from polynexus_core.domain.models import ContextPackage, Project, Run, Task
from polynexus_core.persistence.generation import GenerationRepository
from polynexus_core.persistence.repository import (
    SqlContextPackageRepository,
    SqlProjectRepository,
    SqlTaskRepository,
)
from polynexus_core.runtime.codex_exec import CodexExecRuntimeAdapter
from polynexus_core.runtime.supervisor import RunSupervisor
from polynexus_core.storage.content import ContentStore
from polynexus_core.workflows.models import WorkflowDefinition, WorkflowStep
from polynexus_core.workspace.ownership import ControlledJob, OwnedProcessRegistry

from test_d1b_candidate_evidence_human_p0 import (
    _add_scoped_publication,
    _candidate,
    _enrollment_proof,
    _observation,
    _upgrade as _upgrade_d1b,
    d1b_db,
)


def _emit(name: str, value: object) -> None:
    root_value = os.environ.get("B01_EVIDENCE_DIR")
    if not root_value:
        return
    root = Path(root_value)
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


@pytest.fixture()
def b01_generation_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("POLYNEXUS_CONTENT_ROOT", str(tmp_path / "content"))
    database = tmp_path / "generation.db"
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
    config.set_main_option("sqlalchemy.url", "sqlite:///" + database.as_posix())
    command.upgrade(config, "head")
    engine = create_engine("sqlite:///" + database.as_posix(), future=True)
    with Session(engine) as session:
        project = Project(name="b01-synthetic")
        SqlProjectRepository(session).add(project)
        session.flush()
        context = ContextPackage(project_id=project.id, version=1)
        SqlContextPackageRepository(session).add(context)
        session.flush()
        task = Task(
            project_id=project.id,
            title="B01 synthetic process tree",
            workflow_id="review-minimal",
            workflow_version=1,
            context_package_id=context.id,
        )
        SqlTaskRepository(session).add(task)
        session.flush()
        prepared = GenerationRepository(session).prepare(
            task_id=task.id,
            context_package_id=context.id,
            requirements="B01 synthetic requirements",
            validation="B01 synthetic validation",
        )
        session.commit()
        yield session, task, prepared, tmp_path
    engine.dispose()


def _launch_real_tree(root: Path, label: str) -> tuple[ControlledJob, Path]:
    """Launch a root -> child process tree and retain the child by handle."""

    ready = root / f"{label}-child.json"
    grandchild_ready = root / f"{label}-grandchild.json"
    grandchild_code = "import time; time.sleep(90)"
    child_code = (
        "import json,subprocess,sys,time;"
        "from pathlib import Path;"
        f"grandchild=subprocess.Popen([sys.executable,'-c',{grandchild_code!r}]);"
        "Path(sys.argv[1]).write_text(json.dumps({'pid':grandchild.pid}),encoding='utf-8');"
        "time.sleep(90)"
    )
    root_code = (
        "import json,subprocess,sys,time;"
        "from pathlib import Path;"
        f"child=subprocess.Popen([sys.executable,'-c',{child_code!r},sys.argv[2]]);"
        "Path(sys.argv[1]).write_text(json.dumps({'pid':child.pid}),encoding='utf-8');"
        "time.sleep(90)"
    )
    job = ControlledJob(
        [sys.executable, "-B", "-c", root_code, str(ready), str(grandchild_ready)],
        root,
    )
    deadline = time.monotonic() + 10
    while not ready.exists() or not grandchild_ready.exists():
        if time.monotonic() >= deadline:
            job.stop(timeout=10)
            job.dispose()
            raise AssertionError("owned child readiness timeout")
        time.sleep(0.02)
    child_pid = json.loads(ready.read_text(encoding="utf-8"))["pid"]
    job.retain_descendant(int(child_pid))
    grandchild_pid = json.loads(grandchild_ready.read_text(encoding="utf-8"))["pid"]
    job.retain_descendant(int(grandchild_pid))
    return job, ready


def _facts(job: ControlledJob) -> list[dict[str, object]]:
    facts = job.facts()
    assert len(facts) == 3
    assert all(item["stopped"] is True for item in facts)
    assert all(int(item["ended_filetime"]) > 0 for item in facts)
    return facts


def test_b01_failure_retry_recovery_and_late_abort_are_fenced(
    b01_generation_db,
):
    session, task, prepared, tmp_path = b01_generation_db
    generations = GenerationRepository(session)
    owners = OwnedProcessRegistry()
    jobs: list[ControlledJob] = []
    evidence: dict[str, object] = {"case": "B01-FAILURE-RETRY-RECOVERY"}

    generations.begin(
        principal="test-only:b01",
        command_id="b01-begin-g1",
        task_id=task.id,
        expected_revision=0,
        inputs=prepared,
    )
    session.commit()
    g1 = WorkGenerationRef(task.id, 1)
    run1 = generations.create_run(
        principal="test-only:b01",
        command_id="b01-run-g1",
        task_id=task.id,
        revision=1,
        context_package_id=prepared["context_package_id"],
        expected_control=0,
    )
    claim1 = generations.claim(
        g1,
        run_id=run1.id,
        lineage="b01:" + run1.id,
        expected_control=0,
    )
    session.commit()
    job1, _ready1 = _launch_real_tree(tmp_path, "g1")
    jobs.append(job1)
    owners.register_controlled_job(g1, run1.id, claim1["fence"], job1)
    before_cancel = job1.facts()
    assert all(item["stopped"] is False for item in before_cancel)

    with pytest.raises(GenerationConflict, match="owned_handle_unknown"):
        owners.cancel(g1, run1.id, claim1["fence"] + 1)
    owners.cancel(g1, run1.id, claim1["fence"])
    after_cancel = _facts(job1)
    session.execute(
        text("UPDATE runs SET state='CANCELLED' WHERE id=:run_id"),
        {"run_id": run1.id},
    )
    generations.close(
        g1,
        run_id=run1.id,
        fence=claim1["fence"],
        owned_processes=owners,
    )
    session.commit()

    generations.begin(
        principal="test-only:b01",
        command_id="b01-begin-g2",
        task_id=task.id,
        expected_revision=1,
        inputs=prepared,
        predecessor=1,
    )
    session.commit()
    g2 = WorkGenerationRef(task.id, 2)
    run2 = generations.create_run(
        principal="test-only:b01",
        command_id="b01-run-g2",
        task_id=task.id,
        revision=2,
        context_package_id=prepared["context_package_id"],
        expected_control=0,
    )
    claim2 = generations.claim(
        g2,
        run_id=run2.id,
        lineage="b01:" + run2.id,
        expected_control=0,
    )
    session.commit()
    job2, _ready2 = _launch_real_tree(tmp_path, "g2")
    jobs.append(job2)
    owners.register_controlled_job(g2, run2.id, claim2["fence"], job2)
    g2_before_late_abort = generations.observe(g2)
    g2_facts_before_late_abort = job2.facts()

    late_abort = generations.abort(
        g1,
        principal="test-only:b01",
        command_id="b01-late-abort-g1",
        expected_control=generations.get(g1)["control_revision"],
    )
    session.commit()
    assert late_abort["generation_revision"] == 1
    late_abort_generation_unchanged = generations.observe(g2) == g2_before_late_abort
    late_abort_process_facts_unchanged = job2.facts() == g2_facts_before_late_abort
    assert late_abort_generation_unchanged
    assert late_abort_process_facts_unchanged

    owners.cancel(g2, run2.id, claim2["fence"])
    after_retry_cleanup = _facts(job2)
    session.execute(
        text("UPDATE runs SET state='CANCELLED' WHERE id=:run_id"),
        {"run_id": run2.id},
    )
    generations.close(
        g2,
        run_id=run2.id,
        fence=claim2["fence"],
        owned_processes=owners,
    )
    session.commit()

    evidence.update(
        {
            "old": {
                "generation": 1,
                "run_id": run1.id,
                "fence": claim1["fence"],
                "before_cancel": before_cancel,
                "after_cleanup": after_cancel,
            },
            "new": {
                "generation": 2,
                "run_id": run2.id,
                "fence": claim2["fence"],
                "after_cleanup": after_retry_cleanup,
            },
            "late_abort": {
                "target_generation": 1,
                "target_run_id": run1.id,
                "new_generation_unchanged": late_abort_generation_unchanged,
                "new_run_process_facts_unchanged": late_abort_process_facts_unchanged,
                "new_generation_before_late_abort": g2_before_late_abort,
                "new_run_process_facts_before_late_abort": g2_facts_before_late_abort,
                "control_revision": generations.get(g1)["control_revision"],
            },
            "ownership": {
                "old_fence": claim1["fence"],
                "new_fence": claim2["fence"],
                "fence_increased": claim2["fence"] > claim1["fence"],
                "principal": "TEST_ONLY:test-only:b01",
            },
            "runner_exit": "recorded by pytest wrapper",
            "child_exit_evidence": [
                item["exit_code"] for item in after_cancel + after_retry_cleanup
            ],
        }
    )
    _emit("failure-retry-recovery.json", evidence)
    try:
        assert evidence["ownership"]["fence_increased"] is True
    finally:
        for job in jobs:
            if not job.stopped():
                job.stop(timeout=10)
            job.dispose()


def test_b01_real_process_tree_timeout_has_terminal_run_and_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    source = tmp_path / "timeout-source"
    source.mkdir()
    (source / "bug.py").write_text("def answer():\n    return 41\n", encoding="utf-8")
    (source / "test_bug.py").write_text(
        "from bug import answer\nassert answer() == 42\n", encoding="utf-8"
    )
    _git(source, "init", "-b", "main")
    _git(source, "add", "bug.py", "test_bug.py")
    _git(source, "commit", "-m", "timeout-baseline")

    task = Task(
        id="b01-timeout-task",
        project_id="b01-timeout-project",
        title="B01 timeout tree",
        workflow_id="review-minimal",
        workflow_version=1,
    )
    context = ContextPackage(
        id="b01-timeout-context",
        project_id=task.project_id,
        version=1,
        instructions=("Hold a real owned process tree until the supervisor deadline.",),
        project_facts={
            "managed_workspace": str(source),
            "workspace_scope_mode": "PROJECTED_STAGING",
            "allowed_input_paths": json.dumps(("bug.py", "test_bug.py")),
            "allowed_output_paths": json.dumps(("bug.py",)),
            "runtime_policy_evidence_sha256": hashlib.sha256(b"b01-timeout-policy").hexdigest(),
        },
    )
    workflow = WorkflowDefinition(
        id=task.workflow_id,
        version=task.workflow_version,
        steps=(WorkflowStep(id="b01-timeout", type="TOOL"),),
    )
    jobs: list[ControlledJob] = []

    def factory(_argv: list[str], cwd: Path) -> ControlledJob:
        job, _ready = _launch_real_tree(cwd, "timeout")
        jobs.append(job)
        return job

    adapter = CodexExecRuntimeAdapter(
        executable=Path(sys.executable),
        content_root=tmp_path / "content",
        version_probe=lambda _path: "b01-test-runtime",
        job_factory=factory,
    )
    monkeypatch.setattr(
        "polynexus_core.runtime.supervisor._DEFAULT_OPERATION_TIMEOUT_SECONDS",
        0.25,
    )
    run = Run(
        id="b01-timeout-run",
        task_id=task.id,
        workflow_id=workflow.id,
        workflow_version=workflow.version,
        context_package_id=context.id,
    )
    execution = asyncio.run(RunSupervisor(adapter).execute_run(run, task, context, workflow))
    assert execution.run.state is RunState.TIMED_OUT
    assert len(jobs) == 1
    timeout_facts = _facts(jobs[0])
    evidence = {
        "case": "B01-PROCESS-TREE-TIMEOUT",
        "run_id": run.id,
        "runtime_state": execution.run.state.value,
        "deadline_seconds": 0.25,
        "owned_process_facts": timeout_facts,
        "all_owned_handles_stopped": all(item["stopped"] is True for item in timeout_facts),
        "all_owned_handles_have_end_observation": all(
            int(item["ended_filetime"]) > 0 for item in timeout_facts
        ),
        "runner_exit": "recorded by pytest wrapper",
        "child_exit_evidence": [item["exit_code"] for item in timeout_facts],
        "pid_scan_used_as_oracle": False,
        "flag_used_as_oracle": False,
    }
    _emit("process-tree-timeout.json", evidence)
    jobs[0].dispose()


def _git(cwd: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", "-c", "user.name=b01-test", "-c", "user.email=b01@example.invalid", *args],
        cwd=cwd,
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def _source_hashes(root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != ".polynexus-working-copy.json":
            values[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return values


def test_b01_p0_accept_open_verify_and_offline_reconstruct_is_byte_identical(
    d1b_db,
    monkeypatch: pytest.MonkeyPatch,
):
    session, store, tmp_path = d1b_db
    repo = __import__("polynexus_core.persistence.d1b", fromlist=["D1bRepository"]).D1bRepository(
        session, store
    )
    published = _add_scoped_publication(repo, _candidate(repo), suffix="b01")
    candidate_id = published["candidate_id"]
    contract_id = published["validation_contract_snapshot_id"]
    repo.verify_candidate(
        candidate_id=candidate_id,
        contract_id=contract_id,
        observations=[_observation(candidate_id, contract_id=contract_id)],
        trusted_runner="core-test:pytest",
    )
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(hours=1)
    proof = _enrollment_proof("test-only:b01-human", expiry, issued_at=now)
    pairing = repo.create_pairing(
        principal_ref="test-only:b01-human",
        enrollment_proof=proof,
        expires_at=expiry,
    )
    session_info = repo.create_session(
        grant_id=pairing["grant_id"],
        pairing_proof=proof,
        audience="ui",
        csrf_token="b01-csrf",
        now=now,
    )
    challenge = repo.issue_challenge(
        session_id=session_info["session_id"],
        candidate_id=candidate_id,
        action="Accept",
        now=now,
    )
    accepted = repo.submit_decision(
        session_id=session_info["session_id"],
        challenge_id=challenge["challenge_id"],
        nonce=challenge["nonce"],
        action="Accept",
        candidate_id=candidate_id,
        view_digest=challenge["view_digest"],
        csrf_token="b01-csrf",
        origin="http://127.0.0.1:5173",
        expected_origin="http://127.0.0.1:5173",
        command_id="b01-test-only-accept",
        now=now,
    )
    accepted_root = tmp_path / "accepted-managed-worktree"
    workspace = repo.open_accepted_worktree(
        acceptance_id=accepted["acceptance_id"],
        target_dir=accepted_root,
        owner_ref="test-only:b01",
    )
    assert workspace["label"] == "Working Copy"
    accepted_hashes = _source_hashes(accepted_root)
    package_path = tmp_path / "accepted-b01.p0.zip"
    repo.export_p0(acceptance_id=accepted["acceptance_id"], package_path=package_path)
    verified = repo.verify_p0_package(package_path)
    assert verified["verified"] is True

    portable = tmp_path / "portable-b01.p0.zip"
    portable.write_bytes(package_path.read_bytes())
    monkeypatch.delenv("POLYNEXUS_P0_RECEIPT_PRIVATE_KEY", raising=False)
    offline_database = tmp_path / "offline-b01.db"
    _upgrade_d1b(offline_database)
    offline_engine = create_engine("sqlite:///" + offline_database.as_posix(), future=True)
    try:
        with Session(offline_engine) as offline_session:
            offline_repo = __import__(
                "polynexus_core.persistence.d1b", fromlist=["D1bRepository"]
            ).D1bRepository(offline_session, ContentStore(tmp_path / "offline-content"))
            offline_verified = offline_repo.verify_p0_package(portable)
            assert offline_verified["verified"] is True
            restored_root = tmp_path / "reconstructed-clean"
            restored = offline_repo.reconstruct_p0_package(
                package_path=portable,
                target_dir=restored_root,
            )
            assert restored["verified"] is True
            reconstructed_hashes = _source_hashes(restored_root)
    finally:
        offline_engine.dispose()

    assert reconstructed_hashes == accepted_hashes
    evidence = {
        "case": "B01-P0-RECONSTRUCT",
        "candidate_id": candidate_id,
        "acceptance_id": accepted["acceptance_id"],
        "principal": "TEST_ONLY:test-only:b01-human",
        "accepted_worktree": str(accepted_root),
        "package": str(portable),
        "offline_verification": offline_verified,
        "accepted_source_sha256": accepted_hashes,
        "reconstructed_source_sha256": reconstructed_hashes,
        "original_accepted_bytes_unchanged": reconstructed_hashes == accepted_hashes,
        "provider_private_session_required": False,
        "runner_exit": "recorded by pytest wrapper",
        "child_exit_evidence": [],
    }
    _emit("p0-reconstruct.json", evidence)
