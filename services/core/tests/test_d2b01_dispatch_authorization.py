"""Runtime dispatch authority: exact policy, single-use and binding transaction."""
from __future__ import annotations

import asyncio
import shutil
import sys
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from polynexus_core.domain.enums import RunState
from polynexus_core.domain.generation import GenerationConflict
from polynexus_core.domain.models import ContextPackage, Project, Task
from polynexus_core.domain.runtime_dispatch_authorization import (
    DispatchAuthorizationError, DispatchAuthorizationState, DispatchIssuerClass,
)
from polynexus_core.execution_service import ExecutionService
from polynexus_core.persistence.generation import GenerationRepository
from polynexus_core.persistence.repository import (
    SqlContextPackageRepository, SqlEvidenceRepository, SqlProjectRepository,
    SqlRunRepository, SqlRuntimeBindingSnapshotRepository, SqlTaskRepository,
)
from polynexus_core.runtime.routing_policy import (
    DataClassification, DestinationTrust, PolicyDecision, ToolTrust,
)


def _alembic(database: Path, revision: str = "head") -> None:
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
    config.set_main_option("sqlalchemy.url", "sqlite:///" + database.as_posix())
    command.upgrade(config, revision)


@pytest.fixture
def dispatch_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("POLYNEXUS_CONTENT_ROOT", str(tmp_path / "content"))
    monkeypatch.setenv("POLYNEXUS_OPENCODE_EXECUTABLE", sys.executable)
    monkeypatch.setenv("POLYNEXUS_RUNTIME_PROFILE_REF", "opencode.acp.local")
    monkeypatch.setenv("POLYNEXUS_DISPATCH_TEST_ONLY", "1")
    database = tmp_path / "dispatch.db"
    _alembic(database)
    engine = create_engine("sqlite:///" + database.as_posix())
    with Session(engine) as session:
        project = Project(name="technical", classification="PUBLIC")
        SqlProjectRepository(session).add(project)
        session.flush()
        context = ContextPackage(project_id=project.id, version=1, classification="PUBLIC")
        SqlContextPackageRepository(session).add(context)
        session.flush()
        task = Task(project_id=project.id, title="technical", workflow_id="review-minimal",
                    workflow_version=1, context_package_id=context.id, classification="PUBLIC")
        SqlTaskRepository(session).add(task)
        session.commit()
        generations = GenerationRepository(session)
        inputs = generations.prepare(task_id=task.id, context_package_id=context.id,
                                     requirements="technical requirement", validation="technical validation")
        session.commit()
        generations.begin(principal="technical", command_id="begin", task_id=task.id,
                          expected_revision=0, inputs=inputs)
        session.commit()
        run = generations.create_run(principal="technical", command_id="run", task_id=task.id,
                                     revision=1, context_package_id=context.id, expected_control=0)
        session.commit()
        service = ExecutionService(session)
        profile = service._registry._resolve_selected_profile()
        decision, fresh = service._check_policy(run, profile)
        assert decision.decision is PolicyDecision.APPROVAL_REQUIRED
        yield session, service, run, task, context, profile, decision, fresh
    engine.dispose()


def _issue(dispatch_db):
    session, service, run, _task, _context, profile, decision, _fresh = dispatch_db
    authorization = service._issue_test_only_runtime_dispatch_authorization(run.id)
    audit = service._policy_audit_for_run(run.id)
    return authorization, audit


def test_approval_without_authorization_keeps_created_need_action_and_no_binding(dispatch_db) -> None:
    session, service, run, _task, _context, _profile, _decision, _fresh = dispatch_db
    with pytest.raises(GenerationConflict, match="predispatch_policy_denied"):
        asyncio.run(service.execute_existing_run(run.id))
    assert SqlRunRepository(session).get(run.id).state is RunState.CREATED
    assert SqlRuntimeBindingSnapshotRepository(session).get_by_run(run.id) is None
    audit = service._policy_audit_for_run(run.id)
    assert audit.status.value == "NEED_ACTION"
    assert audit.metadata["decision"] == "APPROVAL_REQUIRED"


@pytest.mark.parametrize("field,value,reason", [
    ("run_id", "run_other", "authorization_run_scope_mismatch"),
    ("task_id", "task_other", "authorization_run_scope_mismatch"),
    ("generation_revision", 2, "authorization_generation_mismatch"),
    ("runtime_profile_ref", "reference.local", "authorization_profile_mismatch"),
    ("profile_revision", 2, "authorization_profile_mismatch"),
    ("policy_digest", "0" * 64, "authorization_stale"),
])
def test_exact_scope_and_digest_mismatch_rejected(dispatch_db, field, value, reason) -> None:
    session, service, run, _task, _context, profile, decision, _fresh = dispatch_db
    authorization, audit = _issue(dispatch_db)
    with pytest.raises(DispatchAuthorizationError, match=reason):
        service._dispatch_authorizations.validate(replace(authorization, **{field: value}), run, profile, decision, audit)
    assert service._dispatch_authorizations.get(authorization.authorization_id).state is DispatchAuthorizationState.ISSUED


def test_expired_revoked_and_consumed_authorities_cannot_replay(dispatch_db, monkeypatch: pytest.MonkeyPatch) -> None:
    session, service, run, task, context, profile, decision, _fresh = dispatch_db
    authorization, audit = _issue(dispatch_db)
    from polynexus_core.persistence import runtime_dispatch_authorization as module
    present = module.utc_now
    monkeypatch.setattr(module, "utc_now", lambda: present() + timedelta(minutes=20))
    with pytest.raises(DispatchAuthorizationError, match="authorization_expired"):
        service._dispatch_authorizations.validate(authorization, run, profile, decision, audit)
    monkeypatch.setattr(module, "utc_now", present)
    service._dispatch_authorizations.revoke(authorization.authorization_id)
    session.commit()
    revoked = service._dispatch_authorizations.get(authorization.authorization_id)
    with pytest.raises(DispatchAuthorizationError, match="authorization_replayed"):
        service._dispatch_authorizations.validate(revoked, run, profile, decision, audit)


def test_changed_effective_facts_and_deny_priority(dispatch_db) -> None:
    session, service, run, _task, _context, profile, decision, _fresh = dispatch_db
    authorization, audit = _issue(dispatch_db)
    for altered in (
        replace(decision, classification=DataClassification.INTERNAL),
        replace(decision, destination_trust=DestinationTrust.UNTRUSTED_EXTERNAL),
        replace(decision, tool_trust=ToolTrust.UNTRUSTED),
    ):
        with pytest.raises(DispatchAuthorizationError, match="authorization_stale"):
            service._dispatch_authorizations.validate(authorization, run, profile, altered, audit)
    denied = replace(decision, decision=PolicyDecision.DENY)
    assert service._dispatch_gate(run, profile, denied, audit) == (None, False)
    with pytest.raises(DispatchAuthorizationError, match="authorization_policy_not_approval_required"):
        service._dispatch_authorizations.validate(authorization, run, profile, denied, audit)


def test_policy_recheck_to_deny_blocks_product_start_without_consuming_grant(
    dispatch_db, monkeypatch: pytest.MonkeyPatch,
) -> None:
    session, service, run, _task, _context, _profile, decision, fresh = dispatch_db
    authorization, audit = _issue(dispatch_db)
    denied = replace(decision, decision=PolicyDecision.DENY)
    denied_evidence = replace(fresh, metadata={
        **{key: str(value) for key, value in denied.as_dict().items()},
        "generation_revision": str(run.generation_revision),
    })
    monkeypatch.setattr(service, "_check_policy", lambda _run, _profile: (denied, denied_evidence))
    with pytest.raises(GenerationConflict, match="predispatch_policy_denied"):
        asyncio.run(service.execute_existing_run(run.id))
    assert SqlRunRepository(session).get(run.id).state is RunState.CREATED
    assert SqlRuntimeBindingSnapshotRepository(session).get_by_run(run.id) is None
    assert service._dispatch_authorizations.get(authorization.authorization_id).state is DispatchAuthorizationState.ISSUED
    audits = list(SqlEvidenceRepository(session).list_by_run(run.id))
    assert [e.metadata["decision"] for e in audits if e.source == "runtime.routing_policy"] == ["APPROVAL_REQUIRED"]
    assert [e.metadata["decision"] for e in audits if e.source == "runtime.routing_policy.recheck"] == ["DENY"]


def test_atomic_consume_binding_and_idempotent_repeat(dispatch_db) -> None:
    session, service, run, task, context, _profile, _decision, _fresh = dispatch_db
    authorization, audit = _issue(dispatch_db)
    workflow = service._load_workflow(task.workflow_id, task.workflow_version)
    claimed, selected = service.prepare_claimed_run(run, task, context, workflow)
    assert claimed.state is RunState.STARTING
    assert selected.runtime_profile_ref == "opencode.acp.local"
    snapshot = SqlRuntimeBindingSnapshotRepository(session).get_by_run(run.id)
    assert snapshot and snapshot.run_id == run.id
    consumed = service._dispatch_authorizations.get(authorization.authorization_id)
    assert consumed.state is DispatchAuthorizationState.CONSUMED
    with pytest.raises(DispatchAuthorizationError, match="authorization_replayed"):
        service._dispatch_authorizations.validate(consumed, run, selected, _decision, audit)
    assert [e.event_kind for e in service._dispatch_authorizations.events(authorization.authorization_id)] == ["ISSUE", "CONSUME"]
    sources = [e.source for e in SqlEvidenceRepository(session).list_by_run(run.id)]
    assert sources.count("runtime.routing_policy") == 1
    assert sources.count("runtime.dispatch_authorization") == 1
    assert service._policy_audit_for_run(run.id).metadata["decision"] == "APPROVAL_REQUIRED"
    with pytest.raises((GenerationConflict, DispatchAuthorizationError)):
        service.prepare_claimed_run(claimed, task, context, workflow)
    assert SqlRuntimeBindingSnapshotRepository(session).get_by_run(run.id) == snapshot
    assert [e.event_kind for e in service._dispatch_authorizations.events(authorization.authorization_id)] == ["ISSUE", "CONSUME"]


def test_binding_failure_rolls_back_claim_and_consumption(dispatch_db, monkeypatch: pytest.MonkeyPatch) -> None:
    session, service, run, task, context, _profile, _decision, _fresh = dispatch_db
    authorization, _audit = _issue(dispatch_db)
    workflow = service._load_workflow(task.workflow_id, task.workflow_version)
    def fail(_snapshot):
        raise RuntimeError("injected binding failure")
    monkeypatch.setattr(service._binding_repo, "insert_once", fail)
    with pytest.raises(RuntimeError, match="injected binding failure"):
        service.prepare_claimed_run(run, task, context, workflow)
    assert SqlRunRepository(session).get(run.id).state is RunState.CREATED
    assert SqlRuntimeBindingSnapshotRepository(session).get_by_run(run.id) is None
    assert service._dispatch_authorizations.get(authorization.authorization_id).state is DispatchAuthorizationState.ISSUED
    assert [e.event_kind for e in service._dispatch_authorizations.events(authorization.authorization_id)] == ["ISSUE"]


def test_second_run_cannot_reuse_first_run_authorization(dispatch_db) -> None:
    session, service, run, task, context, profile, decision, _fresh = dispatch_db
    authorization, audit = _issue(dispatch_db)
    second = GenerationRepository(session).create_run(principal="technical", command_id="run-2",
                                                    task_id=task.id, revision=1,
                                                    context_package_id=context.id, expected_control=0)
    session.commit()
    second_decision, second_fresh = service._check_policy(second, profile)
    second_audit = service._policy_evidence_for_run(second, second_fresh)
    assert service._dispatch_gate(second, profile, second_decision, second_audit) == (None, False)
    with pytest.raises(DispatchAuthorizationError, match="authorization_run_scope_mismatch"):
        service._dispatch_authorizations.validate(authorization, second, profile, second_decision, second_audit)


def test_issuer_boundary_test_only_is_not_human_acceptance(dispatch_db, monkeypatch: pytest.MonkeyPatch) -> None:
    session, service, run, _task, _context, profile, decision, _fresh = dispatch_db
    authorization, audit = _issue(dispatch_db)
    assert authorization.issuer_class is DispatchIssuerClass.TEST_ONLY
    assert authorization.issuer_ref.startswith("test-only:")
    with pytest.raises(DispatchAuthorizationError, match="authorization_human_proof_invalid"):
        service._dispatch_authorizations.issue_human(run, profile, decision, audit,
                                                     session_id="agent-runtime-credential", csrf_token="not-human")
    monkeypatch.delenv("POLYNEXUS_DISPATCH_TEST_ONLY")
    with pytest.raises(DispatchAuthorizationError, match="authorization_test_only_environment_invalid"):
        service._dispatch_authorizations.validate(authorization, run, profile, decision, audit)


def test_migration_upgrade_and_backup_restore(tmp_path: Path) -> None:
    old = tmp_path / "pre-0010.db"
    _alembic(old, "0009")
    backup = tmp_path / "backup.db"
    shutil.copy2(old, backup)
    _alembic(old, "head")
    engine = create_engine("sqlite:///" + old.as_posix())
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0010"
        assert connection.execute(text("SELECT count(*) FROM sqlite_master WHERE type='table' AND name LIKE 'runtime_dispatch_%'")).scalar_one() == 2
    engine.dispose()
    restored = create_engine("sqlite:///" + backup.as_posix())
    with restored.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0009"
        assert connection.execute(text("SELECT count(*) FROM sqlite_master WHERE type='table' AND name LIKE 'runtime_dispatch_%'")).scalar_one() == 0
    restored.dispose()


def test_db_scope_and_audit_rows_are_immutable(dispatch_db) -> None:
    session, service, run, _task, _context, _profile, _decision, _fresh = dispatch_db
    authorization, _audit = _issue(dispatch_db)
    with pytest.raises(Exception, match="Dispatch authorization scope immutable"):
        session.execute(text("UPDATE runtime_dispatch_authorizations SET task_id='other' WHERE authorization_id=:id"), {"id": authorization.authorization_id})
    session.rollback()
    with pytest.raises(Exception, match="Dispatch authorization audit immutable"):
        session.execute(text("DELETE FROM runtime_dispatch_authorization_events WHERE authorization_id=:id"), {"id": authorization.authorization_id})
    session.rollback()


def test_database_rejects_two_issued_authorizations_for_one_run(dispatch_db) -> None:
    session, _service, _run, _task, _context, _profile, _decision, _fresh = dispatch_db
    authorization, _audit = _issue(dispatch_db)
    columns = [row[1] for row in session.execute(text("PRAGMA table_info(runtime_dispatch_authorizations)"))]
    names = ", ".join(columns)
    values = ", ".join("'duplicate-authorization'" if name == "authorization_id" else name for name in columns)
    with pytest.raises(Exception, match="UNIQUE constraint failed"):
        session.execute(text(
            f"INSERT INTO runtime_dispatch_authorizations ({names}) "
            f"SELECT {values} FROM runtime_dispatch_authorizations WHERE authorization_id=:id"
        ), {"id": authorization.authorization_id})
    session.rollback()
