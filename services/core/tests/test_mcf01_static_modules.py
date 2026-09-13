"""MCF-01 deterministic contracts, fail-closed composition and real Core path."""
from __future__ import annotations

import asyncio
import traceback
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import datetime, timezone

from d1a_fixtures import d1a_content_environment,prepare_generation,migrate_fixture_engine
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from polynexus_core.domain.enums import AuthOwnership, RunState, TransportKind
from polynexus_core.domain.models import ContextPackage, Project, Run, Task
from polynexus_core.domain.runtime_binding import RuntimeBindingError, RuntimeProfile
from polynexus_core.execution_service import ExecutionService
from polynexus_core.extensions import (
    ConformanceScope, HealthBoundary, ModuleError, ModuleManifest, ModuleRegistry,
    ModuleType, RuntimeModuleBridge,
)
from polynexus_core.persistence.models import Base
from polynexus_core.persistence.repository import (
    SqlContextPackageRepository, SqlProjectRepository, SqlRunRepository,
    SqlRuntimeBindingSnapshotRepository, SqlTaskRepository,
)
from polynexus_core.runtime.codex import CodexRuntimeAdapter
from polynexus_core.runtime.contracts import RuntimeCapabilities
from polynexus_core.runtime.opencode import OpenCodeRuntimeAdapter
from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
from polynexus_core.runtime.registry import RuntimeRegistry, RUNTIME_PROFILE_ENV

MARKER = "Bearer SYNTHETIC_MCF01_COOKIE_TOKEN"


def manifest(key="reference", **changes):
    fields = dict(
        module_id=f"module.{key}", module_type=ModuleType.RUNTIME,
        module_version="1.0.0", capabilities=("cancel", "artifacts", "timeout_cleanup_verified"),
        health=HealthBoundary.RUNTIME_PROBE,
        conformance_scope=ConformanceScope.DETERMINISTIC_LOCAL_CONFORMANCE,
    )
    fields.update(changes)
    return ModuleManifest(**fields)


def profile(key="reference", **changes):
    fields = dict(provider_id="polynexus", transport_kind=TransportKind.LOCAL,
                  runtime_id=key, adapter_id=f"builtin.{key}", runtime_profile_ref=f"{key}.local")
    fields.update(changes)
    return RuntimeProfile(**fields)


def bridge():
    return RuntimeModuleBridge(ModuleRegistry(), RuntimeRegistry())


@pytest.mark.parametrize("changes", [
    {"contract_version": 2}, {"contract_version": True}, {"contract_version": "1"},
    {"module_id": "bad/id"}, {"module_id": "name\n"}, {"module_id": "x" * 65},
    {"module_id": MARKER}, {"module_type": "UNKNOWN"}, {"module_type": "MEMORY"},
    {"capabilities": "cancel"}, {"capabilities": ("not valid",)},
    {"capabilities": ({"token": MARKER},)}, {"module_version": MARKER},
    {"config": {"api_key": MARKER}}, {"config": MARKER}, {"provider_id": MARKER},
    {"maturity": "SUPPORTED"}, {"conformance_scope": "PASS"},
    {"security": MARKER}, {"lifecycle": MARKER},
])
def test_invalid_manifest_rejects_without_echo(changes):
    with pytest.raises(ModuleError) as caught:
        manifest(**changes)
    assert MARKER not in str(caught.value)


def test_manifest_normalization_immutability_and_no_arbitrary_config():
    caps = ["cancel", "artifacts", "cancel"]
    value = manifest(capabilities=caps)
    caps.append("resume")
    assert value.capabilities == ("artifacts", "cancel")
    with pytest.raises(FrozenInstanceError):
        value.module_version = "2.0.0"
    with pytest.raises(TypeError):
        ModuleManifest("module.fixture", ModuleType.TOOL, "1.0.0", api_key=MARKER)
    assert MARKER not in repr(asdict(value))


@pytest.mark.parametrize("kind", list(ModuleType))
def test_descriptor_vocabulary_has_no_memory_or_implicit_execution(kind):
    item = ModuleManifest("module.fixture", kind, "1.0.0")
    registry = ModuleRegistry()
    registry.register(item)
    registry.register(item)
    assert registry.resolve(item.module_id) == item
    assert "MEMORY" not in ModuleType.__members__
    if kind is not ModuleType.RUNTIME:
        with pytest.raises(ModuleError):
            RuntimeModuleBridge(ModuleRegistry(), RuntimeRegistry()).register(item, ((profile(), ReferenceRuntimeAdapter),))


def test_conflicting_manifest_and_unknown_capability_fail_closed():
    modules = ModuleRegistry()
    item = manifest()
    modules.register(item)
    with pytest.raises(ModuleError, match="Conflicting module registration"):
        modules.register(replace(item, module_version="2.0.0"))
    with pytest.raises(ModuleError, match="unavailable"):
        modules.resolve(item.module_id, required_capabilities=("resume",))
    with pytest.raises(ModuleError, match="Unknown or disabled"):
        modules.resolve("unknown.module")
    assert modules.resolve(item.module_id) == item


def test_registration_is_lazy_and_disable_blocks_direct_registry_creation():
    b = bridge()
    calls = []
    def factory():
        calls.append(1)
        return ReferenceRuntimeAdapter()
    b.register(manifest(), ((profile(), factory),))
    assert calls == []
    snapshot = b.runtimes.bind("reference.local", "run-1", datetime.now(timezone.utc))
    b.modules.set_enabled("module.reference", False)
    with pytest.raises(ModuleError, match="Unknown or disabled"):
        b.runtimes.create_adapter(b.runtimes.resolve("reference.local"))
    assert calls == []
    b.modules.set_enabled("module.reference", True)
    assert isinstance(b.runtimes.create_adapter(b.runtimes.resolve("reference.local")), ReferenceRuntimeAdapter)
    assert snapshot.runtime_id == "reference"
    with pytest.raises(FrozenInstanceError):
        snapshot.runtime_id = "other"


def test_batch_profile_conflict_is_atomic():
    b = bridge()
    original = profile("occupied")
    b.runtimes.register(original, ReferenceRuntimeAdapter)
    with pytest.raises(RuntimeBindingError, match="Conflicting profile registration"):
        b.register(manifest(), (
            (profile("new"), ReferenceRuntimeAdapter),
            (replace(original, runtime_id="conflict"), ReferenceRuntimeAdapter),
        ))
    assert not b.modules.contains("module.reference")
    with pytest.raises(RuntimeBindingError):
        b.runtimes.resolve("new.local")
    assert b.runtimes.resolve("occupied.local") == original
    assert isinstance(b.runtimes.create_adapter(original), ReferenceRuntimeAdapter)


def test_batch_factory_conflict_is_atomic_and_original_remains_available():
    b = bridge()
    b.runtimes.register(profile(), ReferenceRuntimeAdapter)
    with pytest.raises(RuntimeBindingError, match="Conflicting adapter factory"):
        b.register(manifest(), ((profile("new"), ReferenceRuntimeAdapter), (profile(), lambda: ReferenceRuntimeAdapter())))
    assert not b.modules.contains("module.reference")
    with pytest.raises(RuntimeBindingError):
        b.runtimes.resolve("new.local")
    assert isinstance(b.runtimes.create_adapter(profile()), ReferenceRuntimeAdapter)


def test_multiple_profiles_share_one_factory_within_module():
    b = bridge()
    first = profile()
    second = replace(first, runtime_profile_ref="reference.other", profile_revision=2)
    b.register(manifest(), ((first, ReferenceRuntimeAdapter), (second, ReferenceRuntimeAdapter)))
    assert b.runtimes.resolve("reference.other") == second
    assert isinstance(b.runtimes.create_adapter(second), ReferenceRuntimeAdapter)
    with pytest.raises(ModuleError, match="already registered"):
        b.register(manifest(), ((first, ReferenceRuntimeAdapter),))


@pytest.mark.parametrize("registration", [(), ((profile(), None),), ((None, ReferenceRuntimeAdapter),)])
def test_unavailable_factory_and_empty_registration_rejected(registration):
    b = bridge()
    with pytest.raises(ModuleError):
        b.register(manifest(), registration)
    assert not b.modules.contains("module.reference")


def test_missing_factory_in_existing_registry_rejects():
    with pytest.raises(RuntimeBindingError, match="No adapter factory"):
        RuntimeRegistry().create_adapter(profile())


def test_unknown_resolution_and_invalid_runtime_capability_rejected():
    b = bridge()
    with pytest.raises(ModuleError, match="capability"):
        b.register(manifest(capabilities=("unknown",)), ((profile(), ReferenceRuntimeAdapter),))
    with pytest.raises(RuntimeBindingError):
        b.runtimes.bind("missing.local", "run-1", datetime.now(timezone.utc))
    assert not b.modules.contains("module.reference")


@pytest.mark.parametrize("caps", [RuntimeCapabilities(cancel="yes"), RuntimeCapabilities(resume="NATIVE"), object()])
def test_malformed_adapter_capabilities_rejected(caps):
    class Invalid(ReferenceRuntimeAdapter):
        def capabilities(self):
            return caps
    b = bridge()
    b.register(manifest(), ((profile(), Invalid),))
    with pytest.raises(ModuleError, match="factory or capability"):
        b.runtimes.create_adapter(b.runtimes.resolve("reference.local"))


def test_false_capability_claim_and_auth_mismatch_rejected():
    b = bridge()
    b.register(manifest(capabilities=("resume",)), ((profile(), ReferenceRuntimeAdapter),))
    with pytest.raises(ModuleError):
        b.runtimes.create_adapter(profile())
    b2 = bridge()
    p = profile(auth_ownership=AuthOwnership.RUNTIME_MANAGED)
    b2.register(manifest(), ((p, ReferenceRuntimeAdapter),))
    with pytest.raises(RuntimeBindingError, match="authentication ownership"):
        b2.runtimes.create_adapter(p)


def test_profile_copy_and_later_mutation_fail_closed():
    b = bridge()
    original = profile()
    b.register(manifest(), ((original, ReferenceRuntimeAdapter),))
    original.runtime_id = "changed"
    assert b.runtimes.resolve("reference.local").runtime_id == "reference"
    b.runtimes.resolve("reference.local").runtime_id = "changed"
    with pytest.raises(ModuleError):
        b.runtimes.create_adapter(b.runtimes.resolve("reference.local"))


def test_probe_is_current_observation_with_module_ownership():
    b = bridge()
    b.register(manifest(), ((profile(), ReferenceRuntimeAdapter),))
    result = asyncio.run(b.probe("module.reference", "reference.local"))
    assert result.healthy is True and result.ready is True and result.error_category is None
    with pytest.raises(ModuleError, match="does not belong"):
        asyncio.run(b.probe("module.reference", "other.local"))


@pytest.mark.parametrize("mode,category", [("error", "PROBE_FAILURE"), ("timeout", "PROBE_TIMEOUT"), ("invalid", "INVALID_PROBE"), ("unhealthy", None)])
def test_probe_failures_are_bounded_and_sanitized(mode, category):
    cancelled = []
    class Probe(ReferenceRuntimeAdapter):
        async def health(self):
            if mode == "error":
                raise RuntimeError(MARKER)
            if mode == "invalid":
                return MARKER
            if mode == "unhealthy":
                return False
            try:
                await asyncio.sleep(10)
            finally:
                cancelled.append(True)
    b = bridge()
    b.register(manifest(), ((profile(), Probe),))
    result = asyncio.run(b.probe("module.reference", "reference.local", timeout=0.01))
    assert result.error_category == category
    assert MARKER not in repr(result)
    if mode == "timeout":
        assert cancelled == [True]
    if mode == "unhealthy":
        assert result.healthy is False and result.ready is True


def seed(session):
    project = Project(name="MCF01")
    context = ContextPackage(project_id=project.id, version=1, instructions=("fixture:mcf01",))
    task = Task(project_id=project.id, title="module proof", workflow_id="review-minimal", workflow_version=1, context_package_id=context.id)
    run = Run(task_id=task.id, workflow_id=task.workflow_id, workflow_version=1, context_package_id=context.id)
    for repo, entity in ((SqlProjectRepository, project), (SqlContextPackageRepository, context), (SqlTaskRepository, task)):
        repo(session).add(entity)
    run.generation_revision=prepare_generation(session,task.id)
    SqlRunRepository(session).add(run)
    session.commit()
    return run


@pytest.fixture
def engine(tmp_path):
    value = create_engine(f"sqlite:///{tmp_path / 'mcf01.db'}")
    migrate_fixture_engine(value)
    yield value
    value.dispose()


def test_three_modules_use_same_core_orchestration_and_durable_bindings(engine, monkeypatch):
    b = bridge()
    specs = (("reference", ReferenceRuntimeAdapter), ("codex", CodexRuntimeAdapter), ("opencode", OpenCodeRuntimeAdapter))
    observations = []
    for key, adapter_type in specs:
        def factory(key=key, adapter_type=adapter_type):
            # Independent connection proves the binding committed before factory invocation.
            with Session(engine) as other:
                binding = SqlRuntimeBindingSnapshotRepository(other).get_by_run(current_run_id)
                assert binding is not None and binding.runtime_id == key
            observations.append(adapter_type)
            return adapter_type()
        b.register(manifest(key), ((profile(key), factory),))
    run_ids = []
    with Session(engine) as session:
        service = ExecutionService(session, b.runtimes)
        for key, adapter_type in specs:
            run = seed(session)
            current_run_id = run.id
            run_ids.append(run.id)
            monkeypatch.setenv(RUNTIME_PROFILE_ENV, f"{key}.local")
            result = asyncio.run(service.execute_existing_run(run.id))
            assert result.run.id == run.id
            assert result.run.state is RunState.COMPLETED
            assert result.run.runtime_ref.startswith(f"{key}:")
            assert observations[-1] is adapter_type
    with Session(engine) as reloaded:
        snapshots = [SqlRuntimeBindingSnapshotRepository(reloaded).get_by_run(run_id) for run_id in run_ids]
        assert len({s.runtime_profile_ref for s in snapshots}) == 3
        assert len({s.adapter_id for s in snapshots}) == 3
        assert len({s.runtime_id for s in snapshots}) == 3
        b.modules.set_enabled("module.codex", False)
        assert SqlRuntimeBindingSnapshotRepository(reloaded).get_by_run(run_ids[1]) == snapshots[1]


@pytest.mark.parametrize("mode", ["factory", "execution", "disabled", "unknown"])
def test_failures_preserve_binding_without_fallback(engine, monkeypatch, mode):
    b = bridge()
    fallback_calls = []
    def fallback():
        fallback_calls.append(True)
        return ReferenceRuntimeAdapter()
    b.register(manifest(), ((profile(), fallback),))
    class Failure(CodexRuntimeAdapter):
        async def create_run(self, context):
            raise RuntimeError(MARKER)
    def failing_factory():
        if mode == "factory":
            raise RuntimeError(MARKER)
        return Failure()
    b.register(manifest("broken"), ((profile("broken"), failing_factory),))
    if mode == "disabled":
        b.modules.set_enabled("module.broken", False)
    monkeypatch.setenv(RUNTIME_PROFILE_ENV, "unknown.local" if mode == "unknown" else "broken.local")
    with Session(engine) as session:
        run = seed(session)
        service = ExecutionService(session, b.runtimes)
        if mode == "execution":
            result = asyncio.run(service.execute_existing_run(run.id))
            assert result.result is None and result.evidence == ()
        else:
            with pytest.raises(RuntimeBindingError) as caught:
                asyncio.run(service.execute_existing_run(run.id))
            assert MARKER not in "".join(traceback.format_exception(caught.value))
        stored = SqlRunRepository(session).get(run.id)
        binding = SqlRuntimeBindingSnapshotRepository(session).get_by_run(run.id)
        assert stored.state is (RunState.CREATED if mode == "unknown" else RunState.FAILED)
        if mode == "unknown":
            assert binding is None
        else:
            assert binding.runtime_id == "broken"
        assert MARKER not in repr(stored)
    assert fallback_calls == []
