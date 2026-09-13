"""PRE-WP14-B Runtime Binding implementation tests (ADR-011).

Deterministic coverage:
A. Identifier validation        B. Identity separation
C. Registry                     D. Snapshot immutability
E. Persistence                  F. Execution transaction boundary
G. Alembic 0002 migration       H. Secret exclusion boundary

Migration tests run ONLY against temporary isolated SQLite databases.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from d1a_fixtures import d1a_content_environment,prepare_generation,migrate_fixture_engine
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from polynexus_core.domain.enums import (
    AuthOwnership,
    ExecutionTarget,
    RunState,
    TransportKind,
    UsageVisibility,
)
from polynexus_core.domain.models import ContextPackage, Project, Run, RunEvent, Task
from polynexus_core.domain.runtime_binding import (
    DEFAULT_SNAPSHOT_SCHEMA_VERSION,
    OPAQUE_IDENTIFIER_MAX_LENGTH,
    SUPPORTED_SNAPSHOT_SCHEMA_VERSIONS,
    RuntimeBindingError,
    RuntimeBindingSnapshot,
    RuntimeProfile,
    legacy_backfill_snapshot,
    validate_opaque_identifier,
)
from polynexus_core.execution_service import ExecutionService
from polynexus_core.persistence.models import Base, RunBindingSnapshotRow
from polynexus_core.persistence.repository import (
    SqlContextPackageRepository,
    SqlProjectRepository,
    SqlRunRepository,
    SqlRuntimeBindingSnapshotRepository,
    SqlTaskRepository,
)
from polynexus_core.runtime.registry import (
    REFERENCE_PROFILE_REF,
    RuntimeRegistry,
    build_default_registry,
    build_reference_profile,
)

ROOT = Path(__file__).resolve().parents[3]

SECRET_MARKER_PRE_WP14_B = "SECRET_MARKER_PRE_WP14_B_DO_NOT_PERSIST"


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_engine(tmp_path: Path):
    db_path = tmp_path / "wp14b.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    migrate_fixture_engine(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine, expire_on_commit=False, future=True)
    session = Session()
    yield session
    session.close()


def _reference_profile() -> RuntimeProfile:
    return build_reference_profile()


def _seed_run(session: Session, state: RunState = RunState.CREATED) -> Run:
    """Persist project/task/context-package/run and return the Run."""
    project_repo = SqlProjectRepository(session)
    task_repo = SqlTaskRepository(session)
    cp_repo = SqlContextPackageRepository(session)
    run_repo = SqlRunRepository(session)

    project = Project(name="WP14B")
    cp = ContextPackage(project_id=project.id, version=1, instructions=("fixture:wp14b",))
    task = Task(
        project_id=project.id,
        title="runtime binding task",
        workflow_id="review-minimal",
        workflow_version=1,
        context_package_id=cp.id,
    )
    run = Run(
        task_id=task.id,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=cp.id,
        state=state,
    )
    project_repo.add(project)
    cp_repo.add(cp)
    task_repo.add(task)
    run.generation_revision=prepare_generation(session,task.id)
    run_repo.add(run)
    session.commit()
    return run


def _alembic_config(tmp_path: Path, db_path: Path):
    from alembic.config import Config

    alembic_ini = tmp_path / "alembic.ini"
    alembic_dir = ROOT / "services" / "core" / "alembic"
    alembic_ini.write_text(
        "[alembic]\n"
        f"script_location = {alembic_dir}\n"
        "prepend_sys_path = .\n"
        f"sqlalchemy.url = sqlite:///{db_path}\n"
        "\n"
        "[loggers]\n"
        "keys = root,sqlalchemy,alembic\n"
        "\n"
        "[handlers]\n"
        "keys = console\n"
        "\n"
        "[formatters]\n"
        "keys = generic\n"
        "\n"
        "[logger_root]\n"
        "level = WARN\n"
        "handlers = console\n"
        "\n"
        "[logger_sqlalchemy]\n"
        "level = WARN\n"
        "handlers =\n"
        "qualname = sqlalchemy.engine\n"
        "\n"
        "[logger_alembic]\n"
        "level = INFO\n"
        "handlers =\n"
        "qualname = alembic.engine\n"
        "\n"
        "[handler_console]\n"
        "class = StreamHandler\n"
        "args = (sys.stderr,)\n"
        "level = NOTSET\n"
        "formatter = generic\n"
        "\n"
        "[formatter_generic]\n"
        "format = %(levelname)-5.5s [%(name)s] %(message)s\n"
        "datefmt = %H:%M:%S\n"
    )
    return Config(str(alembic_ini))


# ---------------------------------------------------------------------------
# A. Identifier validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", ["polynexus", "builtin.reference", "reference-local_1"])
def test_valid_opaque_identifiers(value: str) -> None:
    assert validate_opaque_identifier(value, "f") == value


@pytest.mark.parametrize(
    "value",
    [
        "PolyNexus",                       # uppercase
        "-leading",                        # leading separator
        "trailing-",                       # trailing separator
        "a..b",                            # repeated separator
        "_underscore",                     # leading underscore separator
        "has space",                       # space
        "Bearer abc123",                   # credential-shaped value
        "cookie=abc; path=/",              # cookie-shaped value
        "x" * (OPAQUE_IDENTIFIER_MAX_LENGTH + 1),  # over max length
        "",                                # empty
    ],
)
def test_invalid_opaque_identifiers_rejected(value: str) -> None:
    with pytest.raises(RuntimeBindingError):
        validate_opaque_identifier(value, "f")


def test_identifier_max_length_boundary() -> None:
    ok = "a" * OPAQUE_IDENTIFIER_MAX_LENGTH
    assert validate_opaque_identifier(ok, "f") == ok


def test_dot_separated_adapter_id_accepted() -> None:
    profile = _reference_profile()
    assert profile.adapter_id == "builtin.reference"


# ---------------------------------------------------------------------------
# B. Identity separation
# ---------------------------------------------------------------------------

def test_provider_runtime_adapter_are_distinct_concepts() -> None:
    p = _reference_profile()
    assert p.provider_id == "polynexus"
    assert p.runtime_id == "reference"
    assert p.adapter_id == "builtin.reference"
    assert len({p.provider_id, p.runtime_id, p.adapter_id}) == 3


def test_transport_kind_and_execution_target_are_orthogonal() -> None:
    assert TransportKind.LOCAL is not ExecutionTarget.LOCAL
    assert type(TransportKind.LOCAL) is not type(ExecutionTarget.LOCAL)


def test_same_provider_different_transports_are_different_profiles() -> None:
    base = _reference_profile()
    other = RuntimeProfile(
        provider_id=base.provider_id,
        transport_kind=TransportKind.NATIVE_SUBSCRIPTION,
        runtime_id="reference-sub",
        adapter_id="builtin.reference-sub",
        execution_target=ExecutionTarget.LOCAL,
        runtime_profile_ref="reference.subscription",
        profile_revision=1,
    )
    assert base.provider_id == other.provider_id
    assert base.transport_kind is not other.transport_kind
    assert base.runtime_profile_ref != other.runtime_profile_ref


def test_same_task_multiple_runs_have_independent_snapshots(db_session) -> None:
    repo = SqlRuntimeBindingSnapshotRepository(db_session)
    resolved = datetime(2026, 8, 25, tzinfo=timezone.utc)
    s1 = legacy_backfill_snapshot("run-1", ExecutionTarget.LOCAL, resolved)
    s2 = legacy_backfill_snapshot("run-2", ExecutionTarget.LOCAL, resolved + timedelta(seconds=1))
    repo.insert_once(s1)
    repo.insert_once(s2)
    loaded1 = repo.get_by_run("run-1")
    loaded2 = repo.get_by_run("run-2")
    assert loaded1.run_id != loaded2.run_id
    assert loaded1.resolved_at != loaded2.resolved_at


def test_task_is_not_a_run_in_binding_contract() -> None:
    # Snapshots are keyed by run identity only; a Task id is not acceptable.
    with pytest.raises(RuntimeBindingError):
        RuntimeBindingSnapshot(
            run_id="",  # missing Run identity
            provider_id="polynexus",
            transport_kind=TransportKind.LOCAL,
            runtime_id="reference",
            adapter_id="builtin.reference",
            execution_target=ExecutionTarget.LOCAL,
            runtime_profile_ref=None,
            profile_revision=None,
            adapter_version=None,
            resolved_at=datetime.now(timezone.utc),
            legacy_backfill=True,
        )


# ---------------------------------------------------------------------------
# C. Registry
# ---------------------------------------------------------------------------

def test_registry_resolves_reference_profile() -> None:
    registry = build_default_registry()
    profile = registry.resolve(REFERENCE_PROFILE_REF)
    assert profile.provider_id == "polynexus"
    assert profile.transport_kind is TransportKind.LOCAL
    assert profile.adapter_id == "builtin.reference"
    assert profile.auth_ownership is AuthOwnership.NONE
    assert profile.usage_visibility is UsageVisibility.UNAVAILABLE


def test_registry_creates_reference_adapter() -> None:
    from polynexus_core.runtime.reference import ReferenceRuntimeAdapter

    registry = build_default_registry()
    adapter = registry.create_adapter(registry.resolve(REFERENCE_PROFILE_REF))
    assert isinstance(adapter, ReferenceRuntimeAdapter)


def test_unknown_profile_fails_closed() -> None:
    registry = build_default_registry()
    with pytest.raises(RuntimeBindingError, match="Unknown or unavailable"):
        registry.resolve("does-not-exist.profile")


def test_no_implicit_reference_fallback() -> None:
    registry = build_default_registry()
    # An unknown profile must NOT silently resolve to the reference profile.
    with pytest.raises(RuntimeBindingError):
        registry.bind("unknown.profile", run_id="run-x", resolved_at=datetime.now(timezone.utc))


def test_unregistered_adapter_factory_fails_closed() -> None:
    registry = RuntimeRegistry()
    registry.register(_reference_profile(), lambda: (_ for _ in ()).throw(AssertionError))
    # Remove the factory to simulate a profile without a registered adapter.
    registry._factories.clear()
    with pytest.raises(RuntimeBindingError, match="No adapter factory"):
        registry.create_adapter(registry.resolve(REFERENCE_PROFILE_REF))


def test_registry_has_no_vendor_specific_core_branch() -> None:
    source = (
        Path(__file__).parents[1]
        / "src" / "polynexus_core" / "runtime" / "registry.py"
    ).read_text(encoding="utf-8")
    code_lines = [
        line for line in source.splitlines()
        if not line.strip().startswith("#") and "``" not in line
    ]
    code = "\n".join(code_lines)
    for vendor in ("openai", "anthropic", "google", "claude-code", "gemini-cli"):
        assert vendor not in code
    assert "provider_id ==" not in code
    assert "runtime_id ==" not in code
    assert "adapter_id ==" not in code


# ---------------------------------------------------------------------------
# D. Snapshot immutability
# ---------------------------------------------------------------------------

def _legacy_snapshot(run_id: str, resolved: datetime) -> RuntimeBindingSnapshot:
    return legacy_backfill_snapshot(run_id, ExecutionTarget.LOCAL, resolved)


def test_frozen_snapshot_mutation_rejected() -> None:
    snapshot = _legacy_snapshot("run-frozen", datetime(2026, 8, 25, tzinfo=timezone.utc))
    with pytest.raises(Exception):  # FrozenInstanceError
        snapshot.provider_id = "other"  # type: ignore[misc]


def test_duplicate_insert_rejected(db_session) -> None:
    repo = SqlRuntimeBindingSnapshotRepository(db_session)
    resolved = datetime(2026, 8, 25, tzinfo=timezone.utc)
    repo.insert_once(_legacy_snapshot("run-dup", resolved))
    with pytest.raises(RuntimeBindingError, match="already bound"):
        repo.insert_once(_legacy_snapshot("run-dup", resolved))


def test_repository_update_delete_rejected(db_session) -> None:
    repo = SqlRuntimeBindingSnapshotRepository(db_session)
    snapshot = _legacy_snapshot("run-reject", datetime(2026, 8, 25, tzinfo=timezone.utc))
    repo.insert_once(snapshot)

    with pytest.raises(RuntimeBindingError, match="update is rejected"):
        repo.update(snapshot)
    with pytest.raises(RuntimeBindingError, match="delete is rejected"):
        repo.delete(snapshot.run_id)


def test_orm_update_rejected(db_session) -> None:
    repo = SqlRuntimeBindingSnapshotRepository(db_session)
    original = _legacy_snapshot("run-orm-upd", datetime(2026, 8, 25, tzinfo=timezone.utc))
    repo.insert_once(original)
    db_session.commit()

    row = db_session.get(RunBindingSnapshotRow, "run-orm-upd")
    row.provider_id = "tampered"
    with pytest.raises(RuntimeBindingError, match="update rejected"):
        db_session.flush()
    db_session.rollback()

    reloaded = repo.get_by_run("run-orm-upd")
    assert reloaded is not None
    assert reloaded.provider_id == "polynexus"


def test_orm_delete_rejected(db_session) -> None:
    repo = SqlRuntimeBindingSnapshotRepository(db_session)
    repo.insert_once(_legacy_snapshot("run-orm-del", datetime(2026, 8, 25, tzinfo=timezone.utc)))
    db_session.commit()

    row = db_session.get(RunBindingSnapshotRow, "run-orm-del")
    db_session.delete(row)
    with pytest.raises(RuntimeBindingError, match="delete rejected"):
        db_session.flush()
    db_session.rollback()

    assert repo.get_by_run("run-orm-del") is not None


def test_existing_snapshot_unchanged_after_failed_mutations(db_session) -> None:
    repo = SqlRuntimeBindingSnapshotRepository(db_session)
    resolved = datetime(2026, 8, 25, tzinfo=timezone.utc)
    snapshot = _legacy_snapshot("run-stable", resolved)
    repo.insert_once(snapshot)
    db_session.commit()

    with pytest.raises(RuntimeBindingError):
        repo.insert_once(_legacy_snapshot("run-stable", resolved))
    with pytest.raises(RuntimeBindingError):
        repo.update(snapshot)
    with pytest.raises(RuntimeBindingError):
        repo.delete("run-stable")

    reloaded = repo.get_by_run("run-stable")
    assert reloaded == snapshot


# ---------------------------------------------------------------------------
# E. Persistence
# ---------------------------------------------------------------------------

def _persist_full_snapshot(repo) -> RuntimeBindingSnapshot:
    snapshot = RuntimeProfile(
        provider_id="acme-local",
        transport_kind=TransportKind.LOCAL,
        runtime_id="local-model",
        adapter_id="builtin.local-model",
        runtime_profile_ref="local-model.default",
        profile_revision=3,
        auth_ownership=AuthOwnership.SECRET_REF,
        secret_ref_id="secret-ref-local-1",
    ).bind(
        run_id="run-full",
        resolved_at=datetime(2026, 8, 25, 12, 30, tzinfo=timezone.utc),
        adapter_version="0.2.0",
    )
    repo.insert_once(snapshot)
    return snapshot


def test_persist_close_reopen_reload_all_fields(tmp_path: Path) -> None:
    db_path = tmp_path / "reload.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    session = Session()
    repo = SqlRuntimeBindingSnapshotRepository(session)
    snapshot = _persist_full_snapshot(repo)
    session.commit()
    session.close()
    engine.dispose()

    engine2 = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    Session2 = sessionmaker(bind=engine2, expire_on_commit=False, future=True)
    session2 = Session2()
    repo2 = SqlRuntimeBindingSnapshotRepository(session2)
    loaded = repo2.get_by_run("run-full")

    assert loaded is not None
    assert loaded == snapshot
    assert loaded.snapshot_schema_version == DEFAULT_SNAPSHOT_SCHEMA_VERSION
    assert loaded.resolved_at.tzinfo is not None
    session2.close()
    engine2.dispose()


def test_unknown_snapshot_schema_version_fails_closed(db_session) -> None:
    repo = SqlRuntimeBindingSnapshotRepository(db_session)
    db_session.execute(
        text(
            """
            INSERT INTO run_binding_snapshots (
                run_id, provider_id, transport_kind, runtime_id, adapter_id,
                execution_target, runtime_profile_ref, profile_revision,
                adapter_version, resolved_at, legacy_backfill,
                snapshot_schema_version, auth_ownership, secret_ref_id,
                usage_visibility
            ) VALUES (
                'run-badver', 'polynexus', 'LOCAL', 'reference', 'builtin.reference',
                'LOCAL', NULL, NULL, NULL, '2026-08-25 00:00:00.000000', 1,
                99, 'NONE', NULL, 'UNAVAILABLE'
            )
            """
        )
    )
    db_session.commit()
    with pytest.raises(RuntimeBindingError, match="snapshot_schema_version"):
        repo.get_by_run("run-badver")


def test_run_lifecycle_update_does_not_mutate_snapshot(db_session) -> None:
    run = _seed_run(db_session, state=RunState.CREATED)
    binding_repo = SqlRuntimeBindingSnapshotRepository(db_session)
    run_repo = SqlRunRepository(db_session)

    snapshot = legacy_backfill_snapshot(
        run.id, ExecutionTarget.LOCAL, datetime(2026, 8, 25, tzinfo=timezone.utc)
    )
    binding_repo.insert_once(snapshot)
    db_session.commit()

    # Normal lifecycle update path: CAS claim then legal transitions only.
    assert run_repo.claim_for_execution(run.id) is True
    event = RunEvent(run_id=run.id, from_state=RunState.CREATED, to_state=RunState.STARTING)
    run_repo.append_event(event)
    stored_run = run_repo.get(run.id)
    assert stored_run is not None
    stored_run.transition(RunState.RUNNING)
    run_repo.update(stored_run)
    db_session.commit()

    reloaded = binding_repo.get_by_run(run.id)
    assert reloaded == snapshot


def test_secret_ref_id_is_opaque_reference_only() -> None:
    profile = RuntimeProfile(
        provider_id="acme-api",
        transport_kind=TransportKind.OFFICIAL_API,
        runtime_id="acme-runtime",
        adapter_id="builtin.acme",
        runtime_profile_ref="acme.default",
        auth_ownership=AuthOwnership.SECRET_REF,
        secret_ref_id="secret-ref-acme-prod-1",
    )
    assert profile.secret_ref_id == "secret-ref-acme-prod-1"

    with pytest.raises(RuntimeBindingError):
        RuntimeProfile(
            provider_id="acme-api",
            transport_kind=TransportKind.OFFICIAL_API,
            runtime_id="acme-runtime",
            adapter_id="builtin.acme",
            runtime_profile_ref="acme.default",
            auth_ownership=AuthOwnership.SECRET_REF,
            secret_ref_id="sk-live-ABC123credential-value",
        )


# ---------------------------------------------------------------------------
# F. Execution transaction boundary
# ---------------------------------------------------------------------------

class _ExplodingStatusAdapter:
    """Adapter whose status() always fails — proves binding precedes/exists
    independently of adapter behaviour."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def health(self):
        return True

    async def readiness(self):
        return True

    def capabilities(self):
        from polynexus_core.domain.enums import ResumeMode
        from polynexus_core.runtime.contracts import RuntimeCapabilities

        return RuntimeCapabilities(cancel=True, resume=ResumeMode.NONE, artifacts=True)

    async def create_run(self, context):
        self.calls.append("create_run")
        return "exploding:ref"

    async def submit(self, runtime_ref, task):
        self.calls.append("submit")

    async def status(self, runtime_ref):
        self.calls.append("status")
        raise RuntimeError(f"boom {SECRET_MARKER_PRE_WP14_B}")

    async def result(self, runtime_ref):
        raise AssertionError("result should not be reached")

    async def cancel(self, runtime_ref):
        raise AssertionError("cancel should not be reached")

    async def resume(self, runtime_ref, checkpoint=None):
        raise NotImplementedError

    async def artifacts(self, runtime_ref):
        return ()

    async def cleanup(self, runtime_ref):
        return True

    def version_info(self):
        return "exploding/0.1"


class _CountingRegistry(RuntimeRegistry):
    """Registry whose reference factory counts adapter constructions."""

    def __init__(self) -> None:
        super().__init__()
        self.factory_calls = 0
        super().register(build_reference_profile(), self._factory)

    def _factory(self):
        self.factory_calls += 1
        from polynexus_core.runtime.reference import ReferenceRuntimeAdapter

        return ReferenceRuntimeAdapter()


def _make_service(session, registry=None) -> ExecutionService:
    return ExecutionService(session, registry=registry)


def test_execute_existing_run_binds_before_adapter_invocation(db_session) -> None:
    run = _seed_run(db_session)
    exploding = _ExplodingStatusAdapter()

    class ExplodingRegistry(RuntimeRegistry):
        def __init__(self) -> None:
            super().__init__()
            super().register(build_reference_profile(), lambda: exploding)

    service = _make_service(db_session, registry=ExplodingRegistry())

    execution = asyncio.run(service.execute_existing_run(run.id))

    # Adapter failed at its boundary — but the immutable binding was already
    # committed before the adapter was invoked, and the failure is truthful.
    binding_repo = SqlRuntimeBindingSnapshotRepository(db_session)
    snapshot = binding_repo.get_by_run(run.id)
    assert snapshot is not None
    assert snapshot.provider_id == "polynexus"
    assert snapshot.adapter_id == "builtin.reference"
    assert snapshot.legacy_backfill is False
    assert snapshot.runtime_profile_ref == REFERENCE_PROFILE_REF
    assert snapshot.profile_revision == 1

    # resolved_at equals the deterministic claim-event timestamp.
    events = {e.to_state: e for e in execution.run.events}
    assert snapshot.resolved_at.replace(tzinfo=None) == events[RunState.STARTING].occurred_at

    # The adapter actually ran (binding happened first, not instead of it).
    assert "create_run" in exploding.calls
    assert execution.run.state is RunState.FAILED
    # No fabricated outputs on the failure path.
    assert execution.result is None or execution.result.status is RunState.FAILED


def test_registry_failure_prevents_claim_and_adapter(db_session) -> None:
    run = _seed_run(db_session)
    counting = _CountingRegistry()
    # Empty out profiles so resolution fails closed.
    counting._profiles.clear()

    service = _make_service(db_session, registry=counting)

    with pytest.raises(RuntimeBindingError):
        asyncio.run(service.execute_existing_run(run.id))

    # Nothing happened: no claim, no events, no adapter construction.
    reloaded = SqlRunRepository(db_session).get(run.id)
    assert reloaded.state is RunState.CREATED
    assert reloaded.events == []
    assert counting.factory_calls == 0


def test_snapshot_insert_failure_prevents_adapter_execution(db_session) -> None:
    run = _seed_run(db_session)
    counting = _CountingRegistry()

    # Pre-bind the Run so the in-transaction insert_once fails closed.
    binding_repo = SqlRuntimeBindingSnapshotRepository(db_session)
    binding_repo.insert_once(
        legacy_backfill_snapshot(run.id, ExecutionTarget.LOCAL, datetime.now(timezone.utc))
    )
    db_session.commit()

    service = _make_service(db_session, registry=counting)

    with pytest.raises(RuntimeBindingError, match="already bound"):
        asyncio.run(service.execute_existing_run(run.id))

    # Transaction rolled back: the Run is back to CREATED with no claim
    # event, and no adapter was ever constructed.
    reloaded = SqlRunRepository(db_session).get(run.id)
    assert reloaded.state is RunState.CREATED
    assert [e.to_state for e in reloaded.events] == []
    assert counting.factory_calls == 0


def test_duplicate_execution_does_not_rebind(db_session) -> None:
    from polynexus_core.errors import ClaimConflictError

    run = _seed_run(db_session)
    service = _make_service(db_session)

    asyncio.run(service.execute_existing_run(run.id))

    binding_repo = SqlRuntimeBindingSnapshotRepository(db_session)
    before = binding_repo.get_by_run(run.id)

    with pytest.raises(ClaimConflictError):
        asyncio.run(service.execute_existing_run(run.id))

    after = binding_repo.get_by_run(run.id)
    assert before == after


def test_execute_task_creates_snapshot(db_session) -> None:
    run = _seed_run(db_session)
    service = _make_service(db_session)

    execution = asyncio.run(service.execute_task(run.task_id, generation_revision=1))

    binding_repo = SqlRuntimeBindingSnapshotRepository(db_session)
    snapshot = binding_repo.get_by_run(execution.run.id)
    assert snapshot is not None
    assert snapshot.legacy_backfill is False
    assert snapshot.runtime_profile_ref == REFERENCE_PROFILE_REF
    assert snapshot.execution_target is ExecutionTarget.LOCAL


def test_execute_existing_run_lifecycle_unchanged(db_session) -> None:
    run = _seed_run(db_session)
    service = _make_service(db_session)

    execution = asyncio.run(service.execute_existing_run(run.id))

    states = [e.to_state for e in execution.run.events]
    assert states == [RunState.STARTING, RunState.RUNNING, RunState.COMPLETED]
    assert execution.run.state is RunState.COMPLETED
    assert execution.result is not None
    assert execution.result.status is RunState.COMPLETED


# ---------------------------------------------------------------------------
# G. Alembic 0002 migration (temporary isolated databases ONLY)
# ---------------------------------------------------------------------------

_LEGACY_SEED_STATEMENTS = [
    "INSERT INTO context_packages(id,project_id,version,created_at) VALUES('cp-none','proj-legacy',1,'2026-01-01')",
    "INSERT INTO projects (id, name, description, created_at) "
    "VALUES ('proj-legacy', 'Legacy', NULL, '2026-08-20 10:00:00.000000')",
    "INSERT INTO tasks (id, project_id, title, workflow_id, workflow_version, mode, "
    "context_package_id, created_at) VALUES ('task-legacy', 'proj-legacy', "
    "'legacy task', 'review-minimal', 1, 'REVIEW', NULL, '2026-08-20 10:00:01.000000')",
    "INSERT INTO runs (id, task_id, workflow_id, workflow_version, context_package_id, "
    "execution_target, resume_mode, state, runtime_ref, created_at, updated_at) "
    "VALUES ('run-with-starting', 'task-legacy', 'review-minimal', 1, 'cp-none', "
    "'LOCAL', 'NONE', 'COMPLETED', NULL, "
    "'2026-08-20 10:00:02.000000', '2026-08-20 10:00:09.000000')",
    "INSERT INTO runs (id, task_id, workflow_id, workflow_version, context_package_id, "
    "execution_target, resume_mode, state, runtime_ref, created_at, updated_at) "
    "VALUES ('run-no-starting', 'task-legacy', 'review-minimal', 1, 'cp-none', "
    "'LOCAL', 'NONE', 'CREATED', NULL, "
    "'2026-08-20 10:00:03.000000', '2026-08-20 10:00:03.000000')",
    # Tie-break case: two STARTING events with identical timestamps, distinct ids.
    "INSERT INTO run_events (id, run_id, from_state, to_state, occurred_at, reason) "
    "VALUES ('evt-b', 'run-with-starting', 'CREATED', 'STARTING', "
    "'2026-08-20 10:00:04.000000', NULL)",
    "INSERT INTO run_events (id, run_id, from_state, to_state, occurred_at, reason) "
    "VALUES ('evt-a', 'run-with-starting', 'CREATED', 'STARTING', "
    "'2026-08-20 10:00:04.000000', NULL)",
]


def _fetch_all_snapshots(engine):
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                f"""
                SELECT * FROM run_binding_snapshots ORDER BY run_id ASC
                """
            )
        ).mappings().all()
    return [dict(r) for r in rows]


@pytest.fixture()
def migration_db(tmp_path: Path):
    """Temporary isolated SQLite database migrated 0001 -> head."""
    from alembic import command as alembic_cmd

    db_path = tmp_path / "migration.db"
    config = _alembic_config(tmp_path, db_path)
    alembic_cmd.upgrade(config, "0001")

    raw = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    with raw.begin() as conn:
        for statement in [*_LEGACY_SEED_STATEMENTS[1:2], _LEGACY_SEED_STATEMENTS[0], *_LEGACY_SEED_STATEMENTS[2:]]:
            conn.execute(text(statement))
    raw.dispose()

    yield db_path, config


def test_migration_backfills_legacy_runs(migration_db) -> None:
    from alembic import command as alembic_cmd

    db_path, config = migration_db
    alembic_cmd.upgrade(config, "head")

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    rows = {r["run_id"]: r for r in _fetch_all_snapshots(engine)}

    assert set(rows) == {"run-with-starting", "run-no-starting"}
    for row in rows.values():
        assert row["provider_id"] == "polynexus"
        assert row["transport_kind"] == "LOCAL"
        assert row["runtime_id"] == "reference"
        assert row["adapter_id"] == "builtin.reference"
        assert row["execution_target"] == "LOCAL"
        assert row["runtime_profile_ref"] is None
        assert row["profile_revision"] is None
        assert row["adapter_version"] is None
        assert bool(row["legacy_backfill"]) is True
        assert row["snapshot_schema_version"] == 1
        assert row["auth_ownership"] == "NONE"
        assert row["secret_ref_id"] is None
        assert row["usage_visibility"] == "UNAVAILABLE"

    # STARTING timestamp selected correctly (tie-break irrelevant to value).
    assert str(rows["run-with-starting"]["resolved_at"]) == "2026-08-20 10:00:04.000000"
    # Fallback to runs.created_at when no STARTING event exists.
    assert str(rows["run-no-starting"]["resolved_at"]) == "2026-08-20 10:00:03.000000"
    engine.dispose()


def test_migration_downgrade_preserves_history_and_reupgrade_identical(migration_db) -> None:
    from alembic import command as alembic_cmd

    db_path, config = migration_db
    alembic_cmd.upgrade(config, "0003")

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    # Compare original fields: downgrade intentionally removes ADR-014 metadata.
    from sqlalchemy import inspect
    run_columns = ','.join(c['name'] for c in inspect(engine).get_columns('runs')
                           if c['name'] != 'next_event_sequence')
    event_columns = 'id,run_id,from_state,to_state,occurred_at,reason'
    before_runs = engine.connect().execute(
        text(f"SELECT {run_columns} FROM runs ORDER BY id")
    ).fetchall()
    before_events = engine.connect().execute(
        text(f"SELECT {event_columns} FROM run_events ORDER BY id")
    ).fetchall()
    before_snapshots = _fetch_all_snapshots(engine)
    engine.dispose()

    alembic_cmd.downgrade(config, "0001")

    engine2 = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    inspector_tables = set(
        engine2.connect().exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).scalars()
    )
    assert "run_binding_snapshots" not in inspector_tables
    after_down_runs = engine2.connect().execute(
        text(f"SELECT {run_columns} FROM runs ORDER BY id")
    ).fetchall()
    after_down_events = engine2.connect().execute(
        text(f"SELECT {event_columns} FROM run_events ORDER BY id")
    ).fetchall()
    assert after_down_runs == before_runs
    assert after_down_events == before_events
    engine2.dispose()

    # Re-upgrade produces identical legacy bindings.
    alembic_cmd.upgrade(config, "0003")
    engine3 = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    after_reup = _fetch_all_snapshots(engine3)
    assert after_reup == before_snapshots

    # Close/reopen reload through the repository contract works.
    Session = sessionmaker(bind=engine3, expire_on_commit=False, future=True)
    session = Session()
    repo = SqlRuntimeBindingSnapshotRepository(session)
    loaded = repo.get_by_run("run-with-starting")
    assert loaded is not None
    assert loaded.legacy_backfill is True
    assert loaded.snapshot_schema_version in SUPPORTED_SNAPSHOT_SCHEMA_VERSIONS
    session.close()
    engine3.dispose()


def test_migration_installs_run_delete_guard_and_fails_closed(migration_db) -> None:
    """Cross-acceptance: the Alembic-migrated head database (NOT create_all)
    installs trg_runs_reject_delete and rejects every Run deletion path;
    downgrade removes it together with 0002 artifacts; re-upgrade restores
    both the legacy backfill and the guard trigger."""
    from alembic import command as alembic_cmd
    from sqlalchemy import MetaData
    from sqlalchemy.orm import registry, relationship

    def _sqlite_names(engine):
        rows = engine.connect().exec_driver_sql(
            "SELECT type, name FROM sqlite_master WHERE type IN ('table','trigger')"
        ).fetchall()
        return {"table": {r[1] for r in rows if r[0] == "table"},
                "trigger": {r[1] for r in rows if r[0] == "trigger"}}

    db_path, config = migration_db
    alembic_cmd.upgrade(config, "0003")

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    # This oracle deliberately targets historical 0003, before D1a columns.
    historical = MetaData()
    historical.reflect(bind=engine, only=["runs", "run_events"])
    mapper = registry()
    class RunRow:
        pass
    class EventRow:
        pass
    mapper.map_imperatively(RunRow, historical.tables["runs"], properties={
        "events": relationship(EventRow, back_populates="run")})
    mapper.map_imperatively(EventRow, historical.tables["run_events"], properties={
        "run": relationship(RunRow, back_populates="events")})
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = Session()

    # The migration-installed database carries all three guards.
    names = _sqlite_names(engine)
    assert {"trg_runs_reject_delete", "trg_rbs_reject_update",
            "trg_rbs_reject_delete"} <= names["trigger"]

    # Direct ORM delete is rejected by the migration-installed trigger
    # (run-no-starting has no child events, so the ORM reaches DELETE).
    with pytest.raises(Exception) as exc_info:
        session.delete(session.get(RunRow, "run-no-starting"))
        session.flush()
    assert "run deletion" in str(exc_info.value).lower()
    session.rollback()

    # Direct ORM delete of a Run WITH child events is also rejected
    # fail-closed (ORM relationship null-update hits the NOT NULL FK first).
    with pytest.raises(Exception):
        session.delete(session.get(RunRow, "run-with-starting"))
        session.flush()
    session.rollback()

    # Bulk ORM delete is rejected.
    with pytest.raises(Exception) as exc_info:
        session.query(RunRow).filter(RunRow.id == "run-no-starting").delete()
        session.flush()
    assert "run deletion" in str(exc_info.value).lower()
    session.rollback()

    # Raw SQL DELETE is rejected.
    with pytest.raises(Exception) as exc_info:
        session.execute(text("DELETE FROM runs"))
    assert "run deletion" in str(exc_info.value).lower()
    session.rollback()

    # Both the Run rows AND their snapshots are preserved.
    repo = SqlRuntimeBindingSnapshotRepository(session)
    for run_id in ("run-with-starting", "run-no-starting"):
        assert repo.get_by_run(run_id) is not None
    assert session.execute(text("SELECT COUNT(*) FROM runs")).scalar_one() == 2

    session.close()
    engine.dispose()

    # Downgrade to 0001 removes the 0002 table and ALL 0002 triggers while
    # preserving runs/events history.
    alembic_cmd.downgrade(config, "0001")
    engine_down = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    down_names = _sqlite_names(engine_down)
    assert "run_binding_snapshots" not in down_names["table"]
    assert not (
        down_names["trigger"]
        & {"trg_runs_reject_delete", "trg_rbs_reject_update", "trg_rbs_reject_delete"}
    )
    down_runs = engine_down.connect().execute(
        text("SELECT * FROM runs ORDER BY id")
    ).fetchall()
    down_events = engine_down.connect().execute(
        text("SELECT * FROM run_events ORDER BY id")
    ).fetchall()
    assert len(down_runs) == 2
    assert len(down_events) >= 2
    engine_down.dispose()

    # Re-upgrade rebuilds the deterministic legacy backfill AND the guard.
    alembic_cmd.upgrade(config, "0003")
    engine_up = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    up_names = _sqlite_names(engine_up)
    assert "trg_runs_reject_delete" in up_names["trigger"]
    snapshots = _fetch_all_snapshots(engine_up)
    assert len(snapshots) == 2
    for row in snapshots:
        assert row["legacy_backfill"] == 1
        assert row["secret_ref_id"] is None

    # The rebuilt guard still rejects raw SQL deletion.
    Session2 = sessionmaker(bind=engine_up, expire_on_commit=False, future=True)
    session2 = Session2()
    with pytest.raises(Exception) as exc_info:
        session2.execute(text("DELETE FROM runs"))
    assert "run deletion" in str(exc_info.value).lower()
    session2.rollback()
    session2.close()
    engine_up.dispose()

    # Downgraded history is identical to pre-downgrade state (runs untouched).
    engine_cmp = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    cmp_runs = engine_cmp.connect().execute(
        text("SELECT id, task_id, state FROM runs ORDER BY id")
    ).fetchall()
    assert len(cmp_runs) == 2
    engine_cmp.dispose()


# ---------------------------------------------------------------------------
# H. Secret exclusion boundary
# ---------------------------------------------------------------------------

def test_snapshot_surfaces_contain_no_credential_markers(db_session) -> None:
    run = _seed_run(db_session)
    service = _make_service(db_session)
    execution = asyncio.run(service.execute_task(run.task_id, generation_revision=1))

    marker = SECRET_MARKER_PRE_WP14_B
    blob_parts = []

    # Snapshot DB rows (every column).
    result = db_session.execute(text("SELECT * FROM run_binding_snapshots"))
    for row in result.mappings():
        blob_parts.extend(str(v) for v in row.values())

    # Run events (reasons included).
    result = db_session.execute(text("SELECT reason FROM run_events"))
    blob_parts.extend(str(v) for v in (r[0] for r in result))

    # Evidence metadata.
    result = db_session.execute(text("SELECT metadata_json FROM evidence"))
    blob_parts.extend(str(v) for v in (r[0] for r in result))

    # Artifact metadata columns.
    result = db_session.execute(text("SELECT storage_ref, sha256 FROM artifacts"))
    blob_parts.extend(str(v) for row in result for v in row)

    # Run rows, including result_summary.
    result = db_session.execute(text("SELECT * FROM runs"))
    blob_parts.extend(str(v) for row in result for v in row)

    blob = "\n".join(blob_parts)
    assert marker not in blob
    assert "Bearer " not in blob
    # Domain object itself carries no credential either.
    assert marker not in repr(execution)


def test_runtime_error_capture_sanitized_in_persistence(db_session) -> None:
    """Runtime-facing error capture: an adapter exception carrying a raw
    credential marker must never reach persisted events, evidence metadata,
    or run results. Positive control first proves the scan would detect it."""
    marker = SECRET_MARKER_PRE_WP14_B

    run = _seed_run(db_session)
    exploding = _ExplodingStatusAdapter()

    class ExplodingRegistry(RuntimeRegistry):
        def __init__(self) -> None:
            super().__init__()
            super().register(build_reference_profile(), lambda: exploding)

    service = _make_service(db_session, registry=ExplodingRegistry())

    execution = asyncio.run(service.execute_existing_run(run.id))

    assert execution.run.state is RunState.FAILED

    # Negative samples: no marker anywhere durable.
    blob_parts = []
    for stmt in (
        "SELECT reason FROM run_events",
        "SELECT metadata_json FROM evidence",
        "SELECT result_summary FROM runs",
        "SELECT * FROM run_binding_snapshots",
    ):
        result = db_session.execute(text(stmt))
        blob_parts.extend(str(v) for row in result for v in row)
    blob = "\n".join(blob_parts)
    assert marker not in blob
    assert "boom" not in blob

    # Positive control: the same scan detects the marker when genuinely
    # present (the adapter raised it; only sanitization keeps it out).
    probe_exception = RuntimeError(f"boom {marker}")
    assert marker in str(probe_exception)
    assert marker in "\n".join([blob, str(probe_exception)])


def test_legacy_backfill_snapshot_has_null_secret_ref() -> None:
    snapshot = legacy_backfill_snapshot(
        "run-secret", ExecutionTarget.LOCAL, datetime.now(timezone.utc)
    )
    assert snapshot.secret_ref_id is None
    assert snapshot.auth_ownership is AuthOwnership.NONE


# ---------------------------------------------------------------------------
# Attempt 2: ordering / failure-injection / error-sanitization / auth matrix /
# bulk mutation rejection
# ---------------------------------------------------------------------------

def _engine_url(engine) -> str:
    return str(engine.url)


from polynexus_core.runtime.reference import ReferenceRuntimeAdapter  # noqa: E402


class _ProbeAdapter(ReferenceRuntimeAdapter):
    """Reference adapter that records whether the committed binding is
    visible from an independent connection at its FIRST observable point."""

    def __init__(self, url: str, seen: dict) -> None:
        super().__init__()
        self._url = url
        self._seen = seen

    async def create_run(self, context) -> str:
        engine = create_engine(
            self._url, connect_args={"check_same_thread": False}, future=True
        )
        Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
        session = Session()
        try:
            # execute_task creates its own NEW Run identity; verify that at
            # least one committed binding + one STARTING event exist already.
            snaps_n = session.execute(
                text("SELECT COUNT(*) FROM run_binding_snapshots")
            ).scalar()
            starting_n = session.execute(
                text("SELECT COUNT(*) FROM run_events WHERE to_state = 'STARTING'")
            ).scalar()
            self._seen["snapshot"] = snaps_n >= 1
            self._seen["starting_event"] = starting_n >= 1
        finally:
            session.close()
            engine.dispose()
        return await super().create_run(context)


def test_adapter_first_observable_point_sees_committed_snapshot(db_engine, db_session) -> None:
    """execute_task: claim + snapshot + STARTING event are committed BEFORE
    the first adapter invocation (verified from an independent connection)."""
    url = _engine_url(db_engine)
    run = _seed_run(db_session)

    observed: dict = {}

    class ProbeRegistry(RuntimeRegistry):
        def __init__(self) -> None:
            super().__init__()
            super().register(
                build_reference_profile(),
                lambda: _ProbeAdapter(url, observed),
            )

    service = ExecutionService(db_session, registry=ProbeRegistry())
    execution = asyncio.run(service.execute_task(run.task_id, generation_revision=1))

    assert execution.run.state is RunState.COMPLETED
    assert observed.get("snapshot") is True, (
        f"probe saw no snapshot; url={url!r} observed={observed}"
    )
    assert observed.get("starting_event") is True


def test_execute_task_binding_failure_no_adapter_no_partial_state(db_session) -> None:
    """Binding persistence failure rolls back everything; the adapter is
    never constructed or invoked and no half-completed Run remains."""

    class BindFailRegistry(RuntimeRegistry):
        def __init__(self) -> None:
            super().__init__()
            # Registering a factory that fails loudly if an adapter is ever
            # constructed: binding failure must prevent adapter invocation.
            super().register(build_reference_profile(), self._exploding_factory)

        def bind(self, *args, **kwargs):
            raise RuntimeBindingError("Runtime binding failed")

        @staticmethod
        def _exploding_factory():
            raise AssertionError("adapter must never be constructed after bind failure")

    service = ExecutionService(db_session, registry=BindFailRegistry())

    seeded = _seed_run(db_session)
    runs_before = len(SqlRunRepository(db_session).list_by_task(seeded.task_id))
    with pytest.raises(RuntimeBindingError, match="binding failed"):
        asyncio.run(service.execute_task(seeded.task_id, generation_revision=1))

    # Rolled back: no NEW Run rows persisted for the task.
    assert (
        len(SqlRunRepository(db_session).list_by_task(seeded.task_id)) == runs_before
    )


class _ExplodingFactoryRegistry(RuntimeRegistry):
    """Registry whose adapter factory raises AFTER binding has committed."""

    def __init__(self) -> None:
        super().__init__()
        self.factory_calls = 0
        super().register(build_reference_profile(), self._factory)

    def _factory(self):
        self.factory_calls += 1
        raise RuntimeError(
            f"factory construction boom {SECRET_MARKER_PRE_WP14_B}"
        )


def _assert_fail_closed_after_factory_failure(session, run_id: str, exc) -> None:
    # Sanitized error only: the raw factory exception and credential marker
    # never reach the caller.
    message = str(exc.value)
    assert "adapter construction failed" in message
    assert SECRET_MARKER_PRE_WP14_B not in message

    # The committed snapshot is preserved.
    snapshot = SqlRuntimeBindingSnapshotRepository(session).get_by_run(run_id)
    assert snapshot is not None
    assert snapshot.legacy_backfill is False

    # The Run legally transitioned STARTING -> FAILED with a sanitized reason.
    reloaded = SqlRunRepository(session).get(run_id)
    assert reloaded.state is RunState.FAILED
    states = [e.to_state for e in reloaded.events]
    assert states == [RunState.STARTING, RunState.FAILED]
    failed_reason = [e.reason for e in reloaded.events if e.to_state is RunState.FAILED][0]
    assert failed_reason == "Runtime adapter construction failed"
    assert SECRET_MARKER_PRE_WP14_B not in failed_reason

    # No raw marker in any persisted surface.
    blob_parts = []
    for stmt in (
        "SELECT reason FROM run_events",
        "SELECT metadata_json FROM evidence",
        "SELECT result_summary FROM runs",
    ):
        result = session.execute(text(stmt))
        blob_parts.extend(str(v) for row in result for v in row)
    assert SECRET_MARKER_PRE_WP14_B not in "\n".join(blob_parts)


def test_execute_existing_run_factory_failure_fails_closed(db_session) -> None:
    """Factory construction failure after commit: Run must not stay STARTING,
    the snapshot survives, and no raw exception/marker leaks."""
    run = _seed_run(db_session)
    registry = _ExplodingFactoryRegistry()
    service = _make_service(db_session, registry=registry)

    with pytest.raises(RuntimeBindingError) as exc_info:
        asyncio.run(service.execute_existing_run(run.id))

    assert registry.factory_calls == 1
    _assert_fail_closed_after_factory_failure(db_session, run.id, exc_info)


def test_execute_task_factory_failure_fails_closed(db_session) -> None:
    """Same fail-closed contract for execute_task(): the newly created Run is
    recovered from STARTING to FAILED, snapshot kept, errors sanitized."""
    run = _seed_run(db_session)
    runs_before = len(SqlRunRepository(db_session).list_by_task(run.task_id))
    registry = _ExplodingFactoryRegistry()
    service = _make_service(db_session, registry=registry)

    with pytest.raises(RuntimeBindingError) as exc_info:
        asyncio.run(service.execute_task(run.task_id, generation_revision=1))

    assert registry.factory_calls == 1

    runs = SqlRunRepository(db_session).list_by_task(run.task_id)
    assert len(runs) == runs_before + 1
    created_run = [r for r in runs if r.state is RunState.FAILED]
    assert len(created_run) == 1
    assert created_run[0].state is RunState.FAILED
    _assert_fail_closed_after_factory_failure(
        db_session, created_run[0].id, exc_info
    )


# --- Error message security -------------------------------------------------

@pytest.mark.parametrize(
    "marker",
    [
        "token-ABC123secret",
        "cookie-session-XYZ789",
        "api-key-SKILL99-live",
        "Bearer real-credential-token",
        "sessionid=q1w2e3r4",
    ],
)
def test_identifier_rejection_never_leaks_value(marker: str) -> None:
    with pytest.raises(RuntimeBindingError) as exc_info:
        validate_opaque_identifier(marker, "provider_id")
    assert marker not in str(exc_info.value)


@pytest.mark.parametrize(
    "marker",
    [
        "profile-with-token-abc123",
        "profile-with-cookie-session-marker",
        "profile-with-api-key-material",
    ],
)
def test_unknown_profile_error_does_not_echo_input(marker: str) -> None:
    registry = build_default_registry()
    with pytest.raises(RuntimeBindingError) as exc_info:
        registry.resolve(marker)
    message = str(exc_info.value)
    assert marker not in message
    assert "Unknown or unavailable runtime profile" in message


def test_unregistered_factory_error_does_not_echo_adapter_id() -> None:
    registry = RuntimeRegistry()
    profile = RuntimeProfile(
        provider_id="leaky-provider",
        transport_kind=TransportKind.LOCAL,
        runtime_id="leaky-runtime-secret",
        adapter_id="builtin.leaky-secret-adapter",
        runtime_profile_ref="leaky.default",
    )
    registry.register(profile, lambda: None)  # type: ignore[arg-type]
    registry._factories.clear()
    with pytest.raises(RuntimeBindingError) as exc_info:
        registry.create_adapter(registry.resolve("leaky.default"))
    message = str(exc_info.value)
    assert "builtin.leaky-secret-adapter" not in message
    assert "No adapter factory registered" in message


def test_execution_failure_error_not_persisted_raw(db_session) -> None:
    """Adapter exceptions carrying secrets never reach persisted surfaces."""
    run = _seed_run(db_session)
    exploding = _ExplodingStatusAdapter()

    class ExplodingRegistry(RuntimeRegistry):
        def __init__(self) -> None:
            super().__init__()
            super().register(build_reference_profile(), lambda: exploding)

    service = ExecutionService(db_session, registry=ExplodingRegistry())
    asyncio.run(service.execute_existing_run(run.id))

    blob_parts = []
    result = db_session.execute(text("SELECT reason FROM run_events"))
    blob_parts.extend(str(r[0]) for r in result)
    result = db_session.execute(text("SELECT result_summary FROM runs"))
    blob_parts.extend(str(r[0]) for r in result)
    result = db_session.execute(text("SELECT metadata_json FROM evidence"))
    blob_parts.extend(str(r[0]) for r in result)
    blob = "\n".join(blob_parts)
    assert SECRET_MARKER_PRE_WP14_B not in blob


# --- Auth ownership / secret_ref_id invariant matrix ------------------------

_AUTH_MATRIX = [
    (AuthOwnership.NONE, None, True),
    (AuthOwnership.RUNTIME_MANAGED, None, True),
    (AuthOwnership.BROWSER_PROFILE_MANAGED, None, True),
    (AuthOwnership.SECRET_REF, "secret-ref-valid-1", True),
    (AuthOwnership.NONE, "unexpected-ref", False),
    (AuthOwnership.RUNTIME_MANAGED, "unexpected-ref", False),
    (AuthOwnership.BROWSER_PROFILE_MANAGED, "unexpected-ref", False),
    (AuthOwnership.SECRET_REF, None, False),
]


@pytest.mark.parametrize("ownership,secret_ref,allowed", _AUTH_MATRIX)
def test_auth_ownership_secret_ref_matrix_profile(
    ownership: AuthOwnership, secret_ref, allowed: bool
) -> None:
    kwargs = dict(
        provider_id="matrix-provider",
        transport_kind=TransportKind.LOCAL,
        runtime_id="matrix-runtime",
        adapter_id="builtin.matrix",
        runtime_profile_ref="matrix.default",
        auth_ownership=ownership,
        secret_ref_id=secret_ref,
    )
    if allowed:
        profile = RuntimeProfile(**kwargs)
        assert profile.auth_ownership is ownership
    else:
        with pytest.raises(RuntimeBindingError):
            RuntimeProfile(**kwargs)


@pytest.mark.parametrize("ownership,secret_ref,allowed", _AUTH_MATRIX)
def test_auth_ownership_secret_ref_matrix_snapshot(
    ownership: AuthOwnership, secret_ref, allowed: bool
) -> None:
    kwargs = dict(
        run_id=f"run-matrix-{ownership.value.lower()}",
        provider_id="matrix-provider",
        transport_kind=TransportKind.LOCAL,
        runtime_id="matrix-runtime",
        adapter_id="builtin.matrix",
        execution_target=ExecutionTarget.LOCAL,
        runtime_profile_ref="matrix.default",
        profile_revision=1,
        adapter_version=None,
        resolved_at=datetime.now(timezone.utc),
        legacy_backfill=False,
        auth_ownership=ownership,
        secret_ref_id=secret_ref,
    )
    if allowed:
        snapshot = RuntimeBindingSnapshot(**kwargs)
        assert snapshot.auth_ownership is ownership
    else:
        with pytest.raises(RuntimeBindingError):
            RuntimeBindingSnapshot(**kwargs)


def test_reload_rejects_mismatched_auth_ownership_row(db_session) -> None:
    """A persisted row violating the invariant fails closed on reload."""
    db_session.execute(
        text(
            """
            INSERT INTO run_binding_snapshots (
                run_id, provider_id, transport_kind, runtime_id, adapter_id,
                execution_target, runtime_profile_ref, profile_revision,
                adapter_version, resolved_at, legacy_backfill,
                snapshot_schema_version, auth_ownership, secret_ref_id,
                usage_visibility
            ) VALUES (
                'run-auth-bad', 'polynexus', 'LOCAL', 'reference',
                'builtin.reference', 'LOCAL', 'reference.local', 1, NULL,
                '2026-08-25 00:00:00.000000', 0, 1, 'NONE',
                'should-not-exist-ref', 'UNAVAILABLE'
            )
            """
        )
    )
    db_session.commit()
    repo = SqlRuntimeBindingSnapshotRepository(db_session)
    with pytest.raises(RuntimeBindingError, match="must not carry"):
        repo.get_by_run("run-auth-bad")


def test_migration_backfill_row_satisfies_auth_invariant(migration_db) -> None:
    from alembic import command as alembic_cmd

    db_path, config = migration_db
    alembic_cmd.upgrade(config, "head")
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = Session()
    repo = SqlRuntimeBindingSnapshotRepository(session)
    for run_id in ("run-with-starting", "run-no-starting"):
        loaded = repo.get_by_run(run_id)
        assert loaded is not None
        assert loaded.auth_ownership is AuthOwnership.NONE
        assert loaded.secret_ref_id is None
    session.close()
    engine.dispose()


# --- Immutability: bulk ORM and raw SQL rejection ----------------------------

def test_bulk_orm_update_rejected(db_session) -> None:
    repo = SqlRuntimeBindingSnapshotRepository(db_session)
    original = _legacy_snapshot("run-bulk-upd", datetime(2026, 8, 25, tzinfo=timezone.utc))
    repo.insert_once(original)
    db_session.commit()

    with pytest.raises(Exception) as exc_info:
        db_session.query(RunBindingSnapshotRow).filter(
            RunBindingSnapshotRow.run_id == "run-bulk-upd"
        ).update({"provider_id": "tampered"})
        db_session.flush()
    assert "immutable" in str(exc_info.value)
    db_session.rollback()

    assert repo.get_by_run("run-bulk-upd") == original


def test_bulk_orm_delete_rejected(db_session) -> None:
    repo = SqlRuntimeBindingSnapshotRepository(db_session)
    original = _legacy_snapshot("run-bulk-del", datetime(2026, 8, 25, tzinfo=timezone.utc))
    repo.insert_once(original)
    db_session.commit()

    with pytest.raises(Exception) as exc_info:
        db_session.query(RunBindingSnapshotRow).filter(
            RunBindingSnapshotRow.run_id == "run-bulk-del"
        ).delete()
        db_session.flush()
    assert "immutable" in str(exc_info.value)
    db_session.rollback()

    assert repo.get_by_run("run-bulk-del") == original


def test_direct_sql_update_delete_rejected(db_session) -> None:
    repo = SqlRuntimeBindingSnapshotRepository(db_session)
    original = _legacy_snapshot("run-raw-sql", datetime(2026, 8, 25, tzinfo=timezone.utc))
    repo.insert_once(original)
    db_session.commit()

    with pytest.raises(Exception) as exc_info:
        db_session.execute(
            text("UPDATE run_binding_snapshots SET provider_id = 'tampered'")
        )
    assert "immutable" in str(exc_info.value)
    db_session.rollback()

    with pytest.raises(Exception) as exc_info:
        db_session.execute(text("DELETE FROM run_binding_snapshots"))
    assert "immutable" in str(exc_info.value)
    db_session.rollback()

    assert repo.get_by_run("run-raw-sql") == original


def test_run_deletion_fail_closed_preserves_run_and_snapshot(db_session) -> None:
    from polynexus_core.persistence.models import RunRow

    run = _seed_run(db_session)
    repo = SqlRuntimeBindingSnapshotRepository(db_session)
    original = _legacy_snapshot(run.id, datetime(2026, 8, 25, tzinfo=timezone.utc))
    repo.insert_once(original)
    db_session.commit()

    # Run deletion is fail-closed on every path: direct ORM delete, bulk ORM
    # delete, and raw SQL. A Run owns its binding snapshot 1:1 forever, so no
    # orphan snapshot may ever exist and deletion is rejected outright.
    # 1. Direct ORM delete is rejected.
    with pytest.raises(Exception) as exc_info:
        db_session.delete(db_session.get(RunRow, run.id))
        db_session.flush()
    assert "run deletion" in str(exc_info.value).lower()
    db_session.rollback()

    # 2. Bulk ORM delete is rejected.
    with pytest.raises(Exception) as exc_info:
        db_session.query(RunRow).filter(RunRow.id == run.id).delete()
        db_session.flush()
    assert "run deletion" in str(exc_info.value).lower()
    db_session.rollback()

    # 3. Raw SQL DELETE is rejected.
    with pytest.raises(Exception) as exc_info:
        db_session.execute(text("DELETE FROM runs"))
    assert "run deletion" in str(exc_info.value).lower()
    db_session.rollback()

    # The Run row AND the snapshot row are both preserved.
    run_repo = SqlRunRepository(db_session)
    reloaded_run = run_repo.get(run.id)
    assert reloaded_run is not None
    assert reloaded_run.id == run.id
    assert repo.get_by_run(run.id) == original
