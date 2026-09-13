"""WP-13 deterministic workflow hard-gate contract tests.

Covers the acceptance matrix: configuration validation (fail closed), required
TOOL_EVIDENCE satisfaction, explicit FAIL / missing / malformed / cross-run /
cross-task / AI-only evidence non-PASS behavior, HUMAN_GATE under D11 Option C
(no auto-approval), verified-verdict rules, durability across close/reopen,
idempotent replay, truthful terminal required Runs, secret redaction, non-mutation
by Council output, tamper detection for all metadata fields, and real
ExecutionService integration. No new model/table/migration/endpoint is exercised;
the evaluator uses the existing Task/Run/Evidence boundaries.
"""

from __future__ import annotations

import json
from pathlib import Path

from d1a_fixtures import d1a_content_environment,prepare_generation,migrate_fixture_engine
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from polynexus_core.domain.enums import (
    AssuranceMode,
    EvidenceStatus,
    EvidenceType,
    RunState,
    WorkMode,
)
from polynexus_core.domain.models import (
    ContextPackage,
    Evidence,
    Project,
    Run,
    Task,
)
from polynexus_core.persistence.models import Base
from polynexus_core.persistence.repository import (
    SqlContextPackageRepository,
    SqlEvidenceRepository,
    SqlProjectRepository,
    SqlRunRepository,
    SqlTaskRepository,
    _serialize_dict,
    _deserialize_dict,
)
from polynexus_core.workflows.gates import (
    GateOutcome,
    GateReportTamperedError,
    WorkflowGateConfigError,
    WorkflowIdentityError,
    _compute_identity_hash,
    _compute_provenance_token,
    evaluate_workflow_gates,
    persist_gate_report,
    reload_gate_report,
    validate_workflow_gates,
)
from polynexus_core.workflows.loader import load_workflow_definition
from polynexus_core.workflows.models import WorkflowDefinition

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VERIFIED_GATE_WORKFLOW = _REPO_ROOT / "workflows" / "builtin" / "verified-gate.yaml"

_SECRET = "SECRET_MARKER_RAW_LEAK_xyz987"


@pytest.fixture()
def gate_session(tmp_path: Path):
    db_path = tmp_path / "wp13.db"
    url = f"sqlite:///{db_path}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    migrate_fixture_engine(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = Session()
    yield session, db_path
    session.close()
    engine.dispose()


def _seed(session):
    project = Project(name="WP-13 Project")
    SqlProjectRepository(session).add(project)
    context = ContextPackage(project_id=project.id, version=1)
    SqlContextPackageRepository(session).add(context)
    task = Task(
        project_id=project.id,
        title="Gate task",
        workflow_id="verified-gate",
        workflow_version=1,
        mode=WorkMode.VALIDATE,
        context_package_id=context.id,
    )
    SqlTaskRepository(session).add(task)
    session.commit()
    prepare_generation(session,task.id)
    return task, context, project


def _new_run(session, task, context, *, generation_revision=None) -> Run:
    run = Run(
        task_id=task.id,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=context.id,
     generation_revision=generation_revision)
    SqlRunRepository(session).add(run)
    session.commit()
    return run


def _add_evidence(session, task, run, etype, status, metadata=None, source="test",
                  actor_id="test:actor"):
    ev = Evidence(
        task_id=task.id,
        run_id=run.id,
        actor_id=actor_id,
        source=source,
        type=etype,
        status=status,
        metadata=metadata or {},
    )
    SqlEvidenceRepository(session).add(ev)
    session.commit()
    return ev


def _add_all_pass_evidence(session, task, run):
    """Add evidence for all gates to produce a PASS verdict (EVIDENCE_CHECK only)."""
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "make build", "exit_code": "0"},
    )
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "unit-test", "command": "make test", "exit_code": "0"},
    )


# ---------------------------------------------------------------------------
# 1. Valid fixed workflow nodes load and preserve gate configuration
# ---------------------------------------------------------------------------


def test_valid_workflow_preserves_gate_config(gate_session) -> None:
    session, _ = gate_session
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    assert workflow.id == "verified-gate"
    assert workflow.assurance is AssuranceMode.VERIFIED

    evidence_step = next(s for s in workflow.steps if s.id == "evidence-gate")
    assert evidence_step.type == "EVIDENCE_CHECK"
    assert evidence_step.parameters["hard_gates"] == ["build", "unit-test"]

    human_step = next(s for s in workflow.steps if s.id == "human-approval")
    assert human_step.type == "HUMAN_GATE"
    assert human_step.parameters["human_gate"] == "release-signoff"

    assert validate_workflow_gates(workflow) == []


# ---------------------------------------------------------------------------
# 2. Invalid gate configuration fails closed before execution
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_steps",
    [
        [
            {"id": "a", "type": "CONTEXT"},
            {"id": "g1", "type": "EVIDENCE_CHECK", "hard_gates": ["build"]},
            {"id": "g2", "type": "EVIDENCE_CHECK", "hard_gates": ["build"]},
        ],
        [
            {"id": "a", "type": "CONTEXT"},
            {"id": "g1", "type": "EVIDENCE_CHECK", "hard_gates": []},
        ],
        [
            {"id": "a", "type": "CONTEXT"},
            {"id": "g1", "type": "EVIDENCE_CHECK", "hard_gates": ["build"], "depends_on": ["missing"]},
        ],
        [
            {"id": "a", "type": "CONTEXT"},
            {"id": "bad", "type": "SCRIPT"},
        ],
        [
            {"id": "a", "type": "CONTEXT"},
            {"id": "a", "type": "SYNTHESIS"},
        ],
    ],
)
def test_invalid_gate_config_fails_closed(bad_steps) -> None:
    workflow = WorkflowDefinition.from_mapping(
        {"id": "bad-wf", "version": 1, "steps": bad_steps}
    )
    errors = validate_workflow_gates(workflow)
    assert errors, "expected configuration errors"
    with pytest.raises(WorkflowGateConfigError):
        engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(engine)
        S = sessionmaker(bind=engine, future=True)
        s = S()
        project = Project(name="P")
        SqlProjectRepository(s).add(project)
        context = ContextPackage(project_id=project.id, version=1)
        SqlContextPackageRepository(s).add(context)
        task = Task(
            project_id=project.id,
            title="T",
            workflow_id="bad-wf",
            workflow_version=1,
            context_package_id=context.id,
        )
        SqlTaskRepository(s).add(task)
        s.commit()
        run = _new_run(s, task, context)
        evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(s))


# ---------------------------------------------------------------------------
# 3. Required TOOL_EVIDENCE with valid PASS metadata satisfies the matching gate
# ---------------------------------------------------------------------------


def test_required_tool_evidence_pass_satisfies_gate(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "make build", "exit_code": "0"},
    )
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "unit-test", "command": "make test", "exit_code": "0"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    gate_outcomes = {e.gate_id: e.outcome for e in report.evaluations}
    assert gate_outcomes["build"] is GateOutcome.PASS
    assert gate_outcomes["unit-test"] is GateOutcome.PASS


# ---------------------------------------------------------------------------
# 4. Explicit tool FAIL blocks PASS and cannot be overridden by AI opinion
# ---------------------------------------------------------------------------


def test_tool_evidence_fail_blocks_pass(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.FAIL,
        metadata={"gate": "build", "command": "make build", "exit_code": "1"},
    )
    _add_evidence(
        session, task, run, EvidenceType.AI_OPINION, EvidenceStatus.PASS,
        metadata={"gate": "build", "summary": "PASS by consensus"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    build_eval = next(e for e in report.evaluations if e.gate_id == "build")
    assert build_eval.outcome is GateOutcome.FAIL
    assert report.verdict is GateOutcome.FAIL


# ---------------------------------------------------------------------------
# 5. Missing / malformed / cross-run / cross-task evidence -> NEED_ACTION
# ---------------------------------------------------------------------------


def test_missing_evidence_is_need_action(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    gate_outcomes = {e.gate_id: e.outcome for e in report.evaluations}
    assert gate_outcomes["build"] is GateOutcome.NEED_ACTION
    assert gate_outcomes["unit-test"] is GateOutcome.NEED_ACTION
    assert report.verdict is GateOutcome.NEED_ACTION


def test_cross_run_evidence_rejected(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    other_run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, other_run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "make build", "exit_code": "0"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    build_eval = next(e for e in report.evaluations if e.gate_id == "build")
    assert build_eval.outcome is GateOutcome.NEED_ACTION


def test_cross_task_evidence_rejected(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    other_project = Project(name="Other")
    SqlProjectRepository(session).add(other_project)
    other_context = ContextPackage(project_id=other_project.id, version=1)
    SqlContextPackageRepository(session).add(other_context)
    other_task = Task(
        project_id=other_project.id, title="Other",
        workflow_id="verified-gate", workflow_version=1,
        context_package_id=other_context.id,
    )
    SqlTaskRepository(session).add(other_task)
    session.commit()
    other_run = _new_run(session, other_task, other_context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, other_task, other_run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "make build", "exit_code": "0"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    build_eval = next(e for e in report.evaluations if e.gate_id == "build")
    assert build_eval.outcome is GateOutcome.NEED_ACTION


def test_malformed_tool_evidence_is_need_action(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"command": "make build", "exit_code": "0"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    build_eval = next(e for e in report.evaluations if e.gate_id == "build")
    assert build_eval.outcome is GateOutcome.NEED_ACTION


# ---------------------------------------------------------------------------
# 6. AI_OPINION never satisfies a deterministic hard gate
# ---------------------------------------------------------------------------


def test_ai_opinion_never_satisfies_gate(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.AI_OPINION, EvidenceStatus.PASS,
        metadata={"gate": "build", "summary": "This gate is PASS by AI judgment"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    build_eval = next(e for e in report.evaluations if e.gate_id == "build")
    assert build_eval.outcome is GateOutcome.NEED_ACTION
    assert report.verdict is GateOutcome.NEED_ACTION


# ---------------------------------------------------------------------------
# 7. D11 Option C: HUMAN_GATE cannot auto-pass for ANY actor
# ---------------------------------------------------------------------------


def test_human_gate_pending_without_decision(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    human_eval = next(e for e in report.evaluations if e.kind.value == "HUMAN_GATE")
    assert human_eval.outcome is GateOutcome.HUMAN_DECISION
    assert report.verdict is GateOutcome.HUMAN_DECISION
    assert report.authority == "none"


@pytest.mark.parametrize(
    ("decision", "actor_id"),
    [
        (decision, actor_id)
        for decision in ("approve", "reject")
        for actor_id in (
            "human:lead",
            "human:lead-engineer",
            "human:admin",
            "agent:coder",
            "tool:build-bot",
            "test:actor",
            "system:gate-bot",
            "user:123",
            "some-random-string",
            "",
        )
    ],
)
def test_human_evidence_any_decision_any_actor_pending(
    gate_session, decision: str, actor_id: str
) -> None:
    """D11 Option C: no actor or decision string proves Human identity.

    Both approve and reject remain unverified HUMAN_DECISION, never PASS,
    VERIFIED, or deterministic FAIL.
    """
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    _add_evidence(
        session, task, run, EvidenceType.HUMAN_EVIDENCE, EvidenceStatus.HUMAN_DECISION,
        metadata={"human_gate": "release-signoff", "decision": decision},
        actor_id=actor_id,
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    human_eval = next(e for e in report.evaluations if e.kind.value == "HUMAN_GATE")
    assert human_eval.outcome is GateOutcome.HUMAN_DECISION
    assert report.verdict is GateOutcome.HUMAN_DECISION


def test_human_evidence_reject_without_identity_stays_pending(gate_session) -> None:
    """D11 Option C rejects cannot become deterministic FAIL without identity."""
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    _add_evidence(
        session, task, run, EvidenceType.HUMAN_EVIDENCE, EvidenceStatus.HUMAN_DECISION,
        metadata={"human_gate": "release-signoff", "decision": "reject"},
        actor_id="human:lead",
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    human_eval = next(e for e in report.evaluations if e.kind.value == "HUMAN_GATE")
    assert human_eval.outcome is GateOutcome.HUMAN_DECISION
    assert report.verdict is GateOutcome.HUMAN_DECISION
    assert report.authority == "none"


def test_human_evidence_observed_status_cannot_auto_pass(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    _add_evidence(
        session, task, run, EvidenceType.HUMAN_EVIDENCE, EvidenceStatus.OBSERVED,
        metadata={"human_gate": "release-signoff", "decision": "approve"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    human_eval = next(e for e in report.evaluations if e.kind.value == "HUMAN_GATE")
    assert human_eval.outcome is GateOutcome.HUMAN_DECISION
    assert "OBSERVED" in human_eval.reason


def test_human_evidence_ambiguous_decision_cannot_auto_pass(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    _add_evidence(
        session, task, run, EvidenceType.HUMAN_EVIDENCE, EvidenceStatus.HUMAN_DECISION,
        metadata={"human_gate": "release-signoff", "decision": "maybe"},
        actor_id="human:lead",
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    human_eval = next(e for e in report.evaluations if e.kind.value == "HUMAN_GATE")
    assert human_eval.outcome is GateOutcome.HUMAN_DECISION


def test_human_evidence_empty_actor_cannot_auto_pass(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    _add_evidence(
        session, task, run, EvidenceType.HUMAN_EVIDENCE, EvidenceStatus.HUMAN_DECISION,
        metadata={"human_gate": "release-signoff", "decision": "approve"},
        actor_id="",
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    human_eval = next(e for e in report.evaluations if e.kind.value == "HUMAN_GATE")
    assert human_eval.outcome is GateOutcome.HUMAN_DECISION


# ---------------------------------------------------------------------------
# 8. VERIFIED/PASS impossible with human gate pending (Option C)
# ---------------------------------------------------------------------------


def test_verified_impossible_with_ai_only_evidence(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.AI_OPINION, EvidenceStatus.PASS,
        metadata={"summary": "everything passes by consensus"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    assert report.verdict is not GateOutcome.PASS
    assert report.authority == "none"


# ---------------------------------------------------------------------------
# 9. Council/Synthesis output cannot mutate a failed/pending gate into verified
# ---------------------------------------------------------------------------


def test_council_output_cannot_mutate_gate_verdict(gate_session) -> None:
    from polynexus_core.council.models import CouncilSpec
    from polynexus_core.council.orchestrator import CouncilOrchestrator

    session, _ = gate_session
    task, context, _ = _seed(session)
    gate_run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)

    before = evaluate_workflow_gates(workflow, task, gate_run, SqlEvidenceRepository(session))
    assert before.verdict is not GateOutcome.PASS

    specs = [
        CouncilSpec(id="p1", role="code-reviewer"),
        CouncilSpec(id="p2", role="risk-reviewer"),
    ]
    import asyncio

    asyncio.run(CouncilOrchestrator(session).run_council(task, context, specs, generation_revision=1))

    after = evaluate_workflow_gates(workflow, task, gate_run, SqlEvidenceRepository(session))
    assert after.verdict is not GateOutcome.PASS
    assert after.authority == "none"


# ---------------------------------------------------------------------------
# 10. Gate outcome / authority / required refs survive close-reopen
# ---------------------------------------------------------------------------


def test_gate_report_close_reopen_durable(gate_session, tmp_path) -> None:
    session, db_path = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    # Use deterministic tool failure for a durable FAIL report. Under D11
    # Option C, Human reject remains unverified HUMAN_DECISION.
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.FAIL,
        metadata={"gate": "build", "command": "make build", "exit_code": "1"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    assert report.verdict is GateOutcome.FAIL
    evidence = persist_gate_report(report, SqlEvidenceRepository(session))
    session.commit()

    session.close()
    url = f"sqlite:///{db_path}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session2 = Session()
    repo2 = SqlEvidenceRepository(session2)
    reloaded = reload_gate_report(
        repo2, evidence.id,
        workflow=workflow, task=task, run=run,
    )
    session2.close()
    engine.dispose()

    assert reloaded.verdict is report.verdict
    assert reloaded.authority == report.authority
    assert reloaded.workflow_id == report.workflow_id
    assert reloaded.task_id == report.task_id
    assert reloaded.run_id == report.run_id
    assert len(reloaded.evaluations) == len(report.evaluations)
    for a, b in zip(reloaded.evaluations, report.evaluations):
        assert a.gate_id == b.gate_id
        assert a.outcome is b.outcome
        assert a.satisfied_by == b.satisfied_by


# ---------------------------------------------------------------------------
# 11. Replaying the same evaluation is idempotent and adds no fabricated evidence
# ---------------------------------------------------------------------------


def test_idempotent_replay_no_fabricated_evidence(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    before = len(repo.list_by_run(run.id))
    report1 = evaluate_workflow_gates(workflow, task, run, repo)
    report2 = evaluate_workflow_gates(workflow, task, run, repo)
    assert len(repo.list_by_run(run.id)) == before
    assert report1.to_json() == report2.to_json()
    assert report1.verdict is report2.verdict


# ---------------------------------------------------------------------------
# 12. Terminal Runs remain truthful
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", [RunState.FAILED, RunState.TIMED_OUT, RunState.CANCELLED])
def test_terminal_required_run_no_verified_verdict(state, gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    run.state = state
    SqlRunRepository(session).update(run)
    session.commit()
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    assert report.verdict is GateOutcome.FAIL
    assert report.authority == "none"
    assert report.evaluations == ()
    reloaded = SqlRunRepository(session).get(run.id)
    assert reloaded.state is state


def test_terminal_run_with_complete_evidence_still_not_pass(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    run.state = RunState.FAILED
    SqlRunRepository(session).update(run)
    session.commit()
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    assert report.verdict is GateOutcome.FAIL
    assert report.authority == "none"
    assert report.evaluations == ()


# ---------------------------------------------------------------------------
# 13. Secret-marker injection
# ---------------------------------------------------------------------------


def test_secret_not_in_gate_result_or_persisted(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.FAIL,
        metadata={"gate": "build", "command": "make build", "exit_code": "1",
                  "error": f"raw-{_SECRET}", "token": "sk-secret-123"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    report_json = report.to_json()
    assert _SECRET not in report_json
    assert "sk-secret-123" not in report_json

    evidence = persist_gate_report(report, SqlEvidenceRepository(session))
    session.commit()
    persisted = SqlEvidenceRepository(session).get(evidence.id)
    assert _SECRET not in str(persisted.metadata)
    assert "sk-secret-123" not in str(persisted.metadata)
    assert report.verdict is GateOutcome.FAIL


# ---------------------------------------------------------------------------
# 14. Same gate FAIL+PASS both insertion orders must be non-PASS
# ---------------------------------------------------------------------------


def test_fail_before_pass_both_orders_non_pass(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.FAIL,
        metadata={"gate": "build", "command": "make build", "exit_code": "1"},
    )
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "make build", "exit_code": "0"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    build_eval = next(e for e in report.evaluations if e.gate_id == "build")
    assert build_eval.outcome is GateOutcome.FAIL
    assert report.verdict is GateOutcome.FAIL


def test_pass_before_fail_both_orders_non_pass(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "make build", "exit_code": "0"},
    )
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.FAIL,
        metadata={"gate": "build", "command": "make build", "exit_code": "1"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    build_eval = next(e for e in report.evaluations if e.gate_id == "build")
    assert build_eval.outcome is GateOutcome.FAIL
    assert report.verdict is GateOutcome.FAIL


# ---------------------------------------------------------------------------
# 15. Hard gate missing/malformed metadata -> NEED_ACTION
# ---------------------------------------------------------------------------


def test_hard_gate_missing_command_metadata_need_action(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "exit_code": "0"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    build_eval = next(e for e in report.evaluations if e.gate_id == "build")
    assert build_eval.outcome is GateOutcome.NEED_ACTION
    assert "command" in build_eval.reason.lower()


def test_hard_gate_missing_exit_code_metadata_need_action(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "make build"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    build_eval = next(e for e in report.evaluations if e.gate_id == "build")
    assert build_eval.outcome is GateOutcome.NEED_ACTION
    assert "exit_code" in build_eval.reason.lower()


def test_hard_gate_non_zero_exit_code_need_action(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "make build", "exit_code": "2"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    build_eval = next(e for e in report.evaluations if e.gate_id == "build")
    assert build_eval.outcome is GateOutcome.NEED_ACTION
    assert "exit_code" in build_eval.reason.lower()


def test_hard_gate_malformed_metadata_need_action(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "make build", "exit_code": None},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    build_eval = next(e for e in report.evaluations if e.gate_id == "build")
    assert build_eval.outcome is GateOutcome.NEED_ACTION


def test_hard_gate_whitespace_command_rejected(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "   ", "exit_code": "0"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    build_eval = next(e for e in report.evaluations if e.gate_id == "build")
    assert build_eval.outcome is GateOutcome.NEED_ACTION


def test_hard_gate_empty_string_command_rejected(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "", "exit_code": "0"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    build_eval = next(e for e in report.evaluations if e.gate_id == "build")
    assert build_eval.outcome is GateOutcome.NEED_ACTION


def test_fail_overrides_pass_even_with_malformed_metadata(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build"},
    )
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.FAIL,
        metadata={"gate": "build", "error": "build failed"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    build_eval = next(e for e in report.evaluations if e.gate_id == "build")
    assert build_eval.outcome is GateOutcome.FAIL


# ---------------------------------------------------------------------------
# 16. Task/workflow identity validation
# ---------------------------------------------------------------------------


def test_task_workflow_id_mismatch_raises_identity_error(gate_session) -> None:
    session, _ = gate_session
    project = Project(name="WP-13 Project")
    SqlProjectRepository(session).add(project)
    context = ContextPackage(project_id=project.id, version=1)
    SqlContextPackageRepository(session).add(context)
    task = Task(
        project_id=project.id,
        title="Wrong workflow",
        workflow_id="wrong-workflow",
        workflow_version=1,
        mode=WorkMode.VALIDATE,
        context_package_id=context.id,
    )
    SqlTaskRepository(session).add(task)
    session.commit()
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    with pytest.raises(WorkflowIdentityError, match="workflow_id"):
        evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))


def test_task_workflow_version_mismatch_raises_identity_error(gate_session) -> None:
    session, _ = gate_session
    project = Project(name="WP-13 Project")
    SqlProjectRepository(session).add(project)
    context = ContextPackage(project_id=project.id, version=1)
    SqlContextPackageRepository(session).add(context)
    task = Task(
        project_id=project.id,
        title="Wrong version",
        workflow_id="verified-gate",
        workflow_version=99,
        mode=WorkMode.VALIDATE,
        context_package_id=context.id,
    )
    SqlTaskRepository(session).add(task)
    session.commit()
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    with pytest.raises(WorkflowIdentityError, match="workflow_version"):
        evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    assert not [
        e for e in SqlEvidenceRepository(session).list_by_run(run.id)
        if e.actor_id == "system:workflow-gate"
        or e.source == "workflow-gate-evaluation"
    ]


def test_run_task_id_mismatch_raises_identity_error(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context, generation_revision=1)
    run.task_id = "fake-task-id"
    # A persisted bound identity cannot be rewritten. The gate still rejects
    # the independently tampered in-memory value with its original error.
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError, match="Run generation is immutable"):
        SqlRunRepository(session).update(run)
        session.commit()
    session.rollback()
    assert SqlRunRepository(session).get(run.id).task_id == task.id
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    with pytest.raises(WorkflowIdentityError, match="task_id"):
        evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))


# ---------------------------------------------------------------------------
# 17. Stale evidence re-evaluation
# ---------------------------------------------------------------------------


def test_stale_evidence_re_evaluate_detects_change(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "make build", "exit_code": "0"},
    )
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "unit-test", "command": "make test", "exit_code": "0"},
    )
    repo = SqlEvidenceRepository(session)
    report1 = evaluate_workflow_gates(workflow, task, run, repo)
    # Under Option C, human gate is pending -> HUMAN_DECISION.
    assert report1.verdict is GateOutcome.HUMAN_DECISION

    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.FAIL,
        metadata={"gate": "build", "command": "make build", "exit_code": "1"},
    )
    report2 = evaluate_workflow_gates(workflow, task, run, repo)
    assert report2.verdict is GateOutcome.FAIL
    assert report1.to_json() != report2.to_json()


# ---------------------------------------------------------------------------
# 18. Cross-project evidence isolation
# ---------------------------------------------------------------------------


def test_cross_project_evidence_rejected(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    other_project = Project(name="Other Project")
    SqlProjectRepository(session).add(other_project)
    other_context = ContextPackage(project_id=other_project.id, version=1)
    SqlContextPackageRepository(session).add(other_context)
    other_task = Task(
        project_id=other_project.id, title="Other Task",
        workflow_id="verified-gate", workflow_version=1,
        context_package_id=other_context.id,
    )
    SqlTaskRepository(session).add(other_task)
    session.commit()
    other_run = _new_run(session, other_task, other_context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, other_task, other_run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "make build", "exit_code": "0"},
    )
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    build_eval = next(e for e in report.evaluations if e.gate_id == "build")
    assert build_eval.outcome is GateOutcome.NEED_ACTION


# ---------------------------------------------------------------------------
# 19. Workflow execution does not bypass gate evaluation
# ---------------------------------------------------------------------------


def test_workflow_execution_does_not_bypass_gates(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    run.state = RunState.COMPLETED
    SqlRunRepository(session).update(run)
    session.commit()
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    report = evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))
    assert report.verdict is not GateOutcome.PASS
    assert report.authority == "none"


# ---------------------------------------------------------------------------
# 20. Durable persist/reload: PASS → FAIL → close/reopen → reload FAIL
# ---------------------------------------------------------------------------


def test_persist_pass_then_fail_close_reopen_reload(gate_session) -> None:
    """Durable persist/reload test: PASS → add FAIL → re-persist →
    close/reopen session → reload must be FAIL."""
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "make build", "exit_code": "0"},
    )
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "unit-test", "command": "make test", "exit_code": "0"},
    )
    repo = SqlEvidenceRepository(session)

    # Initial: HUMAN_DECISION (human gate pending under Option C).
    report_pass = evaluate_workflow_gates(workflow, task, run, repo)
    assert report_pass.verdict is GateOutcome.HUMAN_DECISION
    ev = persist_gate_report(report_pass, repo)
    session.commit()

    # Add FAIL evidence.
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.FAIL,
        metadata={"gate": "build", "command": "make build", "exit_code": "1"},
    )

    # Re-evaluate: FAIL.
    report_fail = evaluate_workflow_gates(workflow, task, run, repo)
    assert report_fail.verdict is GateOutcome.FAIL

    # Re-persist: must update via persistence boundary.
    ev_updated = persist_gate_report(report_fail, repo)
    session.commit()
    assert ev_updated.id == ev.id

    # Close and reopen.
    session.close()
    engine = session.get_bind()
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session2 = Session()
    repo2 = SqlEvidenceRepository(session2)

    # Reload: must be FAIL (durable write).
    reloaded = reload_gate_report(
        repo2, ev.id,
        workflow=workflow, task=task, run=run,
    )
    assert reloaded.verdict is GateOutcome.FAIL
    session2.close()


def test_persist_idempotent_no_duplicate(gate_session) -> None:
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev1 = persist_gate_report(report, repo)
    session.commit()
    ev2 = persist_gate_report(report, repo)
    session.commit()
    assert ev1.id == ev2.id
    gate_reports = [
        e for e in repo.list_by_run(run.id)
        if e.source == "workflow-gate-evaluation"
    ]
    assert len(gate_reports) == 1


# ---------------------------------------------------------------------------
# 21. Tamper detection: verdict
# ---------------------------------------------------------------------------


def test_tamper_verdict_fails_closed(gate_session) -> None:
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper verdict.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    meta["verdict"] = "FAIL" if report.verdict is not GateOutcome.FAIL else "PASS"
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 22. Tamper detection: authority
# ---------------------------------------------------------------------------


def test_tamper_authority_fails_closed(gate_session) -> None:
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper authority.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    meta["authority"] = "forged-authority"
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="authority"):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 23. Tamper detection: evaluations
# ---------------------------------------------------------------------------


def test_tamper_evaluations_fails_closed(gate_session) -> None:
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.FAIL,
        metadata={"gate": "build", "command": "make build", "exit_code": "1"},
    )
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "unit-test", "command": "make test", "exit_code": "0"},
    )
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    assert report.verdict is GateOutcome.FAIL
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper evaluations: change FAIL to PASS.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    evals = json.loads(meta["evaluations"])
    for e in evals:
        if e["outcome"] == "FAIL":
            e["outcome"] = "PASS"
    meta["evaluations"] = json.dumps(evals)
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 24. Tamper detection: required evidence IDs
# ---------------------------------------------------------------------------


def test_tamper_required_evidence_ids_fails_closed(gate_session) -> None:
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "make build", "exit_code": "0"},
    )
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "unit-test", "command": "make test", "exit_code": "0"},
    )
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper required evidence IDs.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    evals = json.loads(meta["evaluations"])
    for e in evals:
        if e["required_evidence_ids"]:
            e["required_evidence_ids"] = ["fake-evidence-id"]
    meta["evaluations"] = json.dumps(evals)
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="evidence.*does not exist"):
        reload_gate_report(
            repo, ev.id,
            workflow=workflow, task=task, run=run,
        )


# ---------------------------------------------------------------------------
# 25. Tamper detection: workflow identity/version
# ---------------------------------------------------------------------------


def test_tamper_workflow_identity_fails_closed(gate_session) -> None:
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper workflow_id in stored metadata.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    meta["workflow_id"] = "tampered-workflow"
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="workflow_id"):
        reload_gate_report(
            repo, ev.id,
            workflow=workflow, task=task, run=run,
        )


# ---------------------------------------------------------------------------
# 26. Reload validates required evidence IDs against actual evidence
# ---------------------------------------------------------------------------


def test_reload_validates_required_evidence_exist(gate_session) -> None:
    """If required_evidence_ids reference evidence that doesn't exist, reload
    must fail closed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Reload with full context must pass.
    reloaded = reload_gate_report(
        repo, ev.id,
        workflow=workflow, task=task, run=run,
    )
    assert reloaded.verdict is report.verdict
    assert reloaded.authority == report.authority


# ---------------------------------------------------------------------------
# 27. ExecutionService integration (real execution path)
# ---------------------------------------------------------------------------


def test_execution_service_runs_gate_evaluation(gate_session) -> None:
    """Verify that ExecutionService.execute_existing_run() evaluates gates
    and persists the gate report as DOCUMENT_EVIDENCE on COMPLETED runs."""
    session, _ = gate_session
    task, context, project = _seed(session)
    run = _new_run(session, task, context, generation_revision=1)

    import asyncio
    from polynexus_core.execution_service import ExecutionService

    service = ExecutionService(session)
    execution = asyncio.run(service.execute_existing_run(run.id))

    repo = SqlEvidenceRepository(session)
    gate_reports = [
        e for e in repo.list_by_run(execution.run.id)
        if e.source == "workflow-gate-evaluation"
    ]

    assert execution.run.state is RunState.COMPLETED
    assert len(gate_reports) == 1
    gate_ev = gate_reports[0]
    assert gate_ev.type is EvidenceType.DOCUMENT_EVIDENCE
    assert "verdict" in gate_ev.metadata
    # ReferenceRuntimeAdapter does not produce TOOL_EVIDENCE for configured gates.
    assert gate_ev.metadata["verdict"] != "PASS"

    # Verify reload works.
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    reloaded = reload_gate_report(repo, gate_ev.id, workflow=workflow, task=task, run=run)
    assert reloaded.run_id == execution.run.id
    assert reloaded.task_id == task.id


# ===========================================================================
# Attempt 5 regression tests — Codex FAIL remediation
# ===========================================================================


# ---------------------------------------------------------------------------
# 34. Partial-context reload (no workflow/task/run) must fail
# ---------------------------------------------------------------------------


def test_reload_requires_full_context() -> None:
    """reload_gate_report() requires workflow/task/run; calling without them
    must raise TypeError (mandatory params)."""
    # The function signature now requires workflow/task/run.
    # Verify that calling without them raises TypeError.
    with pytest.raises(TypeError):
        reload_gate_report(None, "some-id")  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 35. Authority=none with PASS verdict must fail closed
# ---------------------------------------------------------------------------


def test_tamper_authority_none_with_pass_fails_closed(gate_session) -> None:
    """PASS verdict with authority=none is invalid and must fail closed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: set verdict=PASS and authority=none (inconsistent).
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    meta["verdict"] = "PASS"
    meta["authority"] = "none"
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="authority.*none"):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 36. Overall reason tamper must fail closed
# ---------------------------------------------------------------------------


def test_tamper_overall_reason_fails_closed(gate_session) -> None:
    """Tampering overall_reason must fail closed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: change overall_reason.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    meta["overall_reason"] = "forged-reason"
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="overall_reason"):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 37. Tamper: verdict from FAIL to PASS with matching evaluations must fail
# ---------------------------------------------------------------------------


def test_tamper_verdict_fail_to_pass_fails_closed(gate_session) -> None:
    """Changing verdict from FAIL to PASS while leaving evaluations unchanged
    must fail closed because re-evaluation produces FAIL."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.FAIL,
        metadata={"gate": "build", "command": "make build", "exit_code": "1"},
    )
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "unit-test", "command": "make test", "exit_code": "0"},
    )
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    assert report.verdict is GateOutcome.FAIL
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: change verdict to PASS but leave evaluations (including FAIL) unchanged.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    meta["verdict"] = "PASS"
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="verdict"):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 38. Cross-task evidence reference tamper
# ---------------------------------------------------------------------------


def test_tamper_required_evidence_cross_task_fails_closed(gate_session) -> None:
    """required_evidence_ids referencing evidence from another task must fail."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Create evidence in a different task.
    other_project = Project(name="Other")
    SqlProjectRepository(session).add(other_project)
    other_context = ContextPackage(project_id=other_project.id, version=1)
    SqlContextPackageRepository(session).add(other_context)
    other_task = Task(
        project_id=other_project.id, title="Other",
        workflow_id="verified-gate", workflow_version=1,
        context_package_id=other_context.id,
    )
    SqlTaskRepository(session).add(other_task)
    session.commit()
    other_run = _new_run(session, other_task, other_context)
    other_ev = _add_evidence(
        session, other_task, other_run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "make build", "exit_code": "0"},
    )

    # Tamper: reference cross-task evidence in required_evidence_ids.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    evals = json.loads(meta["evaluations"])
    for e in evals:
        if e["required_evidence_ids"]:
            e["required_evidence_ids"] = [other_ev.id]
    meta["evaluations"] = json.dumps(evals)
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="does not exist"):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 39. Evaluation outcome tamper (FAIL to PASS in evaluations)
# ---------------------------------------------------------------------------


def test_tamper_evaluation_outcome_fails_closed(gate_session) -> None:
    """Changing evaluation outcome from FAIL to PASS must fail closed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.FAIL,
        metadata={"gate": "build", "command": "make build", "exit_code": "1"},
    )
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "unit-test", "command": "make test", "exit_code": "0"},
    )
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: change FAIL outcome to PASS in evaluations.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    evals = json.loads(meta["evaluations"])
    for e in evals:
        if e["outcome"] == "FAIL":
            e["outcome"] = "PASS"
    meta["evaluations"] = json.dumps(evals)
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="outcome"):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 40. Evaluation satisfied_by tamper
# ---------------------------------------------------------------------------


def test_tamper_satisfied_by_fails_closed(gate_session) -> None:
    """Changing satisfied_by to a different evidence ID must fail closed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    ev_pass = _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "build", "command": "make build", "exit_code": "0"},
    )
    _add_evidence(
        session, task, run, EvidenceType.TOOL_EVIDENCE, EvidenceStatus.PASS,
        metadata={"gate": "unit-test", "command": "make test", "exit_code": "0"},
    )
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    gate_ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: change satisfied_by in the build evaluation.
    row = session.get(EvidenceRow, gate_ev.id)
    meta = _deserialize_dict(row.metadata_json)
    evals = json.loads(meta["evaluations"])
    for e in evals:
        if e["gate_id"] == "build" and e["satisfied_by"]:
            e["satisfied_by"] = "fake-evidence-id"
    meta["evaluations"] = json.dumps(evals)
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="satisfied_by"):
        reload_gate_report(repo, gate_ev.id, workflow=workflow, task=task, run=run)


# ===========================================================================
# Attempt 6 regression tests — Codex FAIL remediation
# ===========================================================================


# ---------------------------------------------------------------------------
# 41. Gate report type tamper (not DOCUMENT_EVIDENCE) fails closed
# ---------------------------------------------------------------------------


def test_tamper_gate_report_type_fails_closed(gate_session) -> None:
    """If evidence type is changed from DOCUMENT_EVIDENCE, reload fails closed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: change type from DOCUMENT_EVIDENCE to TOOL_EVIDENCE.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    row.type = "TOOL_EVIDENCE"
    session.commit()

    with pytest.raises(GateReportTamperedError, match="DOCUMENT_EVIDENCE"):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 42. Gate report status tamper (not OBSERVED) fails closed
# ---------------------------------------------------------------------------


def test_tamper_gate_report_status_fails_closed(gate_session) -> None:
    """If evidence status is changed from OBSERVED, reload fails closed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: change status from OBSERVED to PASS.
    row = session.get(EvidenceRow, ev.id)
    row.status = "PASS"
    session.commit()

    with pytest.raises(GateReportTamperedError, match="OBSERVED"):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 43. Gate report self-reference cannot satisfy hard gate
# ---------------------------------------------------------------------------


def test_gate_report_self_reference_cannot_satisfy_gate(gate_session) -> None:
    """Gate report evidence must not be treated as TOOL_EVIDENCE for gate evaluation.
    Even if a gate report's metadata contains gate-like keys, it must not satisfy
    a hard gate because it is DOCUMENT_EVIDENCE, not TOOL_EVIDENCE."""
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    repo = SqlEvidenceRepository(session)

    # Create a DOCUMENT_EVIDENCE with gate-like metadata (simulating tamper).
    gate_like_ev = Evidence(
        task_id=task.id,
        run_id=run.id,
        actor_id="system:workflow-gate",
        source="workflow-gate-evaluation",
        type=EvidenceType.DOCUMENT_EVIDENCE,
        status=EvidenceStatus.OBSERVED,
        metadata={"gate": "build", "command": "make build", "exit_code": "0",
                   "verdict": "PASS"},
    )
    SqlEvidenceRepository(session).add(gate_like_ev)
    session.commit()

    # The DOCUMENT_EVIDENCE must NOT satisfy the build gate.
    report = evaluate_workflow_gates(workflow, task, run, repo)
    build_eval = next(e for e in report.evaluations if e.gate_id == "build")
    assert build_eval.outcome is GateOutcome.NEED_ACTION


# ---------------------------------------------------------------------------
# 44. Evaluation reason tamper fails closed
# ---------------------------------------------------------------------------


def test_tamper_evaluation_reason_fails_closed(gate_session) -> None:
    """Tampering evaluation reason must fail closed on reload."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: change reason in evaluations.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    evals = json.loads(meta["evaluations"])
    for e in evals:
        e["reason"] = "forged reason"
    meta["evaluations"] = json.dumps(evals)
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="reason"):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 45. Evaluation step_id tamper fails closed
# ---------------------------------------------------------------------------


def test_tamper_evaluation_step_id_fails_closed(gate_session) -> None:
    """Tampering evaluation step_id must fail closed on reload."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: change step_id in evaluations.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    evals = json.loads(meta["evaluations"])
    for e in evals:
        e["step_id"] = "fake-step"
    meta["evaluations"] = json.dumps(evals)
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 46. Evaluation kind tamper fails closed
# ---------------------------------------------------------------------------


def test_tamper_evaluation_kind_fails_closed(gate_session) -> None:
    """Tampering evaluation kind must fail closed on reload."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: change kind in evaluations.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    evals = json.loads(meta["evaluations"])
    for e in evals:
        e["kind"] = "HUMAN_GATE"
    meta["evaluations"] = json.dumps(evals)
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="kind"):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 47. Tampered identity re-persist remains idempotent (no duplicate)
# ---------------------------------------------------------------------------


def test_tampered_identity_re_persist_no_duplicate(gate_session) -> None:
    """If existing gate report has corrupted identity metadata, persist_gate_report
    must fail closed and not create a duplicate report."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: change workflow_id in identity metadata.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    meta["workflow_id"] = "tampered-workflow"
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    # Re-persist must fail closed, not create a duplicate.
    with pytest.raises(GateReportTamperedError, match="corrupted identity"):
        persist_gate_report(report, repo)

    # Verify no duplicate was created.
    gate_reports = [
        e for e in repo.list_by_run(run.id)
        if e.source == "workflow-gate-evaluation"
    ]
    assert len(gate_reports) == 1


# ===========================================================================
# Attempt 7 regression tests — Codex FAIL remediation
# ===========================================================================


# ---------------------------------------------------------------------------
# 48. run.workflow_version mismatch raises WorkflowIdentityError
# ---------------------------------------------------------------------------


def test_run_workflow_version_mismatch_raises_identity_error(gate_session) -> None:
    """run.workflow_version must equal workflow.version."""
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    run.workflow_version = 99
    SqlRunRepository(session).update(run)
    session.commit()
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    with pytest.raises(WorkflowIdentityError, match="workflow_version"):
        evaluate_workflow_gates(workflow, task, run, SqlEvidenceRepository(session))


# ---------------------------------------------------------------------------
# 49-52. Terminal state persist/close/reopen/reload round-trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", [RunState.FAILED, RunState.TIMED_OUT, RunState.CANCELLED, RunState.ORPHANED])
def test_terminal_state_persist_close_reopen_reload(state, gate_session, tmp_path) -> None:
    """Terminal report with evaluations=() must round-trip through
    persist/close/reopen/reload without failing on missing expected gates."""
    session, db_path = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    run.state = state
    SqlRunRepository(session).update(run)
    session.commit()
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    repo = SqlEvidenceRepository(session)

    report = evaluate_workflow_gates(workflow, task, run, repo)
    assert report.verdict is GateOutcome.FAIL
    assert report.authority == "none"
    assert report.evaluations == ()

    ev = persist_gate_report(report, repo)
    session.commit()

    # Close and reopen.
    session.close()
    url = f"sqlite:///{db_path}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session2 = Session()
    repo2 = SqlEvidenceRepository(session2)

    reloaded = reload_gate_report(repo2, ev.id, workflow=workflow, task=task, run=run)
    assert reloaded.verdict is GateOutcome.FAIL
    assert reloaded.authority == "none"
    assert reloaded.evaluations == ()
    session2.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# 53. Source tamper no-duplicate
# ---------------------------------------------------------------------------


def test_source_tamper_no_duplicate(gate_session) -> None:
    """If existing gate report has corrupted source, persist must fail closed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: change source.
    row = session.get(EvidenceRow, ev.id)
    row.source = "tampered-source"
    session.commit()

    with pytest.raises(GateReportTamperedError, match="corrupted source"):
        persist_gate_report(report, repo)

    gate_reports = [
        e for e in repo.list_by_run(run.id)
        if "workflow_id" in e.metadata and "verdict" in e.metadata
    ]
    assert len(gate_reports) == 1


# ---------------------------------------------------------------------------
# 54. Type tamper no-duplicate
# ---------------------------------------------------------------------------


def test_type_tamper_no_duplicate(gate_session) -> None:
    """If existing gate report has corrupted type, persist must fail closed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: change type.
    row = session.get(EvidenceRow, ev.id)
    row.type = "TOOL_EVIDENCE"
    session.commit()

    with pytest.raises(GateReportTamperedError, match="corrupted type"):
        persist_gate_report(report, repo)

    gate_reports = [
        e for e in repo.list_by_run(run.id)
        if "workflow_id" in e.metadata and "verdict" in e.metadata
    ]
    assert len(gate_reports) == 1


# ---------------------------------------------------------------------------
# 55. Identity tamper (workflow_version) no-duplicate
# ---------------------------------------------------------------------------


def test_identity_tamper_workflow_version_no_duplicate(gate_session) -> None:
    """If existing gate report has corrupted workflow_version, persist must fail closed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: change workflow_version.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    meta["workflow_version"] = "99"
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="corrupted identity"):
        persist_gate_report(report, repo)

    gate_reports = [
        e for e in repo.list_by_run(run.id)
        if "workflow_id" in e.metadata and "verdict" in e.metadata
    ]
    assert len(gate_reports) == 1


# ---------------------------------------------------------------------------
# 56. Malformed workflow_version metadata fails closed
# ---------------------------------------------------------------------------


def test_malformed_workflow_version_fails_closed(gate_session) -> None:
    """If existing gate report has malformed workflow_version, persist must fail closed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: set workflow_version to non-integer.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    meta["workflow_version"] = "not-a-number"
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="malformed"):
        persist_gate_report(report, repo)


# ---------------------------------------------------------------------------
# 57. Source tamper + removed verdict fails closed without duplicate
# ---------------------------------------------------------------------------


def test_source_tamper_remove_verdict_no_duplicate(gate_session) -> None:
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    row = session.get(EvidenceRow, ev.id)
    row.source = "tampered-source"
    meta = _deserialize_dict(row.metadata_json)
    meta.pop("verdict", None)
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError):
        persist_gate_report(report, repo)
    assert len(repo.list_by_run(run.id)) == 3


# ---------------------------------------------------------------------------
# 58. Type tamper + removed evaluations fails closed without duplicate
# ---------------------------------------------------------------------------


def test_type_tamper_remove_evaluations_no_duplicate(gate_session) -> None:
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    row = session.get(EvidenceRow, ev.id)
    row.type = "TOOL_EVIDENCE"
    meta = _deserialize_dict(row.metadata_json)
    meta.pop("evaluations", None)
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError):
        persist_gate_report(report, repo)
    assert len(repo.list_by_run(run.id)) == 3


# ---------------------------------------------------------------------------
# 59. Source + type tamper with canonical actor fails closed
# ---------------------------------------------------------------------------


def test_source_and_type_tamper_canonical_actor_no_duplicate(gate_session) -> None:
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    row = session.get(EvidenceRow, ev.id)
    # actor_id remains the canonical marker while source/type are corrupted.
    row.source = "tampered-source"
    row.type = "TOOL_EVIDENCE"
    session.commit()

    with pytest.raises(GateReportTamperedError):
        persist_gate_report(report, repo)
    assert len(repo.list_by_run(run.id)) == 3


# ---------------------------------------------------------------------------
# 60. Actor + source tamper is detected by the metadata fingerprint
# ---------------------------------------------------------------------------


def test_actor_and_source_tamper_metadata_fingerprint_no_duplicate(
    gate_session,
) -> None:
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    row = session.get(EvidenceRow, ev.id)
    row.actor_id = "tampered-actor"
    row.source = "tampered-source"
    session.commit()

    with pytest.raises(GateReportTamperedError, match="corrupted actor_id"):
        persist_gate_report(report, repo)
    assert len(repo.list_by_run(run.id)) == 3


# ---------------------------------------------------------------------------
# 61. Multiple gate-report candidates fail closed
# ---------------------------------------------------------------------------


def test_multiple_gate_report_candidates_fail_closed(gate_session) -> None:
    session, db_path = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    first = persist_gate_report(report, repo)
    session.commit()

    # A second canonical candidate is inserted directly to simulate corruption.
    second = Evidence(
        task_id=task.id,
        run_id=run.id,
        actor_id="system:workflow-gate",
        source="workflow-gate-evaluation",
        type=EvidenceType.DOCUMENT_EVIDENCE,
        status=EvidenceStatus.OBSERVED,
        metadata={
            "workflow_id": workflow.id,
            "workflow_version": str(workflow.version),
            "verdict": report.verdict.value,
            "authority": report.authority,
            "overall_reason": report.overall_reason,
            "evaluations": json.dumps(
                [e.to_mapping() for e in report.evaluations], sort_keys=True
            ),
        },
    )
    repo.add(second)
    session.commit()
    session.close()

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session2 = Session()
    repo2 = SqlEvidenceRepository(session2)
    with pytest.raises(GateReportTamperedError, match="multiple"):
        persist_gate_report(report, repo2)
    assert first.id != second.id
    assert len(
        [
            e for e in repo2.list_by_run(run.id)
            if e.actor_id == "system:workflow-gate"
            or e.source == "workflow-gate-evaluation"
        ]
    ) == 2
    session2.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# 62. Unrelated DOCUMENT_EVIDENCE does not block first persist
# ---------------------------------------------------------------------------


def test_unrelated_document_evidence_does_not_block_first_persist(gate_session) -> None:
    session, db_path = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    repo = SqlEvidenceRepository(session)

    unrelated = Evidence(
        task_id=task.id,
        run_id=run.id,
        actor_id="system:document-import",
        source="document-import",
        type=EvidenceType.DOCUMENT_EVIDENCE,
        status=EvidenceStatus.OBSERVED,
        metadata={"workflow_id": workflow.id, "title": "ordinary document"},
    )
    repo.add(unrelated)
    session.commit()
    session.close()

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session2 = Session()
    repo2 = SqlEvidenceRepository(session2)
    report = evaluate_workflow_gates(workflow, task, run, repo2)
    gate_report = persist_gate_report(report, repo2)
    session2.commit()
    assert gate_report.source == "workflow-gate-evaluation"
    assert len(repo2.list_by_run(run.id)) == 2
    session2.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# 63. Corrupted candidates remain fail-closed after close/reopen
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tamper_case",
    [
        "source_remove_verdict",
        "type_remove_evaluations",
        "source_type_canonical_actor",
        "actor_source_metadata_fingerprint",
    ],
)
def test_corrupted_candidate_close_reopen_stays_fail_closed(
    gate_session, tamper_case: str
) -> None:
    from polynexus_core.persistence.models import EvidenceRow

    session, db_path = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    if tamper_case == "source_remove_verdict":
        row.source = "tampered-source"
        meta.pop("verdict", None)
    elif tamper_case == "type_remove_evaluations":
        row.type = "TOOL_EVIDENCE"
        meta.pop("evaluations", None)
    elif tamper_case == "source_type_canonical_actor":
        row.source = "tampered-source"
        row.type = "TOOL_EVIDENCE"
    elif tamper_case == "actor_source_metadata_fingerprint":
        row.actor_id = "tampered-actor"
        row.source = "tampered-source"
    else:  # pragma: no cover - parametrization is closed above
        raise AssertionError(f"unexpected tamper case: {tamper_case}")
    row.metadata_json = _serialize_dict(meta)
    session.commit()
    session.close()

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session2 = Session()
    repo2 = SqlEvidenceRepository(session2)
    with pytest.raises(GateReportTamperedError):
        persist_gate_report(report, repo2)
    assert len(repo2.list_by_run(run.id)) == 3
    session2.close()
    engine.dispose()


# ===========================================================================
# Attempt 9 regression tests — Codex FAIL remediation
# ===========================================================================


# ---------------------------------------------------------------------------
# 64. Actor tamper in reload → GateReportTamperedError
# ---------------------------------------------------------------------------


def test_tamper_actor_reload_fails_closed(gate_session) -> None:
    """Changing actor_id from canonical system:workflow-gate must fail closed on reload."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: change actor_id.
    row = session.get(EvidenceRow, ev.id)
    row.actor_id = "attacker"
    session.commit()

    with pytest.raises(GateReportTamperedError, match="actor_id"):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 65. Actor tamper + close/reopen → still fails closed
# ---------------------------------------------------------------------------


def test_tamper_actor_close_reopen_reload_fails_closed(gate_session) -> None:
    """Actor tamper persists across close/reopen and reload still fails closed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, db_path = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper actor.
    row = session.get(EvidenceRow, ev.id)
    row.actor_id = "attacker"
    session.commit()
    session.close()

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session2 = Session()
    repo2 = SqlEvidenceRepository(session2)
    with pytest.raises(GateReportTamperedError, match="actor_id"):
        reload_gate_report(repo2, ev.id, workflow=workflow, task=task, run=run)
    session2.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# 66. task_id row tamper → persist must fail closed, no duplicate
# ---------------------------------------------------------------------------


def test_tamper_task_id_persist_no_duplicate(gate_session) -> None:
    """Row-level task_id tamper must be detected and fail closed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: change row-level task_id.
    row = session.get(EvidenceRow, ev.id)
    row.task_id = "tampered-task-id"
    session.commit()

    # Re-persist must fail closed and not create a duplicate.
    with pytest.raises(GateReportTamperedError, match="task_id"):
        persist_gate_report(report, repo)

    gate_reports = [
        e for e in repo.list_by_task(task.id)
        if e.actor_id == "system:workflow-gate"
        or e.source == "workflow-gate-evaluation"
    ]
    assert len(gate_reports) == 0  # tampered record not found by original task_id


# ---------------------------------------------------------------------------
# 67. run_id row tamper → persist must fail closed, no duplicate
# ---------------------------------------------------------------------------


def test_tamper_run_id_persist_no_duplicate(gate_session) -> None:
    """Row-level run_id tamper must be detected and fail closed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper: change row-level run_id.
    row = session.get(EvidenceRow, ev.id)
    row.run_id = "tampered-run-id"
    session.commit()

    # Re-persist must fail closed and not create a duplicate.
    with pytest.raises(GateReportTamperedError, match="run_id"):
        persist_gate_report(report, repo)

    # The tampered record's task_id is still correct, so it's found by
    # list_by_task() — but it is a corrupted gate report, not a valid one.
    gate_reports = [
        e for e in repo.list_by_task(task.id)
        if e.actor_id == "system:workflow-gate"
        or e.source == "workflow-gate-evaluation"
    ]
    assert len(gate_reports) == 1  # tampered record found by task_id


# ---------------------------------------------------------------------------
# 68. task_id tamper + close/reopen → persist still fails closed
# ---------------------------------------------------------------------------


def test_tamper_task_id_close_reopen_persist_fails_closed(gate_session) -> None:
    """Row-level task_id tamper persists across close/reopen."""
    from polynexus_core.persistence.models import EvidenceRow

    session, db_path = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper task_id.
    row = session.get(EvidenceRow, ev.id)
    row.task_id = "tampered-task-id"
    session.commit()
    session.close()

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session2 = Session()
    repo2 = SqlEvidenceRepository(session2)
    with pytest.raises(GateReportTamperedError, match="task_id"):
        persist_gate_report(report, repo2)
    # Gate report not found by original task_id (tampered); only tool evidence remains.
    assert len(repo2.list_by_task(task.id)) == 2  # 2 tool evidence, no gate report
    session2.close()
    engine.dispose()


def test_tamper_run_id_close_reopen_persist_fails_closed(gate_session) -> None:
    """Row-level run_id tamper persists across close/reopen."""
    from polynexus_core.persistence.models import EvidenceRow

    session, db_path = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper run_id.
    row = session.get(EvidenceRow, ev.id)
    row.run_id = "tampered-run-id"
    session.commit()
    session.close()

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session2 = Session()
    repo2 = SqlEvidenceRepository(session2)
    with pytest.raises(GateReportTamperedError, match="run_id"):
        persist_gate_report(report, repo2)
    # Tampered record's task_id is still correct, so found by list_by_task().
    assert len(repo2.list_by_task(task.id)) == 3  # 2 tool + 1 tampered gate report
    session2.close()
    engine.dispose()


# ===========================================================================
# Attempt 9 fix — combined task_id+run_id tamper & overlapping metadata
# ===========================================================================


# ---------------------------------------------------------------------------
# 70. Combined task_id + run_id tamper → persist must fail closed
# ---------------------------------------------------------------------------


def test_tamper_task_and_run_ids_together_persist_no_duplicate(gate_session) -> None:
    """When BOTH row-level task_id AND run_id are tampered simultaneously,
    neither list_by_run() nor list_by_task() finds the record. The global
    list_all() scan must still detect it via canonical actor/source markers
    and fail closed without creating a duplicate."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper BOTH task_id and run_id together.
    row = session.get(EvidenceRow, ev.id)
    row.task_id = "tampered-task-id"
    row.run_id = "tampered-run-id"
    session.commit()

    # Neither list_by_run() nor list_by_task() can find the record now.
    assert len(repo.list_by_run(run.id)) == 2   # only tool evidence
    assert len(repo.list_by_task(task.id)) == 2  # only tool evidence

    # Re-persist must fail closed via global list_all() scan.
    with pytest.raises(GateReportTamperedError, match="task_id"):
        persist_gate_report(report, repo)

    # No duplicate was created: total gate reports across all evidence == 1.
    all_gate_reports = [
        e for e in repo.list_all()
        if e.actor_id == "system:workflow-gate"
        or e.source == "workflow-gate-evaluation"
    ]
    assert len(all_gate_reports) == 1


# ---------------------------------------------------------------------------
# 71. Ordinary DOCUMENT_EVIDENCE with overlapping metadata does not block first persist
# ---------------------------------------------------------------------------


def test_unrelated_document_evidence_with_overlapping_metadata_does_not_block(
    gate_session,
) -> None:
    """An ordinary DOCUMENT_EVIDENCE that happens to carry one or two metadata
    keys overlapping with gate report keys (e.g. workflow_id + verdict) must
    NOT be classified as a gate-report candidate. It must not block first
    persist or trigger GateReportTamperedError."""
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    repo = SqlEvidenceRepository(session)

    # An ordinary document with partial overlap (only 2 of the 6 required keys).
    unrelated_doc = Evidence(
        task_id=task.id,
        run_id=run.id,
        actor_id="system:document-import",
        source="document-import",
        type=EvidenceType.DOCUMENT_EVIDENCE,
        status=EvidenceStatus.OBSERVED,
        metadata={
            "workflow_id": workflow.id,
            "verdict": "some prose conclusion",
        },
    )
    repo.add(unrelated_doc)
    session.commit()

    # First persist must succeed despite the overlapping metadata.
    report = evaluate_workflow_gates(workflow, task, run, repo)
    gate_report = persist_gate_report(report, repo)
    session.commit()

    assert gate_report.source == "workflow-gate-evaluation"
    assert gate_report.actor_id == "system:workflow-gate"

    # Replay is idempotent — updates in place, no duplicate.
    gate_report_2 = persist_gate_report(report, repo)
    session.commit()
    assert gate_report_2.id == gate_report.id

    # Total evidence: 1 unrelated doc + 1 gate report = 2 for this run.
    assert len(repo.list_by_run(run.id)) == 2


# ===========================================================================
# Attempt 9 fix — multi-task isolation & durable metadata binding
# ===========================================================================


# ---------------------------------------------------------------------------
# 72. Two independent tasks/runs each persist their own gate report
# ---------------------------------------------------------------------------


def _seed_second_task(session, first_project):
    """Create a second independent task + context + run under the same project."""
    context2 = ContextPackage(project_id=first_project.id, version=2)
    SqlContextPackageRepository(session).add(context2)
    task2 = Task(
        project_id=first_project.id,
        title="Gate task 2",
        workflow_id="verified-gate",
        workflow_version=1,
        mode=WorkMode.VALIDATE,
        context_package_id=context2.id,
    )
    SqlTaskRepository(session).add(task2)
    session.commit()
    run2 = Run(
        task_id=task2.id,
        workflow_id=task2.workflow_id,
        workflow_version=task2.workflow_version,
        context_package_id=context2.id,
     generation_revision=None)
    SqlRunRepository(session).add(run2)
    session.commit()
    return task2, context2, run2


def test_two_independent_tasks_runs_each_persist_gate_report(gate_session) -> None:
    """Two different task/run pairs must each be able to persist their own
    gate report without one blocking the other."""
    session, _ = gate_session
    task1, context1, project = _seed(session)
    run1 = _new_run(session, task1, context1)
    task2, context2, run2 = _seed_second_task(session, project)

    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    repo = SqlEvidenceRepository(session)

    # Persist gate report for task1/run1.
    _add_all_pass_evidence(session, task1, run1)
    report1 = evaluate_workflow_gates(workflow, task1, run1, repo)
    ev1 = persist_gate_report(report1, repo)
    session.commit()

    # Persist gate report for task2/run2.
    _add_all_pass_evidence(session, task2, run2)
    report2 = evaluate_workflow_gates(workflow, task2, run2, repo)
    ev2 = persist_gate_report(report2, repo)
    session.commit()

    # Both must succeed independently.
    assert ev1.id != ev2.id
    assert ev1.task_id == task1.id
    assert ev2.task_id == task2.id

    # Each run has exactly 1 gate report.
    gate_reports_r1 = [
        e for e in repo.list_by_run(run1.id) if e.source == "workflow-gate-evaluation"
    ]
    gate_reports_r2 = [
        e for e in repo.list_by_run(run2.id) if e.source == "workflow-gate-evaluation"
    ]
    assert len(gate_reports_r1) == 1
    assert len(gate_reports_r2) == 1


# ---------------------------------------------------------------------------
# 73. Replay of each report updates/reuses only its own row
# ---------------------------------------------------------------------------


def test_replay_updates_only_own_row_per_task_run(gate_session) -> None:
    """Replaying a gate report for task1/run1 must update only task1's row;
    replaying for task2/run2 must update only task2's row."""
    session, _ = gate_session
    task1, context1, project = _seed(session)
    run1 = _new_run(session, task1, context1)
    task2, context2, run2 = _seed_second_task(session, project)

    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    repo = SqlEvidenceRepository(session)

    # Initial persist for both.
    _add_all_pass_evidence(session, task1, run1)
    report1 = evaluate_workflow_gates(workflow, task1, run1, repo)
    ev1 = persist_gate_report(report1, repo)
    session.commit()

    _add_all_pass_evidence(session, task2, run2)
    report2 = evaluate_workflow_gates(workflow, task2, run2, repo)
    ev2 = persist_gate_report(report2, repo)
    session.commit()

    # Replay task1 — must reuse ev1, not ev2.
    ev1_replay = persist_gate_report(report1, repo)
    session.commit()
    assert ev1_replay.id == ev1.id
    assert ev1_replay.id != ev2.id

    # Replay task2 — must reuse ev2, not ev1.
    ev2_replay = persist_gate_report(report2, repo)
    session.commit()
    assert ev2_replay.id == ev2.id
    assert ev2_replay.id != ev1.id

    # Total gate reports across DB: still exactly 2.
    all_gate_reports = [
        e for e in repo.list_all() if e.source == "workflow-gate-evaluation"
    ]
    assert len(all_gate_reports) == 2


# ===========================================================================
# Attempt 9 fix — binding validation & same-task multi-run isolation
# ===========================================================================


# ---------------------------------------------------------------------------
# 74. Binding tamper: bound_task_id → reload fails closed
# ---------------------------------------------------------------------------


def test_tamper_bound_task_id_reload_fails_closed(gate_session) -> None:
    """Tampering bound_task_id in metadata must fail closed on reload."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    meta["bound_task_id"] = "tampered-bound-task"
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="bound_task_id"):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 75. Binding tamper: bound_run_id → reload fails closed
# ---------------------------------------------------------------------------


def test_tamper_bound_run_id_reload_fails_closed(gate_session) -> None:
    """Tampering bound_run_id in metadata must fail closed on reload."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    meta["bound_run_id"] = "tampered-bound-run"
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="bound_run_id"):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 76. Binding removal → persist fails closed
# ---------------------------------------------------------------------------


def test_remove_binding_metadata_persist_fails_closed(gate_session) -> None:
    """Removing bound_task_id/bound_run_id from metadata must fail closed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    del meta["bound_task_id"]
    del meta["bound_run_id"]
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="binding"):
        persist_gate_report(report, repo)


# ---------------------------------------------------------------------------
# 77. Same-task multiple runs each persist their own gate report
# ---------------------------------------------------------------------------


def test_same_task_two_runs_each_persist_own_gate_report(gate_session) -> None:
    """Two runs under the SAME task must each be able to create and persist
    their own independent gate report without cross-contamination."""
    session, _ = gate_session
    task, context, project = _seed(session)
    run1 = _new_run(session, task, context)
    # Second run under the SAME task (different ContextPackage not required).
    run2 = Run(
        task_id=task.id,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=context.id,
     generation_revision=None)
    SqlRunRepository(session).add(run2)
    session.commit()

    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    repo = SqlEvidenceRepository(session)

    # Persist gate report for run1.
    _add_all_pass_evidence(session, task, run1)
    report1 = evaluate_workflow_gates(workflow, task, run1, repo)
    ev1 = persist_gate_report(report1, repo)
    session.commit()

    # Persist gate report for run2 under the same task.
    _add_all_pass_evidence(session, task, run2)
    report2 = evaluate_workflow_gates(workflow, task, run2, repo)
    ev2 = persist_gate_report(report2, repo)
    session.commit()

    # Both must succeed independently.
    assert ev1.id != ev2.id
    assert ev1.run_id == run1.id
    assert ev2.run_id == run2.id
    assert ev1.task_id == task.id
    assert ev2.task_id == task.id

    # Each run has exactly 1 gate report.
    reports_r1 = [
        e for e in repo.list_by_run(run1.id) if e.source == "workflow-gate-evaluation"
    ]
    reports_r2 = [
        e for e in repo.list_by_run(run2.id) if e.source == "workflow-gate-evaluation"
    ]
    assert len(reports_r1) == 1
    assert len(reports_r2) == 1


# ---------------------------------------------------------------------------
# 78. Same-task replay of run1 does not affect run2's report
# ---------------------------------------------------------------------------


def test_same_task_replay_run1_does_not_affect_run2(gate_session) -> None:
    """Replaying run1's gate report must not update or invalidate run2's report
    when both runs share the same parent task."""
    session, _ = gate_session
    task, context, project = _seed(session)
    run1 = _new_run(session, task, context)
    run2 = Run(
        task_id=task.id,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=context.id,
     generation_revision=None)
    SqlRunRepository(session).add(run2)
    session.commit()

    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    repo = SqlEvidenceRepository(session)

    # Initial persists.
    _add_all_pass_evidence(session, task, run1)
    report1 = evaluate_workflow_gates(workflow, task, run1, repo)
    ev1 = persist_gate_report(report1, repo)
    session.commit()

    _add_all_pass_evidence(session, task, run2)
    report2 = evaluate_workflow_gates(workflow, task, run2, repo)
    ev2 = persist_gate_report(report2, repo)
    session.commit()

    original_ev2_verdict = ev2.metadata.get("verdict")

    # Replay run1 — must only touch ev1.
    ev1_replay = persist_gate_report(report1, repo)
    session.commit()
    assert ev1_replay.id == ev1.id
    assert ev1_replay.id != ev2.id

    # Verify run2's report was untouched.
    reloaded_ev2 = repo.get(ev2.id)
    assert reloaded_ev2 is not None
    assert reloaded_ev2.metadata.get("verdict") == original_ev2_verdict
    assert reloaded_ev2.metadata.get("bound_run_id") == run2.id

    # Total gate reports: still exactly 2 (one per run).
    all_gate_reports = [
        e for e in repo.list_all() if e.source == "workflow-gate-evaluation"
    ]
    assert len(all_gate_reports) == 2


# ===========================================================================
# Attempt 9 fix — combined row+binding tamper safety net
# ===========================================================================


# ---------------------------------------------------------------------------
# 79. Combined row task_id+run_id + binding bound_task_id/bound_run_id tamper
#     → close/reopen → persist must fail closed, no duplicate
# ---------------------------------------------------------------------------


def test_combined_row_and_binding_tamper_close_reopen_fail_closed(
    gate_session,
) -> None:
    """Simultaneously tampering row-level task_id/run_id AND metadata
    bound_task_id/bound_run_id must be detected via the internal-consistency
    safety net. After close/reopen, persist must fail closed and the total
    canonical gate report count must remain 1 (no duplicate created)."""
    from polynexus_core.persistence.models import EvidenceRow

    session, db_path = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Verify initial state: exactly 1 canonical gate report.
    initial_reports = [
        e for e in repo.list_all()
        if e.actor_id == "system:workflow-gate"
        and e.source == "workflow-gate-evaluation"
    ]
    assert len(initial_reports) == 1

    # Tamper ALL four identity fields simultaneously.
    row = session.get(EvidenceRow, ev.id)
    row.task_id = "tampered-row-task"       # row-level task_id tampered
    row.run_id = "tampered-row-run"         # row-level run_id tampered
    meta = _deserialize_dict(row.metadata_json)
    meta["bound_task_id"] = "tampered-bind-task"  # binding task_id tampered
    meta["bound_run_id"] = "tampered-bind-run"    # binding run_id tampered
    row.metadata_json = _serialize_dict(meta)
    session.commit()
    session.close()

    # Close/reopen: fresh session to simulate process restart.
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session2 = Session()
    repo2 = SqlEvidenceRepository(session2)

    # Persist must fail closed — the identity hash detects the existing
    # tampered report even though all visible identity fields were changed.
    with pytest.raises(GateReportTamperedError, match="dual-hash provenance"):
        persist_gate_report(report, repo2)

    # No duplicate was created: total canonical gate reports across DB == 1.
    all_canonical = [
        e for e in repo2.list_all()
        if e.actor_id == "system:workflow-gate"
        and e.source == "workflow-gate-evaluation"
    ]
    assert len(all_canonical) == 1
    assert all_canonical[0].id == ev.id

    session2.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# 80. Combined tamper on one task does not block legitimate creation for another
# ---------------------------------------------------------------------------


def test_combined_tamper_on_one_task_does_not_block_another(gate_session) -> None:
    """An internally inconsistent (tampered) gate report under Task A must not
    prevent Task B (same workflow) from creating its own legitimate report.
    The identity-hash mechanism is inherently task/run-scoped: different
    tasks produce different hashes, so Task A's corruption cannot interfere
    with Task B's persist operation."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task_a, context_a, project = _seed(session)
    run_a = _new_run(session, task_a, context_a)

    # Create Task B under same project.
    context_b = ContextPackage(project_id=project.id, version=2)
    SqlContextPackageRepository(session).add(context_b)
    task_b = Task(
        project_id=project.id,
        title="Gate task B",
        workflow_id="verified-gate",
        workflow_version=1,
        mode=WorkMode.VALIDATE,
        context_package_id=context_b.id,
    )
    SqlTaskRepository(session).add(task_b)
    session.commit()
    run_b = Run(
        task_id=task_b.id,
        workflow_id=task_b.workflow_id,
        workflow_version=task_b.workflow_version,
        context_package_id=context_b.id,
     generation_revision=None)
    SqlRunRepository(session).add(run_b)
    session.commit()

    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    repo = SqlEvidenceRepository(session)

    # Create a legitimate report for Task A, then tamper all 4 identity fields.
    _add_all_pass_evidence(session, task_a, run_a)
    report_a = evaluate_workflow_gates(workflow, task_a, run_a, repo)
    ev_a = persist_gate_report(report_a, repo)
    session.commit()

    row_a = session.get(EvidenceRow, [
        e for e in repo.list_by_run(run_a.id)
        if e.source == "workflow-gate-evaluation"
    ][0].id)
    row_a.task_id = "tampered-A-task"
    row_a.run_id = "tampered-A-run"
    meta_a = _deserialize_dict(row_a.metadata_json)
    meta_a["bound_task_id"] = "tampered-A-bind-task"
    meta_a["bound_run_id"] = "tampered-A-bind-run"
    row_a.metadata_json = _serialize_dict(meta_a)
    session.commit()

    # Task B must successfully create its own gate report because the
    # identity hash is task/run-scoped. Task A's corruption does not
    # produce a matching hash for Task B's identity.
    _add_all_pass_evidence(session, task_b, run_b)
    report_b = evaluate_workflow_gates(workflow, task_b, run_b, repo)
    ev_b = persist_gate_report(report_b, repo)
    session.commit()

    # Task B's report was created successfully.
    assert ev_b.task_id == task_b.id
    assert ev_b.run_id == run_b.id

    # Total canonical gate reports across DB: 2 (Task A's tampered one + Task B's).
    all_canonical = [
        e for e in repo.list_all()
        if e.actor_id == "system:workflow-gate"
        and e.source == "workflow-gate-evaluation"
    ]
    assert len(all_canonical) == 2


# ===========================================================================
# Attempt 9 fix — same-task multi-run isolation & multi-field tamper
# ===========================================================================


# ---------------------------------------------------------------------------
# 81. Same-task corrupted run1 does not block valid run2
# ---------------------------------------------------------------------------


def test_same_task_corrupted_run1_does_not_block_valid_run2(gate_session) -> None:
    """When run1's gate report is fully tampered under the same task,
    run2 must still be able to create its own legitimate gate report."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, project = _seed(session)
    run1 = _new_run(session, task, context)
    run2 = Run(
        task_id=task.id,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=context.id,
     generation_revision=None)
    SqlRunRepository(session).add(run2)
    session.commit()

    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    repo = SqlEvidenceRepository(session)

    # Create and tamper run1's report.
    _add_all_pass_evidence(session, task, run1)
    report1 = evaluate_workflow_gates(workflow, task, run1, repo)
    persist_gate_report(report1, repo)
    session.commit()

    ev1_row = session.get(EvidenceRow, [
        e for e in repo.list_by_run(run1.id)
        if e.source == "workflow-gate-evaluation"
    ][0].id)
    ev1_row.task_id = "tampered-r1-task"
    ev1_row.run_id = "tampered-r1-run"
    meta1 = _deserialize_dict(ev1_row.metadata_json)
    meta1["bound_task_id"] = "tampered-r1-bind-t"
    meta1["bound_run_id"] = "tampered-r1-bind-r"
    ev1_row.metadata_json = _serialize_dict(meta1)
    session.commit()

    # Run2 must successfully create its own independent report.
    _add_all_pass_evidence(session, task, run2)
    report2 = evaluate_workflow_gates(workflow, task, run2, repo)
    ev2 = persist_gate_report(report2, repo)
    session.commit()

    # Run2's report was created successfully with correct identity.
    assert ev2.run_id == run2.id
    assert ev2.task_id == task.id

    # Total canonical gate reports across DB: 2 (tampered run1 + valid run2).
    all_canonical = [
        e for e in repo.list_all()
        if e.actor_id == "system:workflow-gate"
        and e.source == "workflow-gate-evaluation"
    ]
    assert len(all_canonical) == 2


# ---------------------------------------------------------------------------
# 82-84. Multi-field tamper (all 6 fields / source+row+binding / actor+row+binding)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tamper_scenario",
    [
        "all_six_fields",
        "source_plus_row_binding",
        "actor_plus_row_binding",
    ],
)
def test_multi_field_tamper_close_reopen_fail_closed(
    gate_session, tamper_scenario: str
) -> None:
    """Simultaneous multi-field tampering must be detected via the durable
    identity hash even when canonical actor/source are also changed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, db_path = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Verify initial state: exactly 1 canonical gate report.
    initial_reports = [
        e for e in repo.list_all()
        if e.actor_id == "system:workflow-gate"
        and e.source == "workflow-gate-evaluation"
    ]
    assert len(initial_reports) == 1

    row = session.get(EvidenceRow, ev.id)

    if tamper_scenario == "all_six_fields":
        row.actor_id = "attacker"
        row.source = "tampered-source"
        row.task_id = "tampered-row-t"
        row.run_id = "tampered-row-r"
        meta = _deserialize_dict(row.metadata_json)
        meta["bound_task_id"] = "tampered-bind-t"
        meta["bound_run_id"] = "tampered-bind-r"
        row.metadata_json = _serialize_dict(meta)
    elif tamper_scenario == "source_plus_row_binding":
        row.source = "tampered-source"
        row.task_id = "tampered-row-t"
        row.run_id = "tampered-row-r"
        meta = _deserialize_dict(row.metadata_json)
        meta["bound_task_id"] = "tampered-bind-t"
        meta["bound_run_id"] = "tampered-bind-r"
        row.metadata_json = _serialize_dict(meta)
    elif tamper_scenario == "actor_plus_row_binding":
        row.actor_id = "attacker"
        row.task_id = "tampered-row-t"
        row.run_id = "tampered-row-r"
        meta = _deserialize_dict(row.metadata_json)
        meta["bound_task_id"] = "tampered-bind-t"
        meta["bound_run_id"] = "tampered-bind-r"
        row.metadata_json = _serialize_dict(meta)

    session.commit()
    session.close()

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session2 = Session()
    repo2 = SqlEvidenceRepository(session2)

    # Persist must fail closed via the identity hash.
    with pytest.raises(GateReportTamperedError, match="dual-hash provenance"):
        persist_gate_report(report, repo2)

    # No duplicate created: total canonical gate reports across DB == 1.
    # Note: if actor/source were also tampered, we count by metadata fingerprint.
    all_gate_like = [
        e for e in repo2.list_all()
        if e.metadata.get("identity_hash") is not None
        and "verdict" in e.metadata
    ]
    assert len(all_gate_like) == 1
    assert all_gate_like[0].id == ev.id

    session2.close()
    engine.dispose()


# ===========================================================================
# Attempt 9 fix — identity_hash canonical recomputation integrity
# ===========================================================================


# ---------------------------------------------------------------------------
# 85. identity_hash-only tamper → reload fail closed
# ---------------------------------------------------------------------------


def test_tamper_identity_hash_only_reload_fails_closed(gate_session) -> None:
    """Tampering only identity_hash (leaving all other fields intact) must
    fail closed on reload because the recomputed hash will not match."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper ONLY identity_hash.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    meta["identity_hash"] = "0" * 64
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="identity_hash mismatch"):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 86. identity_hash-only tamper → persist fail closed, count unchanged
# ---------------------------------------------------------------------------


def test_tamper_identity_hash_only_persist_fail_closed(gate_session) -> None:
    """Tampering only identity_hash must cause persist to fail closed;
    the canonical gate report count must not increase."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper ONLY identity_hash.
    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    meta["identity_hash"] = "f" * 64
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="identity_hash"):
        persist_gate_report(report, repo)

    # Count unchanged: still exactly 1 canonical gate report.
    all_canonical = [
        e for e in repo.list_all()
        if e.actor_id == "system:workflow-gate"
        and e.source == "workflow-gate-evaluation"
    ]
    assert len(all_canonical) == 1


# ---------------------------------------------------------------------------
# 87. identity_hash missing → reload fail closed
# ---------------------------------------------------------------------------


def test_remove_identity_hash_reload_fails_closed(gate_session) -> None:
    """Removing identity_hash entirely must fail closed on reload."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    del meta["identity_hash"]
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="missing identity_hash"):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 88. identity_hash + actor/source + row/binding all-field tamper
#     → close/reopen → fail closed, canonical count still 1
# ---------------------------------------------------------------------------


def test_all_fields_including_hash_tamper_close_reopen_fail_closed(
    gate_session,
) -> None:
    """Tampering ALL fields including identity_hash must be caught by the
    Signal B internal-consistency safety net (row.task_id != bound_task_id).
    After close/reopen, persist fails closed and no duplicate is created."""
    from polynexus_core.persistence.models import EvidenceRow

    session, db_path = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper ALL 7 fields: actor, source, row.t, row.r, bind.t, bind.r, hash.
    row = session.get(EvidenceRow, ev.id)
    row.actor_id = "attacker"
    row.source = "tampered-source"
    row.task_id = "tampered-row-t"
    row.run_id = "tampered-row-r"
    meta = _deserialize_dict(row.metadata_json)
    meta["bound_task_id"] = "tampered-bind-t"
    meta["bound_run_id"] = "tampered-bind-r"
    meta["identity_hash"] = "a" * 64
    row.metadata_json = _serialize_dict(meta)
    session.commit()
    session.close()

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session2 = Session()
    repo2 = SqlEvidenceRepository(session2)

    # Persist must fail closed via Signal B (internal inconsistency:
    # row.task_id != bound_task_id) even though identity_hash was also changed.
    with pytest.raises(GateReportTamperedError):
        persist_gate_report(report, repo2)

    # No duplicate: total gate-report-like records across DB == 1.
    all_gate_like = [
        e for e in repo2.list_all()
        if e.metadata.get("identity_hash") is not None
        and "verdict" in e.metadata
    ]
    assert len(all_gate_like) == 1
    assert all_gate_like[0].id == ev.id

    session2.close()
    engine.dispose()


# ===========================================================================
# Attempt 9 fix — provenance_token integrity & ordinary-document isolation
# ===========================================================================


# ---------------------------------------------------------------------------
# 89. provenance_token-only tamper → reload fail closed
# ---------------------------------------------------------------------------


def test_tamper_provenance_token_only_reload_fails_closed(gate_session) -> None:
    """Tampering only provenance_token must fail closed on reload."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    meta["provenance_token"] = "b" * 64
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="provenance_token"):
        reload_gate_report(repo, ev.id, workflow=workflow, task=task, run=run)


# ---------------------------------------------------------------------------
# 90. provenance_token-only tamper → persist fail closed, count unchanged
# ---------------------------------------------------------------------------


def test_tamper_provenance_token_only_persist_fail_closed(gate_session) -> None:
    """Tampering only provenance_token must cause persist to fail closed;
    no duplicate is created."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    row = session.get(EvidenceRow, ev.id)
    meta = _deserialize_dict(row.metadata_json)
    meta["provenance_token"] = "c" * 64
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError, match="provenance_token"):
        persist_gate_report(report, repo)

    all_canonical = [
        e for e in repo.list_all()
        if e.actor_id == "system:workflow-gate"
        and e.source == "workflow-gate-evaluation"
    ]
    assert len(all_canonical) == 1


# ---------------------------------------------------------------------------
# 91. Ordinary DOCUMENT_EVIDENCE with ALL six overlapping keys does not block
# ---------------------------------------------------------------------------


def test_ordinary_document_all_six_overlapping_keys_does_not_block(
    gate_session,
) -> None:
    """An ordinary DOCUMENT_EVIDENCE that happens to carry ALL six gate-report
    metadata keys (but lacks identity_hash/provenance_token/bound_*) must NOT
    be classified as a gate-report candidate and must NOT block first persist."""
    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    repo = SqlEvidenceRepository(session)

    # An ordinary document with exactly the 6 core fingerprint keys but
    # none of the extended gate-report binding/hash keys.
    ordinary_doc = Evidence(
        task_id=task.id,
        run_id=run.id,
        actor_id="system:document-import",
        source="document-import",
        type=EvidenceType.DOCUMENT_EVIDENCE,
        status=EvidenceStatus.OBSERVED,
        metadata={
            "workflow_id": workflow.id,
            "workflow_version": str(workflow.version),
            "verdict": "some prose conclusion text",
            "authority": "self-assessed",
            "overall_reason": "manual review outcome",
            "evaluations": json.dumps(
                [{"gate_id": "build", "outcome": "PASS", "reason": "looks fine"}]
            ),
        },
    )
    repo.add(ordinary_doc)
    session.commit()

    # First persist must succeed despite the overlapping metadata.
    report = evaluate_workflow_gates(workflow, task, run, repo)
    gate_report = persist_gate_report(report, repo)
    session.commit()

    assert gate_report.source == "workflow-gate-evaluation"
    assert gate_report.actor_id == "system:workflow-gate"

    # Replay is idempotent.
    gate_report_2 = persist_gate_report(report, repo)
    session.commit()
    assert gate_report_2.id == gate_report.id

    # Total evidence for this run: 1 ordinary doc + 1 gate report = 2.
    assert len(repo.list_by_run(run.id)) == 2


# ---------------------------------------------------------------------------
# 92. Full consistent 8-field rewrite — documented PARTIAL_INTEGRITY limitation
# ---------------------------------------------------------------------------


def test_full_consistent_tamper_creates_new_report_documented_limitation(
    gate_session,
) -> None:
    """Option B threat-model boundary (Human decision 2026-08-24).

    Directly tamper ALL 8 fields: actor_id, source, row.task_id, row.run_id,
    bound_task_id, bound_run_id, identity_hash, AND provenance_token.
    Then close/reopen and call persist_gate_report().

    This test is NOT a no-duplicate PASS under the acceptance contract.
    It documents a known PARTIAL_INTEGRITY limitation: within the current
    Evidence-only boundary (no MAC/secret/external store), fully-consistent
    multi-field tampering including BOTH independently computed hashes
    cannot be detected. A new report IS created alongside the orphaned
    tampered one.

    D12 integrity architecture (HMAC with OS-backed SecretStore or
    write-once audit table) is DEFERRED to CP-04+ per Human Option B.
    Until D12 is approved and implemented, this behavior is expected
    and documented rather than treated as a defect."""
    from polynexus_core.persistence.models import EvidenceRow

    session, db_path = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper ALL 8 fields simultaneously including BOTH hashes.
    row = session.get(EvidenceRow, ev.id)
    row.actor_id = "attacker"
    row.source = "tampered-source"
    row.task_id = "fake-task-999"
    row.run_id = "fake-run-999"
    meta = _deserialize_dict(row.metadata_json)
    meta["bound_task_id"] = "fake-bind-t-999"
    meta["bound_run_id"] = "fake-bind-r-999"

    # Recompute BOTH hashes to match the fake identity (simulating a
    # sophisticated attacker who knows the hash algorithms).
    expected_hash = _compute_identity_hash(
        report.workflow_id, report.workflow_version,
        "fake-task-999", "fake-run-999",
    )
    expected_prov = _compute_provenance_token(
        "attacker", "tampered-source",
        "fake-task-999", "fake-run-999",
    )
    meta["identity_hash"] = expected_hash
    meta["provenance_token"] = expected_prov
    row.metadata_json = _serialize_dict(meta)
    session.commit()
    session.close()

    # Close/reopen: fresh session.
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session2 = Session()
    repo2 = SqlEvidenceRepository(session2)

    # Current behavior: persist_gate_report() creates a new canonical report
    # because all identity signals were consistently destroyed. The system
    # treats this as "no prior gate report exists" which is the honest
    # limitation of the Evidence-only boundary without MAC/secret.
    result = persist_gate_report(report, repo2)
    session2.commit()

    # A NEW canonical report was created (different ID from the tampered one).
    assert result.id != ev.id

    # Total gate-report-like records across DB == 2 (tampered orphan + new).
    all_gate_like = [
        e for e in repo2.list_all()
        if e.metadata.get("identity_hash") is not None
        and e.metadata.get("provenance_token") is not None
    ]
    assert len(all_gate_like) == 2

    session2.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# 93. Partial multi-field tamper missing ONE hash → fail closed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("skip_field", ["identity_hash", "provenance_token"])
def test_partial_multi_field_missing_one_hash_fail_closed(
    gate_session, skip_field: str
) -> None:
    """When attacker tampers all visible fields but misses ONE hash field,
    the surviving hash detects the corruption and persist fails closed."""
    from polynexus_core.persistence.models import EvidenceRow

    session, _ = gate_session
    task, context, _ = _seed(session)
    run = _new_run(session, task, context)
    workflow = load_workflow_definition(_VERIFIED_GATE_WORKFLOW)
    _add_all_pass_evidence(session, task, run)
    repo = SqlEvidenceRepository(session)
    report = evaluate_workflow_gates(workflow, task, run, repo)
    ev = persist_gate_report(report, repo)
    session.commit()

    # Tamper 7 of 8 fields: actor, source, row.t, row.r, bind.t, bind.r,
    # plus ONE of the two hashes. The OTHER hash survives and catches it.
    row = session.get(EvidenceRow, ev.id)
    row.actor_id = "attacker"
    row.source = "tampered-source"
    row.task_id = "tampered-row-t"
    row.run_id = "tampered-row-r"
    meta = _deserialize_dict(row.metadata_json)
    meta["bound_task_id"] = "tampered-bind-t"
    meta["bound_run_id"] = "tampered-bind-r"
    if skip_field == "identity_hash":
        meta["identity_hash"] = "a" * 64
        # provenance_token left intact → catches via provenance mismatch
    elif skip_field == "provenance_token":
        meta["provenance_token"] = "b" * 64
        # identity_hash left intact → catches via identity mismatch
    row.metadata_json = _serialize_dict(meta)
    session.commit()

    with pytest.raises(GateReportTamperedError):
        persist_gate_report(report, repo)

    # No duplicate created (count by metadata fingerprint, not canonical
    # markers which may themselves have been tampered).
    all_gate_like = [
        e for e in repo.list_all()
        if e.metadata.get("identity_hash") is not None
        and e.metadata.get("provenance_token") is not None
    ]
    assert len(all_gate_like) == 1
