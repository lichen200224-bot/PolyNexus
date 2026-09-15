"""Exercise real Registry -> ExecutionService dispatch authorization -> ACP.

An isolated synthetic Run first records APPROVAL_REQUIRED/NEED_ACTION, then
receives exact TEST_ONLY authorization and retries the same production path.
No routing policy is overridden and the ACP process is the real OpenCode target.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "core" / "src"))

from polynexus_core.domain.models import ContextPackage, Project, Task  # noqa: E402
from polynexus_core.domain.generation import GenerationConflict, WorkGenerationRef  # noqa: E402
from polynexus_core.execution_service import ExecutionService  # noqa: E402
from polynexus_core.persistence.generation import GenerationRepository  # noqa: E402
from polynexus_core.persistence.repository import (  # noqa: E402
    SqlArtifactRepository, SqlContextPackageRepository, SqlEvidenceRepository, SqlProjectRepository,
    SqlRunRepository, SqlRuntimeBindingSnapshotRepository, SqlTaskRepository,
)
from polynexus_core.persistence.runtime_dispatch_authorization import RuntimeDispatchAuthorizationRepository  # noqa: E402
from polynexus_core.runtime.opencode_acp import OpenCodeACPRuntimeAdapter  # noqa: E402
from polynexus_core.storage.content import ContentStore  # noqa: E402


def captured(argv: list[str], cwd: Path) -> dict[str, object]:
    result = subprocess.run(argv, cwd=cwd, capture_output=True, check=False, timeout=30)
    return {"argv": argv, "cwd": str(cwd), "exit": result.returncode,
            "stdout": result.stdout.decode(errors="replace"), "stderr": result.stderr.decode(errors="replace")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    args = parser.parse_args()
    root = args.artifact_root.resolve(strict=False)
    if root.exists():
        raise RuntimeError("artifact root must be new")
    root.mkdir(parents=True)
    exe = args.executable.resolve(strict=True)
    content, sources, work = (root / name for name in ("core-content", "source-root", "work-root"))
    sources.mkdir()
    source = sources / "synthetic"
    source.mkdir()
    bug = source / "bug.py"
    bug.write_bytes(b"def answer():\n    return 41\n")
    (source / "test_bug.py").write_bytes(b"from bug import answer\n\ndef test_answer():\n    assert answer() == 42\n")
    initial = [captured(["git", "init", "-b", "main"], source),
               captured(["git", "add", "bug.py", "test_bug.py"], source),
               captured(["git", "-c", "user.name=d2b01-repair", "-c", "user.email=d2b01@example.invalid", "commit", "-m", "synthetic base"], source)]
    if any(item["exit"] != 0 for item in initial):
        raise RuntimeError("synthetic source Git init failed")
    baseline = captured(["git", "rev-parse", "HEAD"], source)["stdout"].strip()
    # ManagedInputs selects exact dirty bytes, including the task oracle.
    bug.write_bytes(b"def answer():\n    return 41\n# selected dirty input\n")
    with (source / "test_bug.py").open("ab") as stream:
        stream.write(b"\n# selected test input\n")
    before = hashlib.sha256(bug.read_bytes()).hexdigest()
    os.environ.update({
        "POLYNEXUS_CONTENT_ROOT": str(content), "POLYNEXUS_SOURCE_ROOT": str(sources),
        "POLYNEXUS_WORK_ROOT": str(work), "POLYNEXUS_OPENCODE_EXECUTABLE": str(exe),
        "POLYNEXUS_RUNTIME_PROFILE_REF": "opencode.acp.local",
        "POLYNEXUS_DISPATCH_TEST_ONLY": "1",
    })
    database = root / "core.db"
    config = Config()
    config.set_main_option("script_location", str(ROOT / "services" / "core" / "alembic"))
    config.set_main_option("sqlalchemy.url", "sqlite:///" + database.as_posix())
    command.upgrade(config, "head")
    engine = create_engine("sqlite:///" + database.as_posix())
    try:
        with Session(engine) as session:
            project = Project(name="D2B01 isolated synthetic", classification="PUBLIC")
            SqlProjectRepository(session).add(project)
            session.flush()
            context = ContextPackage(
                project_id=project.id, version=1, classification="PUBLIC",
                instructions=("Fix only bug.py so answer() returns 42.",),
            )
            SqlContextPackageRepository(session).add(context)
            session.flush()
            task = Task(
                project_id=project.id, title="Fix synthetic answer in bug.py",
                workflow_id="review-minimal", workflow_version=1,
                context_package_id=context.id, classification="PUBLIC",
            )
            SqlTaskRepository(session).add(task)
            session.commit()
            generations = GenerationRepository(session)
            prepared = generations.prepare(
                task_id=task.id, context_package_id=context.id,
                requirements="Change only bug.py from return 41 to return 42.",
                validation="test_bug.py must pass; preserve all other source files.",
                repository="synthetic", baseline=baseline,
                selected=("bug.py", "test_bug.py"), output_paths=("bug.py",),
            )
            session.commit()
            begun = generations.begin(
                principal="d2b01-repair", command_id="begin", task_id=task.id,
                expected_revision=0, inputs=prepared,
            )
            session.commit()
            service = ExecutionService(session)
            selected = service._registry._resolve_selected_profile()
            outcome = ""
            error = ""
            execution = None
            try:
                execution = asyncio.run(service.execute_task(task.id, generation_revision=1))
                outcome = execution.run.state.value
            except GenerationConflict as exc:
                outcome = "PREDISPATCH_POLICY_DENIED"
                error = str(exc)
            runs = list(SqlRunRepository(session).list_by_task(task.id))
            run = runs[0] if runs else None
            evidence = list(SqlEvidenceRepository(session).list_by_run(run.id)) if run else []
            binding = SqlRuntimeBindingSnapshotRepository(session).get_by_run(run.id) if run else None
            audit = [item for item in evidence if item.source == "runtime.routing_policy"]
            jobs = []
            launch_observations = []
            authorization = None
            retry_error = ""
            postcondition = None
            artifact_observations = []
            runtime_observations = []
            if outcome == "PREDISPATCH_POLICY_DENIED" and audit and audit[0].metadata.get("decision") == "APPROVAL_REQUIRED":
                # A separate DB connection checks binding and consumption
                # before the actual owned OpenCode process is created.
                original_factory = OpenCodeACPRuntimeAdapter._managed_job_factory
                def observed_factory(argv, cwd, environment):
                    with Session(engine) as independent:
                        independent_run = SqlRunRepository(independent).get(run.id)
                        independent_binding = SqlRuntimeBindingSnapshotRepository(independent).get_by_run(run.id)
                        independent_auth = RuntimeDispatchAuthorizationRepository(independent).get(authorization.authorization_id)
                        independent_evidence = SqlEvidenceRepository(independent).list_by_run(run.id)
                        launch_observations.append({
                            "run_state": independent_run.state.value,
                            "binding": {"run_id": independent_binding.run_id, "profile": independent_binding.runtime_profile_ref} if independent_binding else None,
                            "authorization_state": independent_auth.state.value if independent_auth else None,
                            "routing_policy_decisions": [e.metadata.get("decision") for e in independent_evidence if e.source == "runtime.routing_policy"],
                            "dispatch_evidence_count": sum(e.source == "runtime.dispatch_authorization" for e in independent_evidence),
                            "argv": argv, "cwd": str(cwd),
                        })
                    job = original_factory(argv, cwd, environment)
                    jobs.append(job)
                    return job
                OpenCodeACPRuntimeAdapter._managed_job_factory = staticmethod(observed_factory)
                try:
                    authorization = service._issue_test_only_runtime_dispatch_authorization(run.id)
                    assert not jobs, "ACP launch before authorization start"
                    execution = asyncio.run(service.execute_existing_run(run.id))
                    outcome = execution.run.state.value
                except Exception as exc:
                    retry_error = type(exc).__name__ + ":" + str(exc)
                    outcome = "RETRY_FAILED"
                finally:
                    OpenCodeACPRuntimeAdapter._managed_job_factory = staticmethod(original_factory)
                if jobs:
                    stdout, stderr = jobs[0].output()
                    (root / "production-acp.stdout.jsonl").write_bytes(stdout)
                    (root / "production-acp.stderr.log").write_bytes(stderr)
                    staging = Path(launch_observations[0]["cwd"])
                    postcondition = captured([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_bug.py"], staging)
                    (root / "production-postcondition.stdout.log").write_text(postcondition["stdout"], encoding="utf-8")
                    (root / "production-postcondition.stderr.log").write_text(postcondition["stderr"], encoding="utf-8")
                persisted_artifacts = SqlArtifactRepository(session).list_by_run(run.id)
                for item in persisted_artifacts:
                    blob = ContentStore(content).read_artifact(item)
                    artifact_observations.append({"id": item.id, "run_id": item.run_id, "storage_ref": item.storage_ref,
                                                  "sha256": item.sha256, "size": item.size,
                                                  "content_sha256": hashlib.sha256(blob).hexdigest()})
                runtime_observations = [{"id": e.id, "run_id": e.run_id, "source": e.source,
                                         "status": e.status.value, "metadata": e.metadata}
                                        for e in SqlEvidenceRepository(session).list_by_run(run.id)
                                        if e.source in {"runtime.opencode.acp", "runtime.dispatch_authorization", "runtime.routing_policy"}]
            stored_auth = RuntimeDispatchAuthorizationRepository(session).get(authorization.authorization_id) if authorization else None
            stored_run = SqlRunRepository(session).get(run.id) if run else None
            persisted_binding = SqlRuntimeBindingSnapshotRepository(session).get_by_run(run.id) if run else None
            process_facts = jobs[0].facts() if len(jobs) == 1 else []
            root_fact = process_facts[0] if len(process_facts) == 1 else None
            with Session(engine) as independent:
                all_evidence_sources = ([item.source for item in SqlEvidenceRepository(independent).list_by_run(run.id)]
                                        if run else [])
            record = {
                "selected_profile": selected.runtime_profile_ref,
                "project_id": project.id, "task_id": task.id, "context_id": context.id,
                "generation": begun, "run_id": run.id if run else None,
                "initial_outcome": "PREDISPATCH_POLICY_DENIED", "initial_error": error,
                "outcome": outcome, "retry_error": retry_error,
                "binding": {"run_id": persisted_binding.run_id, "profile": persisted_binding.runtime_profile_ref, "adapter_id": persisted_binding.adapter_id} if persisted_binding else None,
                "initial_binding": {"run_id": binding.run_id, "profile": binding.runtime_profile_ref} if binding else None,
                "authorization": {"id": stored_auth.authorization_id, "issuer_class": stored_auth.issuer_class.value,
                                  "policy_digest": stored_auth.policy_digest, "state": stored_auth.state.value,
                                  "issued_at": stored_auth.issued_at.isoformat(),
                                  "consumed_at": stored_auth.consumed_at.isoformat() if stored_auth.consumed_at else None} if stored_auth else None,
                "authorization_events": [{"event_kind": e.event_kind, "from_state": e.from_state,
                                          "to_state": e.to_state, "occurred_at": e.occurred_at.isoformat()}
                                         for e in RuntimeDispatchAuthorizationRepository(session).events(authorization.authorization_id)] if authorization else [],
                "launch_observations_before_effect": launch_observations,
                "real_acp_process_count": len(jobs),
                "real_process_facts": process_facts,
                "postcondition_test": postcondition,
                "persisted_artifacts": artifact_observations,
                "persisted_runtime_evidence": runtime_observations,
                "routing_policy_evidence": [{"id": item.id, "run_id": item.run_id, "status": item.status.value, "metadata": item.metadata} for item in audit],
                "all_evidence_sources": all_evidence_sources,
                "source_before_sha256": before,
                "original_source_unchanged": hashlib.sha256(bug.read_bytes()).hexdigest() == before,
                "baseline_commit": baseline,
                "run_state": stored_run.state.value if stored_run else None,
                "staging_after_sha256": hashlib.sha256((Path(launch_observations[0]["cwd"]) / "bug.py").read_bytes()).hexdigest() if jobs else None,
            }
            (root / "production-run.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print("PRODUCTION_PATH_OUTCOME=" + outcome)
            print("PRODUCTION_PATH_POLICY=" + (audit[0].metadata["decision"] if audit else "NONE"))
            print("PRODUCTION_PATH_BINDING=" + (persisted_binding.runtime_profile_ref if persisted_binding else "NONE"))
            print("PRODUCTION_PATH_AUTHORIZATION=" + (stored_auth.state.value if stored_auth else "NONE"))
            print("PRODUCTION_PATH_POSTCONDITION_EXIT=" + str(postcondition["exit"] if postcondition else "NOT_RUN"))
            observed = launch_observations[0] if len(launch_observations) == 1 else {}
            sources_observed = {item["source"] for item in runtime_observations}
            return 0 if (
                outcome == "COMPLETED"
                and selected.runtime_profile_ref == "opencode.acp.local"
                and binding is None and persisted_binding is not None
                and stored_auth and stored_auth.state.value == "CONSUMED"
                and sum(item["event_kind"] == "CONSUME" for item in RuntimeDispatchAuthorizationRepository(session).events(authorization.authorization_id)) == 1
                and observed.get("run_state") == "STARTING"
                and observed.get("binding", {}).get("run_id") == run.id
                and observed.get("authorization_state") == "CONSUMED"
                and observed.get("routing_policy_decisions") == ["APPROVAL_REQUIRED"]
                and observed.get("dispatch_evidence_count") == 1
                and len(jobs) == 1 and root_fact is not None
                and root_fact.get("exit_code") == 0
                and root_fact.get("argv", [None])[0] == str(exe)
                and all(fact.get("stopped") is True for fact in process_facts)
                and postcondition and postcondition["exit"] == 0
                and len(artifact_observations) == 1
                and artifact_observations[0]["sha256"] == artifact_observations[0]["content_sha256"]
                and {"runtime.opencode.acp", "runtime.dispatch_authorization", "runtime.routing_policy"} <= sources_observed
                and hashlib.sha256(bug.read_bytes()).hexdigest() == before
            ) else 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
