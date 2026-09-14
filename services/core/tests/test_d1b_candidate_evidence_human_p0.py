"""D1b W3-W6 acceptance-oriented regression tests."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import shutil
import sqlite3
import zipfile
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from polynexus_core.domain.d1b import (
    Applicability,
    AssuranceMode,
    Candidate,
    CanonicalizationError,
    EvidenceBindingError,
    EvidenceObservation,
    Requiredness,
    SnapshotCapture,
    SnapshotEntry,
    SnapshotManifest,
    VerificationOutcome,
    Validity,
    capture_mapping,
    capture_directory,
    derive_changeset,
    evaluate_verification,
)
from polynexus_core.persistence.d1b import (
    D1bPersistenceError,
    D1bRepository,
    HumanProtocolError,
    P0PackageError,
)
from polynexus_core.storage.content import ContentStore


def _upgrade(path: Path, revision: str = "head"):
    cfg = Config()
    cfg.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
    cfg.set_main_option("sqlalchemy.url", "sqlite:///" + path.as_posix())
    command.upgrade(cfg, revision)


@pytest.fixture()
def d1b_db(tmp_path, monkeypatch):
    monkeypatch.setenv("POLYNEXUS_D1B_TEST_MODE", "1")
    monkeypatch.setenv("POLYNEXUS_ENVIRONMENT", "TEST")
    monkeypatch.setenv("POLYNEXUS_HUMAN_A_LP_ENROLLMENT_SECRET", "test-enrollment-secret")
    monkeypatch.setenv("POLYNEXUS_P0_RECEIPT_PRIVATE_KEY", "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
    monkeypatch.setenv("POLYNEXUS_P0_RECEIPT_PUBLIC_KEY", "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
    monkeypatch.setenv("POLYNEXUS_P0_RECEIPT_KEY_ID", "test-ed25519-v1")
    database = tmp_path / "d1b.db"
    _upgrade(database)
    engine = create_engine("sqlite:///" + database.as_posix(), future=True)

    @event.listens_for(engine, "connect")
    def _foreign_keys(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    with Session(engine) as session:
        yield session, ContentStore(tmp_path / "content"), tmp_path
    engine.dispose()


def _sha(hex_value: str) -> str:
    return "sha256:" + hex_value


def _enrollment_proof(principal_ref: str, expires_at: datetime, issued_at: datetime | None = None) -> str:
    payload = {
        "expires_at": expires_at.isoformat(),
        "issued_at": (issued_at or datetime.now(timezone.utc)).isoformat(),
        "nonce": "test-enrollment-nonce",
        "principal_ref": principal_ref,
    }
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).decode().rstrip("=")
    signed = f"pn-d11-a-lp-enrollment-v1.{encoded}"
    signature = hmac.new(b"test-enrollment-secret", signed.encode(), hashlib.sha256).hexdigest()
    return f"{signed}.{signature}"


def test_0006_preserves_legacy_acceptance_and_fails_closed(tmp_path):
    """A 0005 acceptance remains readable but cannot enter the P0 path."""
    database = tmp_path / "legacy-d1b.db"
    _upgrade(database, "0005")
    baseline = capture_mapping({"app.py": b"before\n"})
    result = capture_mapping({"app.py": b"after\n"})
    requirements = capture_mapping({"requirements.txt": b"legacy\n"})
    validation = capture_mapping({"validation.json": _validation_contract_bytes("legacy-check")})
    changeset = derive_changeset(baseline.manifest, result.manifest)
    candidate = Candidate(
        changeset_id=changeset.changeset_id,
        requirements_snapshot_id=requirements.manifest.snapshot_id,
        validation_contract_snapshot_id=validation.manifest.snapshot_id,
    )
    created_at = "2026-01-01 00:00:00"
    closure = lambda capture: json.dumps(
        {blob: len(value) for blob, value in capture.blobs.items()},
        sort_keys=True,
        separators=(",", ":"),
    )
    with sqlite3.connect(database) as connection:
        for capture in (baseline, result, requirements, validation):
            connection.execute(
                "INSERT INTO content_snapshots(snapshot_id,canonical_json,source_closure_json,source_ref,created_at) VALUES(?,?,?,?,?)",
                (capture.manifest.snapshot_id, capture.manifest.canonical_bytes.decode(), closure(capture), None, created_at),
            )
        connection.execute(
            "INSERT INTO changesets(changeset_id,baseline_snapshot_id,result_snapshot_id,canonical_json,created_at) VALUES(?,?,?,?,?)",
            (changeset.changeset_id, baseline.manifest.snapshot_id, result.manifest.snapshot_id, changeset.canonical_bytes.decode(), created_at),
        )
        connection.execute(
            "INSERT INTO candidates(candidate_id,changeset_id,requirements_snapshot_id,validation_contract_snapshot_id,canonical_json,source_closure_json,frozen,created_at) VALUES(?,?,?,?,?,?,1,?)",
            (
                candidate.candidate_id,
                changeset.changeset_id,
                requirements.manifest.snapshot_id,
                validation.manifest.snapshot_id,
                candidate.canonical_bytes.decode(),
                json.dumps(
                    {
                        "baseline_snapshot_id": baseline.manifest.snapshot_id,
                        "result_snapshot_id": result.manifest.snapshot_id,
                        "requirements_snapshot_id": requirements.manifest.snapshot_id,
                        "validation_contract_snapshot_id": validation.manifest.snapshot_id,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                created_at,
            ),
        )
        connection.execute(
            "INSERT INTO human_pairing_grants(grant_id,principal_ref,proof_digest,status,expires_at,revoked_at,created_at) VALUES(?,?,?,?,?,?,?)",
            ("grant-legacy", "human:legacy", "0" * 64, "ACTIVE", "2027-01-01 00:00:00", None, created_at),
        )
        connection.execute(
            "INSERT INTO human_sessions(session_id,grant_id,principal_ref,audience,csrf_digest,status,expires_at,revoked_at,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            ("session-legacy", "grant-legacy", "human:legacy", "candidate-review", "1" * 64, "ACTIVE", "2027-01-01 00:00:00", None, created_at),
        )
        connection.execute(
            "INSERT INTO human_challenges(challenge_id,session_id,candidate_id,view_digest,action,nonce_digest,expires_at,consumed_at,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            ("challenge-legacy", "session-legacy", candidate.candidate_id, "view-legacy", "Accept", "2" * 64, "2027-01-01 00:00:00", None, created_at),
        )
        connection.execute(
            "INSERT INTO human_decision_events(decision_id,candidate_id,acceptance_id,action,principal_ref,session_id,challenge_id,command_id,view_digest,prior_acceptance_id,replacement_acceptance_id,reason,revision,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("decision-legacy", candidate.candidate_id, "accept-legacy", "Accept", "human:legacy", "session-legacy", "challenge-legacy", "legacy-command", "view-legacy", None, None, None, 1, created_at),
        )
        connection.execute(
            "INSERT INTO accepted_results(acceptance_id,candidate_id,accept_decision_id,publication_id,created_at) VALUES(?,?,?,?,?)",
            ("accept-legacy", candidate.candidate_id, "decision-legacy", None, created_at),
        )

    _upgrade(database, "head")
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT acceptance_id,verification_id,evidence_set_id,policy_revision,view_digest FROM accepted_results"
        ).fetchall() == [("accept-legacy", None, None, None, None)]
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    engine = create_engine("sqlite:///" + database.as_posix(), future=True)
    with Session(engine) as session:
        repo = D1bRepository(session, ContentStore(tmp_path / "content"))
        # Legacy decision rows are immutable and cannot be retrofitted with a
        # modern A-LP trust closure, so the P0 path rejects them before use.
        with pytest.raises(P0PackageError, match="accepted_decision_binding_mismatch"):
            repo._accepted_context("accept-legacy")
    engine.dispose()

    with sqlite3.connect(database) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="accepted result binding rejected"):
            connection.execute(
                "INSERT INTO accepted_results(acceptance_id,candidate_id,accept_decision_id,publication_id,created_at,verification_id,evidence_set_id,policy_revision,view_digest) VALUES(?,?,?,?,?,?,?,?,?)",
                ("accept-new-invalid", candidate.candidate_id, "decision-legacy", None, created_at, None, None, None, None),
            )


_TEST_ARTIFACT = b"pytest-output"
_TEST_ARTIFACT_SHA = hashlib.sha256(_TEST_ARTIFACT).hexdigest()


def _validation_contract_bytes(check_id: str = "tests") -> bytes:
    checks = [
        {"applicability": "APPLICABLE", "check_id": check_id, "requiredness": "REQUIRED"},
    ]
    if check_id == "tests":
        checks.append({"applicability": "APPLICABLE", "check_id": "optional", "requiredness": "OPTIONAL"})
    return json.dumps(
        {
            "assurance": {"mode": "VERIFIED"},
            "checks": checks,
            "format": "pn.validation-contract.v1",
            "revision": 1,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _observation(candidate_id: str, *, contract_id="contract.v1", check_id: str = "tests", requiredness=Requiredness.REQUIRED, outcome=VerificationOutcome.PASS, validity=Validity.VALID, source="pytest", evidence_type="TOOL", freshness="CURRENT", applicability=Applicability.APPLICABLE, raw=True):
    return EvidenceObservation(
        candidate_id=candidate_id,
        contract_id=contract_id,
        check_id=check_id,
        evidence_type=evidence_type,
        actor_id="runner",
        source=source,
        requiredness=requiredness,
        applicability=applicability,
        outcome=outcome,
        validity=validity,
        command="pytest -q" if raw else None,
        cwd="C:/repo" if raw else None,
        argv=("pytest", "-q") if raw else (),
        runner_exit=0 if raw else None,
        child_exit=0 if raw else None,
        raw_artifact_ref="core-blob:" + _TEST_ARTIFACT_SHA if raw else None,
        raw_artifact_sha256=_TEST_ARTIFACT_SHA if raw else None,
        freshness=freshness,
        provenance={"runner": "pytest", "trusted_runner": "core-test:pytest"} if raw else {},
        reason="proved predicate" if applicability is Applicability.NOT_APPLICABLE else None,
    )


def _candidate(repo: D1bRepository, *, result: dict[str, bytes] | None = None, requirements=b"requirements-v1", validation=b"validation-v1", generation_revision=1, lineage="lineage-1"):
    baseline = capture_mapping({"app.py": b"before\n"})
    after = result or {"app.py": b"after\n", "new.txt": b"new"}
    result_capture = capture_mapping(after)
    req = capture_mapping({"requirements.txt": requirements})
    if validation == b"validation-v1":
        validation = _validation_contract_bytes()
    val = capture_mapping({"validation.json": validation})
    repo.save_snapshot(req)
    repo.save_snapshot(val)
    repo.content_store.put(_TEST_ARTIFACT)
    return repo.publish_candidate(
        baseline=baseline,
        result=result_capture,
        requirements_snapshot_id=req.manifest.snapshot_id,
        validation_contract_snapshot_id=val.manifest.snapshot_id,
        # The raw fixture route has no Task/Run/Generation graph.  Scoped
        # publications are covered by the production snapshot-ID API.
        generation_revision=None,
        lineage_ref=lineage,
        provenance={"source": "test"},
    )


def _add_scoped_publication(repo: D1bRepository, published: dict[str, str], suffix: str = "p0") -> dict[str, str]:
    """Attach a real D1a Task/Generation/Run publication to a fixture candidate."""
    session = repo.session
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    project_id = f"project-d1b-{suffix}"
    context_id = f"context-d1b-{suffix}"
    task_id = f"task-d1b-{suffix}"
    run_id = f"run-d1b-{suffix}"
    inputs = {
        "context_package_id": context_id,
        "requirements_ref": repo._load_snapshot(published["requirements_snapshot_id"]).manifest.entries[0].blob,
        "validation_ref": repo._load_snapshot(published["validation_contract_snapshot_id"]).manifest.entries[0].blob,
        "baseline_ref": published["baseline_snapshot_id"],
        "input_ref": published["result_snapshot_id"],
    }
    session.execute(
        text("INSERT INTO projects(id,name,created_at) VALUES(:id,:name,:at)"),
        {"id": project_id, "name": "d1b", "at": now},
    )
    session.execute(
        text("INSERT INTO context_packages(id,project_id,version,instructions,constraints,project_facts,artifact_refs,prior_decision_refs,memory_refs,source_refs,created_at) VALUES(:id,:project,1,'[]','[]','{}','[]','[]','[]','[]',:at)"),
        {"id": context_id, "project": project_id, "at": now},
    )
    session.execute(
        text("INSERT INTO tasks(id,project_id,title,workflow_id,workflow_version,mode,created_at) VALUES(:id,:project,'d1b','wf',1,'LOCAL',:at)"),
        {"id": task_id, "project": project_id, "at": now},
    )
    session.execute(text("INSERT INTO generation_counters(task_id,revision) VALUES(:task,1)"), {"task": task_id})
    session.execute(
        text("INSERT INTO work_generations(task_id,revision,inputs,predecessor,control_revision,aborted,closed,ownership_unknown) VALUES(:task,1,:inputs,NULL,0,0,0,0)"),
        {"task": task_id, "inputs": json.dumps(inputs)},
    )
    session.execute(
        text("INSERT INTO runs(id,task_id,workflow_id,workflow_version,context_package_id,execution_target,resume_mode,state,created_at,updated_at,generation_revision) VALUES(:id,:task,'wf',1,:context,'LOCAL','FRESH','COMPLETED',:at,:at,1)"),
        {"id": run_id, "task": task_id, "context": context_id, "at": now},
    )
    session.execute(
        text("INSERT INTO generation_writer_claims(task_id,revision,lineage,run_id,fence,released) VALUES(:task,1,:lineage,:run,1,1)"),
        {"task": task_id, "lineage": f"run:{run_id}", "run": run_id},
    )
    for snapshot_id, kind in (
        (published["requirements_snapshot_id"], "requirements"),
        (published["validation_contract_snapshot_id"], "validation"),
        (published["baseline_snapshot_id"], "baseline"),
        (published["result_snapshot_id"], "result"),
    ):
        observed = repo._capture_from_snapshot_id(snapshot_id)
        repo.save_snapshot(
            SnapshotCapture(
                observed.manifest,
                observed.blobs,
                source_ref=f"core:generation:{task_id}:1:{run_id}:{kind}",
            )
        )
    return repo.publish_candidate_from_snapshot_ids(
        task_id=task_id,
        generation_revision=1,
        run_id=run_id,
        baseline_snapshot_id=published["baseline_snapshot_id"],
        result_snapshot_id=published["result_snapshot_id"],
        requirements_snapshot_id=published["requirements_snapshot_id"],
        validation_contract_snapshot_id=published["validation_contract_snapshot_id"],
        lineage_ref=f"run:{run_id}",
        provenance={"source": "scoped-test"},
    )


def test_d1b_golden_snapshot_and_changeset_vectors():
    empty = capture_mapping({}).manifest
    assert empty.snapshot_id == _sha("a60c142d586dfa7a88c8ef64f8e42d6ec6583a4b109f3c7d87759d14b35fac4a")
    vectors = {
        "G01": ({}, {"utf8.txt": bytes.fromhex("CF80E6BCA2")}, "daacb451f628d6042d7fa28d5bf0eac0378258d931655908bf1c29b0a7f26bb7", "06561333b5dacc322925230ef07e10b518a75c0fd97d3cb4476b5df6a2383aef"),
        "G02": ({}, {"src/測試.txt": bytes.fromhex("58")}, "e8bda7c54291b10053ddf97779c64c8246b9930d3d69dbe120ce5d4ec75bab6c", "36cf74bede7c7d2941e56b2004bdbffb84f060636988557eaa1705c183115432"),
        "G03": ({"line.txt": bytes.fromhex("610A")}, {"line.txt": bytes.fromhex("610D0A")}, "349ad0e65158b95b75de7435b636352c6fa29bf708a95b45fc1097cdd973ec4a", "df87519025d3dd2a1241c08ebe7898fcffc6133d427cf5def6ea3b59d5ffe3fc"),
        "G04": ({}, {"empty.txt": b""}, "3d9ed22d17634ee059e37e8123b5b403cad28e93e9f05ca0571e0b3a94816a17", "36aff5bf1fe84a43eb025186a8d25290414a04947678359b148bd1876796cea2"),
        "G05": ({}, {"binary.dat": bytes.fromhex("0001FF807F")}, "e59d1f91e2545e8e4c2426f645482ba73e005bb5ffeac95a89461c6a3684dce8", "09c603c1dab682b26a3e547f3e0b9a4fa7a4d2c713dab04ba8eb04134d23f1b5"),
        "G06": ({"tool.sh": (bytes.fromhex("58"), "100644")}, {"tool.sh": (bytes.fromhex("58"), "100755")}, "eb1c495968f90f5ad4cf64ca2049827e3510ad2f1196f49fea97d8a4fe6b5bd5", "2467013ef1d12deadba61e001ea8d8749e3f40a38ad5caafe0902b9bc84add67"),
        "G07": ({}, {"new.txt": bytes.fromhex("58")}, "55954e17be8d0e58268fd39e7ab1f7b7d398f4d9b6de1df8f505d760586be258", "81ed3bcaefe7cf8346de2b8e8a39f1305d1af0d3bb92a93a59c8a84b8045aac0"),
        "G08": ({"new.txt": bytes.fromhex("58")}, {}, "a60c142d586dfa7a88c8ef64f8e42d6ec6583a4b109f3c7d87759d14b35fac4a", "70b3d4243b4864d3cee2f9fa5019f68dfec2405c4a9d92a058c056d6a43048e9"),
        "G10": ({}, {"a.txt": bytes.fromhex("58"), "z.txt": b"", "測試.txt": bytes.fromhex("0001FF807F")}, "4b2dcf60883789647178f8644393b687d1e71241b2389db31fb9c59d375ea954", "92a5962a3465a645f862148e117c17dca6903b95031790a70086c685784424d3"),
        "G11a": ({}, {"é.txt": bytes.fromhex("58")}, "914a99330c7e03c227c74c2ac10f4add4fd52745d0b13eb4844cf1f1465d1b1c", "8d69a923361999a502e888ac12b44ccc2c828a16cd55f916a6a16d2e7f7311af"),
        "G11b": ({}, {"é.txt": bytes.fromhex("58")}, "70a6273c968c6b19fd900b8edb3a2eff8c3643504a76cd80a6ba71d2f6b61ad9", "9129354566f0e9b6dd8b8a48a8df4d10016bbf36391287fb10c6a8eb689021c4"),
        "G12a": ({}, {"large.bin": b"A" * 1_048_575}, "6ff8c0295bf9578e49839e9bf89ed46830e1cb22939c6b9003a21640770f814a", "a45dfbc176638e7befb0528cebb4cec581592c1041bd42838174ed009848d09d"),
        "G12b": ({}, {"large.bin": b"A" * 1_048_576}, "ff15704f1fbc4cd0f75b3be1dc36b221c1128b8367f05e3485e01dd65021ee8f", "d2f37e898070b29492cd71d5e1473efcf5b2dd7ee2a4ce23f177139151b0a3b3"),
    }
    for _name, (before_values, after_values, result_digest, changeset_digest) in vectors.items():
        baseline = capture_mapping(before_values).manifest
        result = capture_mapping(after_values).manifest
        changeset = derive_changeset(baseline, result)
        assert result.snapshot_id == _sha(result_digest)
        assert changeset.changeset_id == _sha(changeset_digest)
    with pytest.raises(CanonicalizationError, match="size_limit"):
        capture_mapping({"large.bin": b"A" * 1_048_577})


def test_d1b_golden_order_collision_and_size_boundaries():
    ordered = capture_mapping({"測試.txt": bytes.fromhex("0001FF807F"), "z.txt": b"", "a.txt": bytes.fromhex("58")}).manifest
    assert [entry.path for entry in ordered.entries] == ["a.txt", "z.txt", "測試.txt"]
    assert ordered.snapshot_id == _sha("4b2dcf60883789647178f8644393b687d1e71241b2389db31fb9c59d375ea954")
    with pytest.raises(CanonicalizationError, match="case_collision"):
        capture_mapping({"a.txt": b"x", "A.txt": b"x"})
    with pytest.raises(CanonicalizationError, match="size_limit"):
        capture_mapping({"large.bin": b"A" * 1_048_577})
    assert capture_mapping({"large.bin": b"A" * 1_048_575}).manifest.entries[0].size == 1_048_575
    assert capture_mapping({"large.bin": b"A" * 1_048_576}).manifest.entries[0].size == 1_048_576
    with pytest.raises(CanonicalizationError):
        capture_mapping({"../escape": b"x"})
    with pytest.raises(CanonicalizationError):
        capture_mapping({"a\\b": b"x"})


def test_d1b_directory_capture_rejects_new_entry_during_fence(tmp_path, monkeypatch):
    root = tmp_path / "source"
    root.mkdir()
    (root / "before.txt").write_bytes(b"before")
    import polynexus_core.domain.d1b as d1b_domain

    original = d1b_domain._directory_state
    calls = {"count": 0}

    def fenced_state(path):
        state = original(path)
        calls["count"] += 1
        if calls["count"] == 1:
            (path / "during.txt").write_bytes(b"during")
        return state

    monkeypatch.setattr(d1b_domain, "_directory_state", fenced_state)
    with pytest.raises(ValueError, match="source_changed_during_capture"):
        capture_directory(root)


def test_d1b_directory_capture_identity_includes_file_mode(tmp_path, monkeypatch):
    root = tmp_path / "source"
    root.mkdir()
    (root / "executable.sh").write_bytes(b"#!/bin/sh\n")
    import polynexus_core.domain.d1b as d1b_domain

    monkeypatch.setattr(
        d1b_domain,
        "_directory_state",
        lambda _path: {"executable.sh": (10, 1, 1, 0o755)},
    )
    capture = capture_directory(root)
    assert capture.manifest.entries[0].mode == "100755"


def test_d1b_directory_capture_excludes_managed_git_metadata(tmp_path):
    root = tmp_path / "managed-worktree"
    (root / ".git").mkdir(parents=True)
    (root / ".git" / "gitdir").write_text("C:/source-repository/.git/worktrees/managed", encoding="utf-8")
    (root / "src").mkdir()
    (root / "src" / "main.py").write_bytes(b"print('ok')\n")

    capture = capture_directory(root)

    assert [entry.path for entry in capture.manifest.entries] == ["src/main.py"]


def test_d1b_applicability_is_exact_and_unknown_blocks_required_gate():
    candidate_id = _sha("1" * 64)
    expected = (
        {"check_id": "gate", "requiredness": "REQUIRED", "applicability": "UNKNOWN", "applicability_predicate": None},
    )
    applicable = _observation(candidate_id, contract_id="contract.v1", check_id="gate")
    with pytest.raises(EvidenceBindingError, match="applicability_mismatch"):
        evaluate_verification(candidate_id, "contract.v1", [applicable], expected_checks=expected)
    unknown = _observation(
        candidate_id,
        contract_id="contract.v1",
        check_id="gate",
        applicability=Applicability.UNKNOWN,
    )
    blocked = evaluate_verification(candidate_id, "contract.v1", [unknown], expected_checks=expected)
    assert not blocked.acceptance_eligible
    assert "applicability_unknown" in blocked.failures[0]


def test_d1b_publication_derives_candidate_and_rejects_caller_diff(d1b_db):
    session, store, _tmp = d1b_db
    repo = D1bRepository(session, store)
    first = _candidate(repo, generation_revision=1, lineage="generation-1")
    session.commit()
    second = _candidate(repo, generation_revision=2, lineage="generation-2")
    assert second["candidate_id"] == first["candidate_id"]
    assert second["publication_id"] != first["publication_id"]
    changed_requirements = _candidate(repo, requirements=b"requirements-v2", generation_revision=3, lineage="generation-3")
    assert changed_requirements["candidate_id"] != first["candidate_id"]
    with pytest.raises(CanonicalizationError, match="caller_change_manifest_rejected"):
        _candidate(repo, generation_revision=4, lineage="generation-4") if False else repo.publish_candidate(
            baseline=capture_mapping({"app.py": b"before\n"}),
            result=capture_mapping({"app.py": b"after\n"}),
            requirements_snapshot_id=first["baseline_snapshot_id"],
            validation_contract_snapshot_id=first["result_snapshot_id"],
            caller_changes=[{"path": "forged.py", "op": "add"}],
        )


def test_d1b_scoped_publication_requires_d1a_generation_closure(d1b_db):
    session, store, _tmp = d1b_db
    repo = D1bRepository(session, store)
    baseline = capture_mapping({"app.py": b"before\n"})
    result = capture_mapping({"app.py": b"after\n"})
    requirements = capture_mapping({"requirements.txt": b"requirements-v1"})
    validation = capture_mapping({"validation.json": _validation_contract_bytes()})
    for capture in (baseline, result, requirements, validation):
        repo.save_snapshot(capture)
    task_id = "task-d1b-scope"
    run_id = "run-d1b-scope"
    project_id = "project-d1b-scope"
    context_id = "context-d1b-scope"
    inputs = {
        "context_package_id": context_id,
        "requirements_ref": requirements.manifest.entries[0].blob,
        "validation_ref": validation.manifest.entries[0].blob,
        "baseline_ref": baseline.manifest.snapshot_id,
        "input_ref": result.manifest.snapshot_id,
    }
    session.execute(text("INSERT INTO projects(id,name,created_at) VALUES(:id,:name,:at)"), {"id": project_id, "name": "scope", "at": datetime.now(timezone.utc).replace(tzinfo=None)})
    session.execute(text("INSERT INTO context_packages(id,project_id,version,instructions,constraints,project_facts,artifact_refs,prior_decision_refs,memory_refs,source_refs,created_at) VALUES(:id,:project,:v,'[]','[]','{}','[]','[]','[]','[]',:at)"), {"id": context_id, "project": project_id, "v": 1, "at": datetime.now(timezone.utc).replace(tzinfo=None)})
    session.execute(text("INSERT INTO tasks(id,project_id,title,workflow_id,workflow_version,mode,created_at) VALUES(:id,:project,'scope','wf',1,'LOCAL',:at)"), {"id": task_id, "project": project_id, "at": datetime.now(timezone.utc).replace(tzinfo=None)})
    session.execute(text("INSERT INTO generation_counters(task_id,revision) VALUES(:task,1)"), {"task": task_id})
    session.execute(text("INSERT INTO work_generations(task_id,revision,inputs,predecessor,control_revision,aborted,closed,ownership_unknown) VALUES(:task,1,:inputs,NULL,0,0,0,0)"), {"task": task_id, "inputs": json.dumps(inputs)})
    session.execute(text("INSERT INTO runs(id,task_id,workflow_id,workflow_version,context_package_id,execution_target,resume_mode,state,created_at,updated_at,generation_revision) VALUES(:id,:task,'wf',1,:context,'LOCAL','FRESH','COMPLETED',:at,:at,1)"), {"id": run_id, "task": task_id, "context": context_id, "at": datetime.now(timezone.utc).replace(tzinfo=None)})
    session.execute(text("INSERT INTO generation_writer_claims(task_id,revision,lineage,run_id,fence,released) VALUES(:task,1,'run:run-d1b-scope',:run,1,0)"), {"task": task_id, "run": run_id})
    for snapshot_id, kind in (
        (requirements.manifest.snapshot_id, "requirements"),
        (validation.manifest.snapshot_id, "validation"),
        (baseline.manifest.snapshot_id, "baseline"),
        (result.manifest.snapshot_id, "result"),
    ):
        observed = repo._capture_from_snapshot_id(snapshot_id)
        repo.save_snapshot(
            SnapshotCapture(
                observed.manifest,
                observed.blobs,
                source_ref=f"core:generation:{task_id}:1:{run_id}:{kind}",
            )
        )
    with pytest.raises(D1bPersistenceError, match="writer_not_quiescent"):
        repo.publish_candidate_from_snapshot_ids(
            task_id=task_id,
            generation_revision=1,
            run_id=run_id,
            baseline_snapshot_id=baseline.manifest.snapshot_id,
            result_snapshot_id=result.manifest.snapshot_id,
            requirements_snapshot_id=requirements.manifest.snapshot_id,
            validation_contract_snapshot_id=validation.manifest.snapshot_id,
            lineage_ref="run:run-d1b-scope",
        )
    session.execute(
        text("UPDATE generation_writer_claims SET released=1 WHERE task_id=:task AND revision=1 AND run_id=:run"),
        {"task": task_id, "run": run_id},
    )
    published = repo.publish_candidate_from_snapshot_ids(
        task_id=task_id,
        generation_revision=1,
        run_id=run_id,
        baseline_snapshot_id=baseline.manifest.snapshot_id,
        result_snapshot_id=result.manifest.snapshot_id,
        requirements_snapshot_id=requirements.manifest.snapshot_id,
        validation_contract_snapshot_id=validation.manifest.snapshot_id,
        lineage_ref="run:run-d1b-scope",
    )
    assert published["publication_id"].startswith("publication_")
    context = repo._candidate_context(published["candidate_id"])
    with pytest.raises(D1bPersistenceError, match="publication_snapshot_scope_mismatch"):
        repo._validate_publication_scope(
            candidate=context.candidate,
            baseline_snapshot_id=baseline.manifest.snapshot_id,
            result_snapshot_id=baseline.manifest.snapshot_id,
            task_id=task_id,
            generation_revision=1,
            run_id=run_id,
            lineage_ref="run:run-d1b-scope",
        )
    with pytest.raises(D1bPersistenceError, match="publication_scope_mismatch"):
        repo.publish_candidate_from_snapshot_ids(
            task_id=task_id,
            generation_revision=1,
            run_id="run-missing",
            baseline_snapshot_id=baseline.manifest.snapshot_id,
            result_snapshot_id=result.manifest.snapshot_id,
            requirements_snapshot_id=requirements.manifest.snapshot_id,
            validation_contract_snapshot_id=validation.manifest.snapshot_id,
            lineage_ref="run:run-d1b-scope",
        )


def test_d1b_snapshot_observation_receipts_survive_content_deduplication(d1b_db):
    session, store, _tmp = d1b_db
    repo = D1bRepository(session, store)
    capture = capture_mapping({"same.txt": b"same bytes"})

    snapshot_id = repo.save_snapshot(
        SnapshotCapture(
            capture.manifest,
            capture.blobs,
            source_ref="core:generation:task-a:1:run-a:baseline",
        )
    )
    assert repo.save_snapshot(
        SnapshotCapture(
            capture.manifest,
            capture.blobs,
            source_ref="core:generation:task-b:1:run-b:result",
        )
    ) == snapshot_id
    assert repo._snapshot_observed(snapshot_id, "core:generation:task-a:1:run-a:baseline")
    assert repo._snapshot_observed(snapshot_id, "core:generation:task-b:1:run-b:result")
    assert session.execute(
        text("SELECT COUNT(*) FROM content_snapshot_observations WHERE snapshot_id=:id"),
        {"id": snapshot_id},
    ).scalar_one() == 2


def test_d1b_evidence_axes_and_assurance_are_fail_closed(d1b_db):
    session, store, _tmp = d1b_db
    repo = D1bRepository(session, store)
    published = _candidate(repo)
    candidate_id = published["candidate_id"]
    contract_id = published["validation_contract_snapshot_id"]
    passing = _observation(candidate_id, contract_id=contract_id)
    optional_skip = _observation(candidate_id, contract_id=contract_id, check_id="optional", requiredness=Requiredness.OPTIONAL, outcome=VerificationOutcome.SKIPPED)
    result = repo.verify_candidate(candidate_id=candidate_id, contract_id=contract_id, observations=[passing, optional_skip], trusted_runner="core-test:pytest")
    assert result.acceptance_eligible
    first_evidence_id = repo.record_evidence(
        candidate_id=candidate_id,
        contract_id=contract_id,
        observations=[passing],
        trusted_runner="core-test:pytest",
    )
    changed_observation = replace(passing, outcome=VerificationOutcome.FAIL)
    changed_evidence_id = repo.record_evidence(
        candidate_id=candidate_id,
        contract_id=contract_id,
        observations=[changed_observation],
        trusted_runner="core-test:pytest",
    )
    assert changed_evidence_id != first_evidence_id
    assurance = repo.append_assurance(candidate_id=candidate_id, mode=AssuranceMode.VERIFIED, profile_ref=contract_id, profile_revision=1)
    assert assurance["status"] == "VERIFIED"
    with pytest.raises(D1bPersistenceError, match="assurance_target_mismatch"):
        repo.append_assurance(
            candidate_id=candidate_id,
            mode=AssuranceMode.VERIFIED,
            target_type="TASK",
            target_id="task-not-the-candidate",
        )
    required_skip = _observation(candidate_id, check_id="skip", outcome=VerificationOutcome.SKIPPED)
    blocked = evaluate_verification(candidate_id, "contract.v1", [required_skip])
    assert not blocked.acceptance_eligible and "required_skipped" in blocked.failures[0]
    optional_fail = evaluate_verification(candidate_id, "contract.v1", [_observation(candidate_id, contract_id="contract.v1", raw=False), _observation(candidate_id, contract_id="contract.v1", check_id="optional-fail", requiredness=Requiredness.OPTIONAL, outcome=VerificationOutcome.FAIL, raw=False)])
    assert optional_fail.acceptance_eligible
    with pytest.raises(EvidenceBindingError, match="cross_candidate"):
        repo.verify_candidate(candidate_id=candidate_id, contract_id=contract_id, observations=[_observation(_sha("0" * 64), contract_id=contract_id)], trusted_runner="core-test:pytest")
    ai = evaluate_verification(candidate_id, "contract.v1", [_observation(candidate_id, source="AI_OPINION", evidence_type="OPINION_ONLY", raw=False)])
    assert not ai.acceptance_eligible
    session.commit()


def test_d1b_generation_run_does_not_promote_generic_runtime_evidence(d1b_db, monkeypatch):
    session, store, _tmp = d1b_db
    repo = D1bRepository(session, store)
    published = _add_scoped_publication(repo, _candidate(repo), suffix="generic")
    task_id = "task-d1b-generic"
    run_id = "run-d1b-generic"
    artifact = b"generic-runtime-output"
    artifact_digest = hashlib.sha256(artifact).hexdigest()
    store.put(artifact)
    project_id = session.execute(
        text("SELECT project_id FROM tasks WHERE id=:task"), {"task": task_id}
    ).scalar_one()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session.execute(
        text(
            "INSERT INTO artifacts(id,project_id,artifact_type,mime_type,source_type,storage_ref,"
            "sha256,size,task_id,run_id) VALUES('artifact-generic',:project,'TEXT','text/plain',"
            "'CORE_RUN','core-blob:'||:sha,:sha,:size,:task,:run)"
        ),
        {
            "project": project_id,
            "sha": artifact_digest,
            "size": len(artifact),
            "task": task_id,
            "run": run_id,
        },
    )
    session.execute(
        text(
            "INSERT INTO evidence(id,task_id,run_id,actor_id,source,type,status,artifact_refs,"
            "metadata_json,observed_at) VALUES('evidence-generic',:task,:run,'core-runner',"
            "'runtime','RUNTIME_EVIDENCE','PASS',:refs,:metadata,:at)"
        ),
        {
            "task": task_id,
            "run": run_id,
            "refs": json.dumps(["artifact-generic"]),
            "metadata": json.dumps(
                {
                    "argv_json": json.dumps(["pytest", "-q"]),
                    "cwd": "C:/managed/run",
                    "exit_code": 0,
                    "child_exit": 0,
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            "at": now,
        },
    )
    session.execute(
        text("UPDATE runs SET result_evidence_ids=:evidence,result_artifact_ids=:artifacts WHERE id=:run"),
        {
            "evidence": json.dumps(["evidence-generic"]),
            "artifacts": json.dumps(["artifact-generic"]),
            "run": run_id,
        },
    )
    session.commit()
    monkeypatch.setenv("POLYNEXUS_TRUSTED_RUNNER_REF", "core-runner:generic-test")
    monkeypatch.setenv("POLYNEXUS_TRUSTED_RUNNER_ATTESTATION", "generic-attestation")
    with pytest.raises(D1bPersistenceError, match="d1b_runtime_evidence_missing"):
        repo.verify_candidate_from_run(
            candidate_id=published["candidate_id"],
            task_id=task_id,
            generation_revision=1,
            run_id=run_id,
        )


def test_d1b_human_exact_view_replay_and_append_only_history(d1b_db):
    session, store, tmp = d1b_db
    repo = D1bRepository(session, store)
    published = _candidate(repo)
    candidate_id = published["candidate_id"]
    contract_id = published["validation_contract_snapshot_id"]
    old_observation = _observation(candidate_id, contract_id=contract_id)
    verification = repo.verify_candidate(candidate_id=candidate_id, contract_id=contract_id, observations=[old_observation], trusted_runner="core-test:pytest")
    assert verification.acceptance_eligible
    session.commit()
    now = datetime.now(timezone.utc)
    pairing_expiry = now + timedelta(hours=1)
    with pytest.raises(HumanProtocolError, match="enrollment_assertion"):
        repo.create_pairing(principal_ref="human:alice", enrollment_proof="pairing-secret", expires_at=pairing_expiry)
    pairing_proof = _enrollment_proof("human:alice", pairing_expiry, issued_at=now)
    pairing = repo.create_pairing(principal_ref="human:alice", enrollment_proof=pairing_proof, expires_at=pairing_expiry)
    signed_expiry = now + timedelta(minutes=20)
    bounded_proof = _enrollment_proof("human:bounded", signed_expiry, issued_at=now)
    bounded = repo.create_pairing(
        principal_ref="human:bounded",
        enrollment_proof=bounded_proof,
        expires_at=now + timedelta(hours=1),
    )
    assert datetime.fromisoformat(bounded["expires_at"]) <= signed_expiry
    with pytest.raises(HumanProtocolError, match="enrollment_assertion_replayed"):
        repo.create_pairing(principal_ref="human:alice", enrollment_proof=pairing_proof, expires_at=pairing_expiry)
    session_info = repo.create_session(grant_id=pairing["grant_id"], pairing_proof=pairing_proof, audience="local-ui", csrf_token="csrf-secret", now=now)
    challenge = repo.issue_challenge(session_id=session_info["session_id"], candidate_id=candidate_id, action="Accept", now=now)
    accepted = repo.submit_decision(
        session_id=session_info["session_id"], challenge_id=challenge["challenge_id"], nonce=challenge["nonce"],
        action="Accept", candidate_id=candidate_id, view_digest=challenge["view_digest"], csrf_token="csrf-secret",
        origin="http://127.0.0.1:5173", expected_origin="http://127.0.0.1:5173", command_id="accept-1", policy_revision=1, now=now,
    )
    replay = repo.submit_decision(
        session_id=session_info["session_id"], challenge_id=challenge["challenge_id"], nonce=challenge["nonce"],
        action="Accept", candidate_id=candidate_id, view_digest=challenge["view_digest"], csrf_token="csrf-secret",
        origin="http://127.0.0.1:5173", expected_origin="http://127.0.0.1:5173", command_id="accept-1", policy_revision=1, now=now,
    )
    assert accepted["acceptance_id"] == replay["acceptance_id"] and replay["idempotent"]
    with pytest.raises(HumanProtocolError, match="agent_promotion"):
        repo.submit_decision(
            session_id=session_info["session_id"], challenge_id=challenge["challenge_id"], nonce=challenge["nonce"],
            action="Accept", candidate_id=candidate_id, view_digest=challenge["view_digest"], csrf_token="csrf-secret",
            origin="http://127.0.0.1:5173", expected_origin="http://127.0.0.1:5173", command_id="accept-agent", human=True, now=now,
        )
    revoke_challenge = repo.issue_challenge(session_id=session_info["session_id"], candidate_id=candidate_id, action="Revoke", now=now)
    with pytest.raises(HumanProtocolError, match="origin"):
        repo.submit_decision(
            session_id=session_info["session_id"], challenge_id=revoke_challenge["challenge_id"], nonce=revoke_challenge["nonce"],
            action="Revoke", candidate_id=candidate_id, view_digest=revoke_challenge["view_digest"], csrf_token="csrf-secret",
            origin="https://evil.example", expected_origin="http://127.0.0.1:5173", command_id="revoke-1", reason="revoke", now=now,
        )
    revoked = repo.submit_decision(
        session_id=session_info["session_id"], challenge_id=revoke_challenge["challenge_id"], nonce=revoke_challenge["nonce"],
        action="Revoke", candidate_id=candidate_id, view_digest=revoke_challenge["view_digest"], csrf_token="csrf-secret",
        origin="http://127.0.0.1:5173", expected_origin="http://127.0.0.1:5173", command_id="revoke-1", reason="human revoked", now=now,
    )
    assert revoked["disposition"] == "REVOKED"
    with pytest.raises(D1bPersistenceError, match="fresh_evidence_required"):
        repo.verify_candidate(
            candidate_id=candidate_id,
            contract_id=contract_id,
            observations=[old_observation],
            trusted_runner="core-test:pytest",
        )
    reaccept_challenge = repo.issue_challenge(
        session_id=session_info["session_id"], candidate_id=candidate_id, action="Accept", now=now
    )
    with pytest.raises(HumanProtocolError, match="fresh_verification_required"):
        repo.submit_decision(
            session_id=session_info["session_id"], challenge_id=reaccept_challenge["challenge_id"], nonce=reaccept_challenge["nonce"],
            action="Accept", candidate_id=candidate_id, view_digest=reaccept_challenge["view_digest"], csrf_token="csrf-secret",
            origin="http://127.0.0.1:5173", expected_origin="http://127.0.0.1:5173", command_id="reaccept-old", now=now,
        )
    session_revoked = repo.revoke_session(session_info["session_id"], csrf_token="csrf-secret", now=now)
    assert session_revoked == {"session_id": session_info["session_id"], "status": "REVOKED"}
    with pytest.raises(HumanProtocolError, match="session_invalid"):
        repo.issue_challenge(session_id=session_info["session_id"], candidate_id=candidate_id, action="Accept", now=now)
    history_count = session.execute(text("SELECT COUNT(*) FROM human_decision_events")).scalar_one()
    assert history_count == 2
    session.commit()
    with pytest.raises(P0PackageError, match="not_current"):
        repo.open_accepted_worktree(acceptance_id=accepted["acceptance_id"], target_dir=tmp / "revoked-worktree", owner_ref="owner")


def test_d1b_supersede_links_another_current_accepted_candidate_in_same_scope(d1b_db):
    session, store, _tmp = d1b_db
    repo = D1bRepository(session, store)
    first = _candidate(repo)
    second = _candidate(repo, result={"app.py": b"after-v2\n", "new.txt": b"new"})
    repo.verify_candidate(
        candidate_id=first["candidate_id"],
        contract_id=first["validation_contract_snapshot_id"],
        observations=[_observation(first["candidate_id"], contract_id=first["validation_contract_snapshot_id"])],
        trusted_runner="core-test:pytest",
    )
    repo.verify_candidate(
        candidate_id=second["candidate_id"],
        contract_id=second["validation_contract_snapshot_id"],
        observations=[_observation(second["candidate_id"], contract_id=second["validation_contract_snapshot_id"])],
        trusted_runner="core-test:pytest",
    )
    now = datetime.now(timezone.utc)
    pairing_expiry = now + timedelta(hours=1)
    pairing_proof = _enrollment_proof("human:supersede", pairing_expiry, issued_at=now)
    pairing = repo.create_pairing(principal_ref="human:supersede", enrollment_proof=pairing_proof, expires_at=pairing_expiry)
    session_info = repo.create_session(grant_id=pairing["grant_id"], pairing_proof=pairing_proof, audience="ui", csrf_token="csrf", now=now)

    first_challenge = repo.issue_challenge(session_id=session_info["session_id"], candidate_id=first["candidate_id"], action="Accept", now=now)
    first_acceptance = repo.submit_decision(
        session_id=session_info["session_id"], challenge_id=first_challenge["challenge_id"], nonce=first_challenge["nonce"],
        action="Accept", candidate_id=first["candidate_id"], view_digest=first_challenge["view_digest"], csrf_token="csrf",
        origin="http://127.0.0.1:5173", expected_origin="http://127.0.0.1:5173", command_id="sup-first-accept", now=now,
    )
    second_challenge = repo.issue_challenge(session_id=session_info["session_id"], candidate_id=second["candidate_id"], action="Accept", now=now)
    second_acceptance = repo.submit_decision(
        session_id=session_info["session_id"], challenge_id=second_challenge["challenge_id"], nonce=second_challenge["nonce"],
        action="Accept", candidate_id=second["candidate_id"], view_digest=second_challenge["view_digest"], csrf_token="csrf",
        origin="http://127.0.0.1:5173", expected_origin="http://127.0.0.1:5173", command_id="sup-second-accept", now=now,
    )
    supersede_challenge = repo.issue_challenge(
        session_id=session_info["session_id"],
        candidate_id=first["candidate_id"],
        action="Supersede",
        replacement_acceptance_id=second_acceptance["acceptance_id"],
        now=now,
    )
    with pytest.raises(HumanProtocolError, match="challenge_replacement_mismatch"):
        repo.submit_decision(
            session_id=session_info["session_id"], challenge_id=supersede_challenge["challenge_id"], nonce=supersede_challenge["nonce"],
            action="Supersede", candidate_id=first["candidate_id"], view_digest=supersede_challenge["view_digest"], csrf_token="csrf",
            origin="http://127.0.0.1:5173", expected_origin="http://127.0.0.1:5173", command_id="sup-link-wrong",
            reason="replace with newer candidate", replacement_acceptance_id=first_acceptance["acceptance_id"], now=now,
        )
    superseded = repo.submit_decision(
        session_id=session_info["session_id"], challenge_id=supersede_challenge["challenge_id"], nonce=supersede_challenge["nonce"],
        action="Supersede", candidate_id=first["candidate_id"], view_digest=supersede_challenge["view_digest"], csrf_token="csrf",
        origin="http://127.0.0.1:5173", expected_origin="http://127.0.0.1:5173", command_id="sup-link", reason="replace with newer candidate",
        replacement_acceptance_id=second_acceptance["acceptance_id"], now=now,
    )
    assert superseded["disposition"] == "SUPERSEDED"
    assert repo._current_disposition(first["candidate_id"]) == ("SUPERSEDED", second_acceptance["acceptance_id"])
    assert repo._current_disposition(second["candidate_id"]) == ("ACCEPTED", second_acceptance["acceptance_id"])
    assert first_acceptance["acceptance_id"] != second_acceptance["acceptance_id"]
    with pytest.raises(P0PackageError, match="not_current"):
        repo._accepted_context(first_acceptance["acceptance_id"])


def test_d1b_p0_worktree_package_round_trip_and_tamper_rejection(d1b_db, monkeypatch):
    session, store, tmp = d1b_db
    repo = D1bRepository(session, store)
    published = _candidate(repo)
    # The P0 path must be exercised against a durable Task/Generation/Run
    # publication, not only the raw fixture publication seam.
    published = _add_scoped_publication(repo, published)
    candidate_id = published["candidate_id"]
    contract_id = published["validation_contract_snapshot_id"]
    repo.verify_candidate(candidate_id=candidate_id, contract_id=contract_id, observations=[_observation(candidate_id, contract_id=contract_id)], trusted_runner="core-test:pytest")
    now = datetime.now(timezone.utc)
    pairing_expiry = now + timedelta(hours=1)
    pairing_proof = _enrollment_proof("human:bob", pairing_expiry, issued_at=now)
    pairing = repo.create_pairing(principal_ref="human:bob", enrollment_proof=pairing_proof, expires_at=pairing_expiry)
    session_info = repo.create_session(grant_id=pairing["grant_id"], pairing_proof=pairing_proof, audience="ui", csrf_token="csrf", now=now)
    challenge = repo.issue_challenge(session_id=session_info["session_id"], candidate_id=candidate_id, action="Accept", now=now)
    accepted = repo.submit_decision(
        session_id=session_info["session_id"], challenge_id=challenge["challenge_id"], nonce=challenge["nonce"],
        action="Accept", candidate_id=candidate_id, view_digest=challenge["view_digest"], csrf_token="csrf",
        origin="http://127.0.0.1:5173", expected_origin="http://127.0.0.1:5173", command_id="accept-p0", now=now,
    )
    workspace = repo.open_accepted_worktree(acceptance_id=accepted["acceptance_id"], target_dir=tmp / "worktree", owner_ref="agent")
    assert workspace["label"] == "Working Copy"
    assert workspace["owner_ref"] == "unassigned"
    assert (tmp / "worktree" / "app.py").read_bytes() == b"after\n"
    assert repo.takeover_workspace(workspace["workspace_id"], owner_ref="human:bob")["taken_over"]
    package = repo.export_p0(acceptance_id=accepted["acceptance_id"], package_path=tmp / "accepted.p0.zip")
    verified = repo.verify_p0_package(tmp / "accepted.p0.zip")
    assert verified["verified"] and verified["candidate_id"] == candidate_id
    portable = tmp / "portable-copy.p0.zip"
    shutil.copy2(tmp / "accepted.p0.zip", portable)
    monkeypatch.delenv("POLYNEXUS_P0_RECEIPT_PRIVATE_KEY", raising=False)
    portable_verified = repo.verify_p0_package(portable)
    assert portable_verified["verified"] and portable_verified["candidate_id"] == candidate_id
    offline_database = tmp / "offline-verifier.db"
    _upgrade(offline_database)
    offline_engine = create_engine("sqlite:///" + offline_database.as_posix(), future=True)
    monkeypatch.delenv("POLYNEXUS_TRUSTED_RUNNER_REF", raising=False)
    monkeypatch.delenv("POLYNEXUS_TRUSTED_RUNNER_ATTESTATION", raising=False)
    with Session(offline_engine) as offline_session:
        offline_repo = D1bRepository(offline_session, ContentStore(tmp / "offline-content"))
        offline_verified = offline_repo.verify_p0_package(portable)
        assert offline_verified["verified"] and offline_verified["candidate_id"] == candidate_id
        offline_restored = offline_repo.reconstruct_p0_package(
            package_path=portable,
            target_dir=tmp / "offline-restored",
        )
        assert offline_restored["verified"]
        assert (tmp / "offline-restored" / "new.txt").read_bytes() == b"new"
    offline_engine.dispose()
    restored = repo.reconstruct_p0_package(package_path=tmp / "accepted.p0.zip", target_dir=tmp / "restored")
    assert restored["verified"] and (tmp / "restored" / "new.txt").read_bytes() == b"new"
    with zipfile.ZipFile(tmp / "missing-source.zip", "w") as archive:
        # A structurally valid-looking package without source closure must fail.
        archive.writestr("manifest.json", b"{}")
    with pytest.raises(P0PackageError):
        repo.verify_p0_package(tmp / "missing-source.zip")
    tampered = tmp / "tampered.p0.zip"
    with zipfile.ZipFile(tmp / "accepted.p0.zip", "r") as source_archive, zipfile.ZipFile(tampered, "w") as target_archive:
        for info in source_archive.infolist():
            value = source_archive.read(info)
            if info.filename == "source/app.py":
                value = b"tampered\n"
            target_archive.writestr(info.filename, value)
    with pytest.raises(P0PackageError):
        repo.verify_p0_package(tampered)
    forged = tmp / "forged-verification.p0.zip"
    with zipfile.ZipFile(tmp / "accepted.p0.zip", "r") as source_archive:
        files = {info.filename: source_archive.read(info) for info in source_archive.infolist()}
    forged_manifest = json.loads(files["manifest.json"])
    forged_manifest["evidence_set"]["observations"][0]["outcome"] = "FAIL"
    files["manifest.json"] = json.dumps(forged_manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    files["evidence.json"] = json.dumps(forged_manifest["evidence_set"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    with zipfile.ZipFile(forged, "w") as target_archive:
        for name, value in files.items():
            target_archive.writestr(name, value)
    with pytest.raises(P0PackageError, match="evidence_identity_mismatch"):
        repo.verify_p0_package(forged)
    forged_runner = tmp / "forged-runner.p0.zip"
    with zipfile.ZipFile(tmp / "accepted.p0.zip", "r") as source_archive:
        files = {info.filename: source_archive.read(info) for info in source_archive.infolist()}
    runner_manifest = json.loads(files["manifest.json"])
    runner_manifest["evidence_set"]["observations"][0]["provenance"]["trusted_runner"] = "core-runner:forged"
    files["manifest.json"] = json.dumps(runner_manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    files["evidence.json"] = json.dumps(runner_manifest["evidence_set"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    with zipfile.ZipFile(forged_runner, "w") as target_archive:
        for name, value in files.items():
            target_archive.writestr(name, value)
    with pytest.raises(P0PackageError, match="evidence_identity_mismatch"):
        repo.verify_p0_package(forged_runner)
    revoke_challenge = repo.issue_challenge(
        session_id=session_info["session_id"],
        candidate_id=candidate_id,
        action="Revoke",
        now=now,
    )
    repo.submit_decision(
        session_id=session_info["session_id"],
        challenge_id=revoke_challenge["challenge_id"],
        nonce=revoke_challenge["nonce"],
        action="Revoke",
        candidate_id=candidate_id,
        view_digest=revoke_challenge["view_digest"],
        csrf_token="csrf",
        origin="http://127.0.0.1:5173",
        expected_origin="http://127.0.0.1:5173",
        command_id="revoke-p0",
        reason="revoke copied package",
        now=now,
    )
    with pytest.raises(P0PackageError, match="not_current"):
        repo.verify_p0_package(portable)
    with pytest.raises(P0PackageError, match="not_current"):
        repo.reconstruct_p0_package(package_path=portable, target_dir=tmp / "revoked-restored")
    # Immutable history cannot be updated or deleted; takeover is the only
    # deliberate mutable managed-worktree field.
    with pytest.raises(IntegrityError):
        session.execute(text("DELETE FROM accepted_results WHERE acceptance_id=:id"), {"id": accepted["acceptance_id"]})
        session.flush()
