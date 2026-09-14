from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from polynexus_core.api import dependencies
from polynexus_core.app import create_app
from polynexus_core.domain.d1b import capture_mapping
from polynexus_core.domain.generation import WorkGenerationRef
from polynexus_core.domain.enums import ArtifactType, EvidenceStatus, EvidenceType, RunState
from polynexus_core.domain.models import Artifact, ContextPackage, Evidence, Project, Run, Task
from polynexus_core.persistence.generation import GenerationRepository
from polynexus_core.persistence.repository import (
    SqlArtifactRepository,
    SqlContextPackageRepository,
    SqlEvidenceRepository,
    SqlProjectRepository,
    SqlRunRepository,
    SqlTaskRepository,
)
from polynexus_core.storage.content import ContentStore


def _upgrade(path: Path) -> None:
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
    config.set_main_option("sqlalchemy.url", "sqlite:///" + path.as_posix())
    command.upgrade(config, "head")


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _enrollment_proof(principal_ref: str, expires_at: datetime, issued_at: datetime) -> str:
    payload = {
        "expires_at": expires_at.isoformat(),
        "issued_at": issued_at.isoformat(),
        "nonce": "api-enrollment-nonce",
        "principal_ref": principal_ref,
    }
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).decode().rstrip("=")
    signed = f"pn-d11-a-lp-enrollment-v1.{encoded}"
    signature = hmac.new(b"test-enrollment-secret", signed.encode(), hashlib.sha256).hexdigest()
    return f"{signed}.{signature}"


def test_d1b_core_api_exact_view_and_explicit_a_lp_human(monkeypatch, tmp_path):
    database = tmp_path / "api.db"
    _upgrade(database)
    monkeypatch.setenv("POLYNEXUS_DATABASE_URL", "sqlite:///" + database.as_posix())
    monkeypatch.setenv("POLYNEXUS_CONTENT_ROOT", str(tmp_path / "content"))
    monkeypatch.setenv("POLYNEXUS_D1B_TEST_MODE", "1")
    monkeypatch.setenv("POLYNEXUS_ENVIRONMENT", "TEST")
    monkeypatch.setenv("POLYNEXUS_HUMAN_TEST_MODE", "1")
    monkeypatch.setenv("POLYNEXUS_UI_ORIGIN", "http://127.0.0.1:5173")
    monkeypatch.setenv("POLYNEXUS_HUMAN_A_LP_ENROLLMENT_SECRET", "test-enrollment-secret")
    monkeypatch.setattr(dependencies, "_LOOPBACK_TOKEN", "test-token")
    client_app = create_app()
    headers = {"X-Loopback-Token": "test-token"}
    requirements = capture_mapping({"requirements.txt": b"requirements-v1"})
    validation_bytes = json.dumps(
        {
            "assurance": {"mode": "VERIFIED"},
            "checks": [{"applicability": "APPLICABLE", "check_id": "api-test", "requiredness": "REQUIRED"}],
            "format": "pn.validation-contract.v1",
            "revision": 1,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    validation = capture_mapping({"validation.json": validation_bytes})
    artifact_digest, _ = ContentStore(tmp_path / "content").put(b"http-output")
    with TestClient(client_app, base_url="http://127.0.0.1", client=("127.0.0.1", 50000)) as client:
        body = {
            "baseline": {"entries": {"app.py": _b64(b"before\n")}},
            "result": {"entries": {"app.py": _b64(b"after\n"), "new.txt": _b64(b"X")}},
            "requirements_snapshot_id": requirements.manifest.snapshot_id,
            "validation_contract_snapshot_id": validation.manifest.snapshot_id,
            "requirements": {"entries": {"requirements.txt": _b64(b"requirements-v1")}},
            "validation_contract": {"entries": {"validation.json": _b64(validation_bytes)}},
            "lineage_ref": "api-test",
        }
        created = client.post("/api/v1/candidates", json=body, headers=headers)
        assert created.status_code == 201, created.text
        candidate_id = created.json()["candidate_id"]
        view = client.get(f"/api/v1/candidates/{candidate_id}/view", headers=headers)
        assert view.status_code == 200
        assert view.json()["candidate_id"] == candidate_id
        rejected = client.post("/api/v1/candidates", json={**body, "caller_changes": []}, headers=headers)
        assert rejected.status_code == 422
        verification = client.post(
            f"/api/v1/candidates/{candidate_id}/verifications",
            headers=headers,
            json={
                "contract_id": validation.manifest.snapshot_id,
                "observations": [{
                    "check_id": "api-test",
                    "evidence_type": "TOOL",
                    "actor_id": "runner",
                    "source": "pytest",
                    "requiredness": "REQUIRED",
                    "applicability": "APPLICABLE",
                    "outcome": "PASS",
                    "validity": "VALID",
                    "command": "pytest -q",
                    "cwd": "C:/repo",
                    "argv": ["pytest", "-q"],
                    "runner_exit": 0,
                    "child_exit": 0,
                    "raw_artifact_ref": "core-blob:" + artifact_digest,
                    "raw_artifact_sha256": artifact_digest,
                    "freshness": "CURRENT",
                    "provenance": {"runner": "pytest", "trusted_runner": "core-test:http"},
                }],
            },
        )
        assert verification.status_code == 201, verification.text
        # The Human protocol is not enabled by the fixture switch in this
        # branch: local-personal use must opt into the explicit A-LP flag.
        monkeypatch.delenv("POLYNEXUS_HUMAN_TEST_MODE", raising=False)
        monkeypatch.setenv("POLYNEXUS_HUMAN_A_LP_ENABLED", "1")
        monkeypatch.setenv("POLYNEXUS_ENVIRONMENT", "LOCAL")
        now = datetime.now(timezone.utc)
        pairing_expiry = now + timedelta(hours=1)
        pairing_proof = _enrollment_proof("human:api", pairing_expiry, issued_at=now)
        local_fixture = client.post(
            "/api/v1/human/pairings",
            headers={**headers, "Origin": "http://127.0.0.1:5173"},
            json={"principal_ref": "human:api", "enrollment_proof": pairing_proof, "expires_at": pairing_expiry.isoformat()},
        )
        assert local_fixture.status_code == 403
        assert local_fixture.json()["detail"] == "d1b_fixture_route_disabled"

        # The legacy HMAC path remains available only for the explicit TEST
        # fixture seam; it is never a LOCAL A-LP enrollment issuer.
        monkeypatch.setenv("POLYNEXUS_ENVIRONMENT", "TEST")
        monkeypatch.setenv("POLYNEXUS_HUMAN_TEST_MODE", "1")
        pairing = client.post(
            "/api/v1/human/pairings",
            headers=headers,
            json={"principal_ref": "human:api", "enrollment_proof": pairing_proof, "expires_at": pairing_expiry.isoformat()},
        )
        assert pairing.status_code == 201, pairing.text
        session = client.post(
            "/api/v1/human/sessions",
            headers=headers,
            json={"grant_id": pairing.json()["grant_id"], "pairing_proof": pairing_proof, "audience": "ui", "csrf_token": "csrf"},
        )
        assert session.status_code == 201, session.text
        challenge = client.post(
            "/api/v1/human/decision-challenges",
            headers=headers,
            json={"session_id": session.json()["session_id"], "candidate_id": candidate_id, "action": "Accept"},
        )
        assert challenge.status_code == 201, challenge.text
        decision_body = {
            "session_id": session.json()["session_id"],
            "challenge_id": challenge.json()["challenge_id"],
            "nonce": challenge.json()["nonce"],
            "action": "Accept",
            "candidate_id": candidate_id,
            "view_digest": challenge.json()["view_digest"],
            "csrf_token": "csrf",
            "origin": "http://127.0.0.1:5173",
            "command_id": "api-accept-1",
        }
        missing_origin = client.post(
            "/api/v1/human/decisions",
            headers=headers,
            json=decision_body,
        )
        assert missing_origin.status_code == 409 and missing_origin.json()["detail"] == "origin_rejected"
        decision = client.post(
            "/api/v1/human/decisions",
            headers={**headers, "Origin": "http://127.0.0.1:5173"},
            json=decision_body,
        )
        assert decision.status_code == 201, decision.text
        assert decision.json()["disposition"] == "ACCEPTED"
        session_revoke = client.post(
            f"/api/v1/human/sessions/{session.json()['session_id']}/revoke",
            headers=headers,
            json={"csrf_token": "csrf"},
        )
        assert session_revoke.status_code == 200, session_revoke.text
        assert session_revoke.json()["status"] == "REVOKED"


def test_d1b_production_generation_snapshot_producer(monkeypatch, tmp_path):
    database = tmp_path / "producer.db"
    _upgrade(database)
    content_root = tmp_path / "content"
    monkeypatch.setenv("POLYNEXUS_DATABASE_URL", "sqlite:///" + database.as_posix())
    monkeypatch.setenv("POLYNEXUS_CONTENT_ROOT", str(content_root))
    monkeypatch.setattr(dependencies, "_LOOPBACK_TOKEN", "producer-token")
    engine = create_engine("sqlite:///" + database.as_posix(), future=True)
    with Session(engine) as session:
        project = Project(name="producer-project")
        SqlProjectRepository(session).add(project)
        context = ContextPackage(project_id=project.id, version=1)
        SqlContextPackageRepository(session).add(context)
        task = Task(
            project_id=project.id,
            title="producer-task",
            workflow_id="review-minimal",
            workflow_version=1,
            context_package_id=context.id,
        )
        SqlTaskRepository(session).add(task)
        session.flush()
        generation_repo = GenerationRepository(session)
        validation_contract = json.dumps(
            {
                "assurance": {"mode": "STANDARD"},
                "checks": [{"applicability": "APPLICABLE", "check_id": "tests", "requiredness": "REQUIRED"}],
                "format": "pn.validation-contract.v1",
                "revision": 1,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        prepared = generation_repo.prepare(
            task_id=task.id,
            context_package_id=context.id,
            requirements="requirements",
            validation=validation_contract,
        )
        generation_repo.begin(
            principal="producer-test",
            command_id="producer-begin",
            task_id=task.id,
            expected_revision=0,
            inputs=prepared,
        )
        run = Run(
            task_id=task.id,
            workflow_id=task.workflow_id,
            workflow_version=task.workflow_version,
            context_package_id=context.id,
            generation_revision=1,
        )
        SqlRunRepository(session).add(run)
        session.flush()
        claim = generation_repo.claim(
            WorkGenerationRef(task.id, 1),
            run_id=run.id,
            lineage="run:" + run.id,
            expected_control=0,
        )
        session.execute(text("UPDATE runs SET state='COMPLETED' WHERE id=:run"), {"run": run.id})
        session.execute(
            text("UPDATE work_generations SET closed=1 WHERE task_id=:task AND revision=1"),
            {"task": task.id},
        )
        session.execute(
            text(
                "UPDATE generation_writer_claims SET released=1 "
                "WHERE task_id=:task AND revision=1 AND run_id=:run"
            ),
            {"task": task.id, "run": run.id},
        )
        session.commit()
        task_id, run_id, fence = task.id, run.id, claim["fence"]
    engine.dispose()

    headers = {"X-Loopback-Token": "producer-token"}
    with TestClient(create_app(), client=("127.0.0.1", 50120)) as client:
        snapshots = {}
        for kind in ("baseline", "result", "requirements", "validation"):
            response = client.post(
                f"/api/v1/tasks/{task_id}/generations/1/snapshots",
                headers=headers,
                json={"run_id": run_id, "kind": kind},
            )
            assert response.status_code == 201, response.text
            value = response.json()
            assert value["quiescent"] and value["source_ref"].endswith(f":{kind}")
            assert value["lineage_ref"] == "run:" + run_id
            snapshots[kind] = value["snapshot_id"]
        published = client.post(
            f"/api/v1/tasks/{task_id}/generations/1/candidates",
            headers=headers,
            json={
                "baseline_snapshot_id": snapshots["baseline"],
                "result_snapshot_id": snapshots["result"],
                "requirements_snapshot_id": snapshots["requirements"],
                "validation_contract_snapshot_id": snapshots["validation"],
                "run_id": run_id,
                "lineage_ref": "run:" + run_id,
            },
        )
        assert published.status_code == 201, published.text
        candidate_id = published.json()["candidate_id"]

    project_id = project.id
    normalized_result = {
        "format": "codex.exec.jsonl.v1",
        "event_count": 1,
        "terminal_type": "turn.completed",
        "d1b_checks": [
            {
                "check_id": "tests",
                "argv": ["pytest", "-q"],
                "cwd": "C:/managed/run",
                "runner_exit": 0,
                "child_exit": 0,
                "output": "production run output",
                "execution_id": "exec-production-run",
            }
        ],
    }
    normalized_json = json.dumps(normalized_result, sort_keys=True, separators=(",", ":"))
    normalized_digest = hashlib.sha256(normalized_json.encode("utf-8")).hexdigest()
    generic_bytes = (normalized_json + "\n").encode("utf-8")
    generic_digest, generic_size = ContentStore(content_root).put(generic_bytes)
    with Session(create_engine("sqlite:///" + database.as_posix(), future=True)) as session:
        generic_artifact = Artifact(
            project_id=project_id,
            task_id=task_id,
            run_id=run_id,
            artifact_type=ArtifactType.CODE_DIFF,
            mime_type="text/x-diff",
            source_type="codex.exec",
            storage_ref=f"core-blob:{generic_digest}",
            sha256=generic_digest,
            size=generic_size,
        )
        generic_evidence = Evidence(
            task_id=task_id,
            run_id=run_id,
            actor_id="runtime:codex.exec",
            source="runtime.codex.exec",
            type=EvidenceType.RUNTIME_EVIDENCE,
            status=EvidenceStatus.OBSERVED,
            artifact_refs=(generic_artifact.id,),
            metadata={
                "normalized_result_json": normalized_json,
                "normalized_result_sha256": normalized_digest,
                "exit_code": "0",
                "cwd": "C:/managed/run",
            },
        )
        SqlArtifactRepository(session).add(generic_artifact)
        SqlEvidenceRepository(session).add(generic_evidence)
        session.flush()
        session.execute(
            text(
                "UPDATE runs SET result_evidence_ids=:evidence,result_artifact_ids=:artifacts "
                "WHERE id=:run"
            ),
            {
                "evidence": json.dumps([generic_evidence.id]),
                "artifacts": json.dumps([generic_artifact.id]),
                "run": run_id,
            },
        )
        session.commit()

    monkeypatch.setenv("POLYNEXUS_TRUSTED_RUNNER_REF", "core-runner:production-test")
    monkeypatch.setenv("POLYNEXUS_TRUSTED_RUNNER_ATTESTATION", "production-attestation")
    with TestClient(create_app(), client=("127.0.0.1", 50121)) as client:
        verified = client.post(
            f"/api/v1/tasks/{task_id}/generations/1/candidates/{candidate_id}/verification",
            headers=headers,
            json={"run_id": run_id},
        )
        assert verified.status_code == 201, verified.text
        assert verified.json()["acceptance_eligible"] is True

        target_verification_id = verified.json()["verification_id"]
        with Session(engine) as session:
            target = session.execute(
                text(
                    "SELECT evidence_set_id FROM verification_records "
                    "WHERE verification_id=:verification"
                ),
                {"verification": target_verification_id},
            ).mappings().one()
            target_evidence = json.loads(
                session.execute(
                    text("SELECT canonical_json FROM evidence_sets WHERE evidence_set_id=:evidence"),
                    {"evidence": target["evidence_set_id"]},
                ).scalar_one()
            )
        reviewed_evidence_id = target_evidence["observations"][0]["evidence_id"]

        monkeypatch.setenv("POLYNEXUS_CROSS_REVIEWER_REF", "reviewer:production-test")
        reviewer_run_response = client.post(
            f"/api/v1/tasks/{task_id}/generations/1/candidates/{candidate_id}/cross-review-runs",
            headers=headers,
            json={"target_run_id": run_id},
        )
        assert reviewer_run_response.status_code == 201, reviewer_run_response.text
        reviewer_run_id = reviewer_run_response.json()["run_id"]

        with Session(engine) as session:
            reviewer_normalized_result = {
                "format": "codex.exec.jsonl.v1",
                "event_count": 1,
                "terminal_type": "turn.completed",
                "d1b_checks": [
                    {
                        "check_id": "tests",
                        "argv": ["reviewer", "--candidate", candidate_id],
                        "cwd": "C:/managed/reviewer",
                        "runner_exit": 0,
                        "child_exit": 0,
                        "output": "independent review passed",
                        "execution_id": "exec-production-cross-review",
                    }
                ],
            }
            reviewer_normalized_json = json.dumps(
                reviewer_normalized_result, sort_keys=True, separators=(",", ":")
            )
            reviewer_digest = hashlib.sha256(reviewer_normalized_json.encode("utf-8")).hexdigest()
            reviewer_bytes = (reviewer_normalized_json + "\n").encode("utf-8")
            reviewer_blob_digest, reviewer_blob_size = ContentStore(content_root).put(reviewer_bytes)
            reviewer_artifact = Artifact(
                project_id=project_id,
                task_id=task_id,
                run_id=reviewer_run_id,
                artifact_type=ArtifactType.TEST_RESULT,
                mime_type="application/json",
                source_type="codex.exec.cross-review",
                storage_ref=f"core-blob:{reviewer_blob_digest}",
                sha256=reviewer_blob_digest,
                size=reviewer_blob_size,
            )
            reviewer_evidence = Evidence(
                task_id=task_id,
                run_id=reviewer_run_id,
                actor_id="runtime:codex.exec",
                source="runtime.codex.exec",
                type=EvidenceType.RUNTIME_EVIDENCE,
                status=EvidenceStatus.OBSERVED,
                artifact_refs=(reviewer_artifact.id,),
                metadata={
                    "normalized_result_json": reviewer_normalized_json,
                    "normalized_result_sha256": reviewer_digest,
                    "exit_code": "0",
                    "cwd": "C:/managed/reviewer",
                },
            )
            SqlArtifactRepository(session).add(reviewer_artifact)
            SqlEvidenceRepository(session).add(reviewer_evidence)
            session.flush()
            reviewer_run = SqlRunRepository(session).get(reviewer_run_id)
            assert reviewer_run is not None
            reviewer_run.transition(RunState.STARTING)
            reviewer_run.transition(RunState.RUNNING)
            reviewer_run.transition(RunState.COMPLETED)
            SqlRunRepository(session).update(reviewer_run)
            session.execute(
                text(
                    "UPDATE runs SET result_evidence_ids=:evidence,result_artifact_ids=:artifacts "
                    "WHERE id=:run"
                ),
                {
                    "evidence": json.dumps([reviewer_evidence.id]),
                    "artifacts": json.dumps([reviewer_artifact.id]),
                    "run": reviewer_run_id,
                },
            )
            session.commit()

        cross_review = client.post(
            f"/api/v1/tasks/{task_id}/generations/1/candidates/{candidate_id}/cross-review-verification",
            headers=headers,
            json={"reviewer_run_id": reviewer_run_id},
        )
        assert cross_review.status_code == 201, cross_review.text
        assert cross_review.json()["acceptance_eligible"] is True
        assurance = client.post(
            f"/api/v1/candidates/{candidate_id}/assurance",
            headers=headers,
            json={
                "mode": "STANDARD",
                "profile_ref": snapshots["validation"],
                "profile_revision": 1,
            },
        )
        assert assurance.status_code == 201, assurance.text
        assert assurance.json()["status"] == "CROSS_REVIEWED"
