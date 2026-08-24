"""WP-13 deterministic workflow hard-gate evaluation.

Evaluates ``EVIDENCE_CHECK`` and ``HUMAN_GATE`` steps from a canonical
``WorkflowDefinition`` against actual persisted ``Evidence`` scoped to the current
Task/Run. The result is a truthful, reloadable verdict that never fabricates a
Finding, Evidence, Artifact, consensus, or implicit Human approval.

Implemented additively over existing Task/Run/Evidence boundaries. No new persisted
model, migration, REST endpoint, RunState, WorkMode, or EvidenceType is introduced;
the verdict is computed from existing ``EvidenceType``/``EvidenceStatus`` values and
stored durably as a ``DOCUMENT_EVIDENCE`` evaluation record (same durable boundary
used by the Council plan).

Gate semantics (D11 Option C for HUMAN_GATE)
--------------------------------------------
- A required hard gate is satisfied only by ``TOOL_EVIDENCE`` with explicit ``PASS``
  and a ``gate`` metadata key matching the configured gate id. ``AI_OPINION``,
  ``RUNTIME_EVIDENCE``, prose, participant consensus, or synthesis text never
  satisfy a deterministic gate.
- Missing, malformed, stale, cross-task, cross-project, or cross-run evidence
  produces a non-PASS outcome (``NEED_ACTION``), not a fabricated PASS.
- An explicit ``FAIL`` tool evidence blocks PASS and cannot be overridden.
  For the same gate id, explicit FAIL always takes precedence over PASS.
- ``FAILED``/``TIMED_OUT``/``CANCELLED``/``ORPHANED`` terminal Run states cannot
  produce a PASS/VERIFIED verdict.
- Task/Run/workflow identity and workflow version must be consistent; run.task_id
  must equal task.id.
- Hard gates require ``command`` (non-empty, non-whitespace string) and
  ``exit_code`` metadata; missing, malformed, or non-zero exit_code evidence
  produces ``NEED_ACTION`` or ``FAIL``.
- ``HUMAN_GATE`` cannot auto-pass (D11 Option C). No actor_id string pattern,
  deny-list, prefix, or metadata field proves Human identity. The existing
  Evidence.actor_id is an arbitrary string boundary. Without an approved identity
  boundary, HUMAN_EVIDENCE with ``decision=approve`` or ``decision=reject``
  produces ``HUMAN_DECISION`` (pending); neither value is a verified decision.
- A ``VERIFIED``/PASS verdict is legal only after every required deterministic hard
  gate passes and every configured Human gate is explicitly approved. The authority
  is derived purely from the workflow ``assurance`` mode and the gate outcomes; it
  never implies Human approval that did not occur.
- ``persist_gate_report`` is idempotent and writes durable metadata updates via
  the persistence boundary. ``reload_gate_report`` re-validates stored metadata
  against actual persisted evidence and fails closed on tamper.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping, Sequence

from polynexus_core.domain.enums import (
    AssuranceMode,
    EvidenceStatus,
    EvidenceType,
    RunState,
)
from polynexus_core.domain.models import Evidence, Run, Task
from polynexus_core.persistence.repository import EvidenceRepository
from polynexus_core.workflows.models import WorkflowDefinition


class GateKind(StrEnum):
    EVIDENCE_CHECK = "EVIDENCE_CHECK"
    HUMAN_GATE = "HUMAN_GATE"


class GateOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    NEED_ACTION = "NEED_ACTION"
    HUMAN_DECISION = "HUMAN_DECISION"


class WorkflowGateConfigError(ValueError):
    """Raised when a workflow's gate configuration fails closed before evaluation."""


class WorkflowIdentityError(ValueError):
    """Raised when Task/Run/workflow identity or version is inconsistent."""


class GateReportTamperedError(ValueError):
    """Raised when a reloaded gate report metadata does not match persisted evidence."""


# Fixed V1 node types per ADR-009.
_KNOWN_STEP_TYPES = {
    "CONTEXT",
    "AI_TASK",
    "PARALLEL_AI",
    "CROSS_REVIEW",
    "TOOL",
    "EVIDENCE_CHECK",
    "HUMAN_GATE",
    "SYNTHESIS",
    "CONDITION",
}

# Metadata keys used by deterministic gate evidence.
_GATE_METADATA_KEY = "gate"
_HUMAN_GATE_METADATA_KEY = "human_gate"
_HUMAN_DECISION_METADATA_KEY = "decision"

_GATE_SOURCE = "workflow-gate-evaluation"
_GATE_ACTOR = "system:workflow-gate"
# All keys that must be simultaneously present for a metadata-only fingerprint
# to classify a record as a gate-report candidate (when actor and source are
# both tampered).  Requiring the full set prevents ordinary documents with
# overlapping partial metadata from blocking first persist.
_GATE_REPORT_ALL_METADATA_KEYS: frozenset[str] = frozenset(
    {"workflow_id", "workflow_version", "verdict", "authority",
     "overall_reason", "evaluations"}
)
# Extended keys written only by persist_gate_report(); their presence
# distinguishes a true gate report from an ordinary document that happens
# to carry workflow/verdict-like metadata.
_GATE_EXTENDED_METADATA_KEYS: frozenset[str] = frozenset(
    {"bound_task_id", "bound_run_id", "identity_hash", "provenance_token"}
)

# Terminal Run states that block a PASS/VERIFIED verdict.
_TERMINAL_FAILED_STATES: frozenset[RunState] = frozenset(
    {RunState.FAILED, RunState.TIMED_OUT, RunState.CANCELLED, RunState.ORPHANED}
)

# Hard gate metadata keys required for a valid PASS.
_REQUIRED_HARD_GATE_KEYS: frozenset[str] = frozenset({"command", "exit_code"})

# Valid authority values for the supported assurance modes.
_VALID_AUTHORITY_VALUES: frozenset[str] = frozenset(
    {"verified-deterministic", "standard-deterministic", "none"}
)


# ---------------------------------------------------------------------------
# Configuration validation (fail closed before evaluation)
# ---------------------------------------------------------------------------


def validate_workflow_gates(workflow: WorkflowDefinition) -> list[str]:
    """Return a list of configuration errors; empty list means valid.

    Validates: known node types, unique step ids, resolvable depends_on,
    non-empty unique ``hard_gates`` per EVIDENCE_CHECK, and a valid ``human_gate``
    id per HUMAN_GATE.
    """
    errors: list[str] = []
    seen_step_ids: set[str] = set()
    seen_evidence_gates: set[str] = set()
    seen_human_gates: set[str] = set()
    step_ids = {s.id for s in workflow.steps}

    for step in workflow.steps:
        if step.type not in _KNOWN_STEP_TYPES:
            errors.append(f"unsupported node type {step.type!r} in step {step.id!r}")
        if step.id in seen_step_ids:
            errors.append(f"duplicate step id {step.id!r}")
        seen_step_ids.add(step.id)
        for dep in step.depends_on:
            if dep not in step_ids:
                errors.append(f"step {step.id!r} depends on unknown step {dep!r}")

        if step.type == GateKind.EVIDENCE_CHECK.value:
            gates = step.parameters.get("hard_gates")
            if not isinstance(gates, list) or not gates:
                errors.append(
                    f"EVIDENCE_CHECK step {step.id!r} requires a non-empty hard_gates list"
                )
            else:
                for gate_id in gates:
                    if not isinstance(gate_id, str) or not gate_id.strip():
                        errors.append(
                            f"EVIDENCE_CHECK step {step.id!r} has an invalid gate id {gate_id!r}"
                        )
                    elif gate_id in seen_evidence_gates:
                        errors.append(f"duplicate hard gate id {gate_id!r}")
                    else:
                        seen_evidence_gates.add(gate_id)
        elif step.type == GateKind.HUMAN_GATE.value:
            gate_id = step.parameters.get(_HUMAN_GATE_METADATA_KEY, step.id)
            if not isinstance(gate_id, str) or not gate_id.strip():
                errors.append(
                    f"HUMAN_GATE step {step.id!r} requires a valid human_gate id"
                )
            elif gate_id in seen_human_gates:
                errors.append(f"duplicate HUMAN_GATE id {gate_id!r}")
            else:
                seen_human_gates.add(gate_id)

    return errors


# ---------------------------------------------------------------------------
# Evaluation records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GateEvaluation:
    gate_id: str
    step_id: str
    kind: GateKind
    outcome: GateOutcome
    reason: str
    satisfied_by: str | None
    required_evidence_ids: tuple[str, ...] = ()

    def to_mapping(self) -> dict[str, object]:
        return {
            "gate_id": self.gate_id,
            "step_id": self.step_id,
            "kind": self.kind.value,
            "outcome": self.outcome.value,
            "reason": self.reason,
            "satisfied_by": self.satisfied_by,
            "required_evidence_ids": list(self.required_evidence_ids),
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "GateEvaluation":
        return cls(
            gate_id=str(data["gate_id"]),
            step_id=str(data["step_id"]),
            kind=GateKind(str(data["kind"])),
            outcome=GateOutcome(str(data["outcome"])),
            reason=str(data["reason"]),
            satisfied_by=data.get("satisfied_by"),
            required_evidence_ids=tuple(data.get("required_evidence_ids", ())),
        )


@dataclass(frozen=True)
class WorkflowGateReport:
    workflow_id: str
    workflow_version: int
    task_id: str
    run_id: str
    evaluations: tuple[GateEvaluation, ...]
    verdict: GateOutcome
    authority: str
    overall_reason: str

    def to_json(self) -> str:
        return json.dumps(
            {
                "workflow_id": self.workflow_id,
                "workflow_version": self.workflow_version,
                "task_id": self.task_id,
                "run_id": self.run_id,
                "evaluations": [e.to_mapping() for e in self.evaluations],
                "verdict": self.verdict.value,
                "authority": self.authority,
                "overall_reason": self.overall_reason,
            },
            sort_keys=True,
        )

    @classmethod
    def from_json(cls, text: str) -> "WorkflowGateReport":
        data = json.loads(text)
        return cls(
            workflow_id=str(data["workflow_id"]),
            workflow_version=int(data["workflow_version"]),
            task_id=str(data["task_id"]),
            run_id=str(data["run_id"]),
            evaluations=tuple(
                GateEvaluation.from_mapping(e) for e in data["evaluations"]
            ),
            verdict=GateOutcome(str(data["verdict"])),
            authority=str(data["authority"]),
            overall_reason=str(data["overall_reason"]),
        )


# ---------------------------------------------------------------------------
# Deterministic evaluation
# ---------------------------------------------------------------------------


def _scope_evidence(
    task: Task, run: Run, evidence_repo: EvidenceRepository,
    exclude_id: str | None = None,
) -> list[Evidence]:
    """Evidence scoped to the current Task and Run.

    Rejects cross-task/cross-run evidence. When ``exclude_id`` is provided,
    the specified evidence record is excluded (used to prevent gate report
    self-reference during re-evaluation).
    """
    return [
        e
        for e in evidence_repo.list_by_run(run.id)
        if e.task_id == task.id and e.run_id == run.id and e.id != exclude_id
    ]


def _require_valid_command(metadata: dict[str, object], gate_id: str) -> str | None:
    """Validate command metadata for a hard gate; returns error reason or None."""
    command = metadata.get("command")
    if command is None or not isinstance(command, str) or not command.strip():
        return f"hard gate {gate_id!r}: command must be a non-empty non-whitespace string"
    return None


def _evaluate_evidence_gate(
    gate_id: str, step_id: str, evidence: Sequence[Evidence]
) -> GateEvaluation:
    """Evaluate a deterministic hard gate.

    FAIL always takes precedence over PASS for the same gate id. Hard gate
    evidence must include a non-empty ``command`` and valid ``exit_code``
    metadata; missing or malformed metadata prevents a PASS outcome.
    """
    gate_evidence = [
        e
        for e in evidence
        if e.type is EvidenceType.TOOL_EVIDENCE
        and e.metadata.get(_GATE_METADATA_KEY) == gate_id
    ]

    failing = [e for e in gate_evidence if e.status is EvidenceStatus.FAIL]
    passing = [e for e in gate_evidence if e.status is EvidenceStatus.PASS]

    # Explicit FAIL always wins — cannot be overridden by PASS or AI opinion.
    if failing:
        chosen = max(failing, key=lambda e: e.observed_at)
        return GateEvaluation(
            gate_id=gate_id,
            step_id=step_id,
            kind=GateKind.EVIDENCE_CHECK,
            outcome=GateOutcome.FAIL,
            reason="required deterministic tool evidence present but failed; "
            "explicit FAIL cannot be overridden",
            satisfied_by=chosen.id,
            required_evidence_ids=(chosen.id,),
        )

    if passing:
        chosen = max(passing, key=lambda e: e.observed_at)
        metadata = chosen.metadata

        missing_keys = _REQUIRED_HARD_GATE_KEYS - set(metadata.keys())
        if missing_keys:
            return GateEvaluation(
                gate_id=gate_id,
                step_id=step_id,
                kind=GateKind.EVIDENCE_CHECK,
                outcome=GateOutcome.NEED_ACTION,
                reason=(
                    f"hard gate evidence missing required metadata keys: "
                    f"{', '.join(sorted(missing_keys))}"
                ),
                satisfied_by=None,
                required_evidence_ids=(),
            )

        cmd_error = _require_valid_command(metadata, gate_id)
        if cmd_error:
            return GateEvaluation(
                gate_id=gate_id,
                step_id=step_id,
                kind=GateKind.EVIDENCE_CHECK,
                outcome=GateOutcome.NEED_ACTION,
                reason=cmd_error,
                satisfied_by=None,
                required_evidence_ids=(),
            )

        exit_code = metadata.get("exit_code")
        if exit_code is None or str(exit_code) != "0":
            return GateEvaluation(
                gate_id=gate_id,
                step_id=step_id,
                kind=GateKind.EVIDENCE_CHECK,
                outcome=GateOutcome.NEED_ACTION,
                reason=(
                    f"hard gate evidence exit_code is not '0': {exit_code!r}"
                ),
                satisfied_by=None,
                required_evidence_ids=(),
            )
        return GateEvaluation(
            gate_id=gate_id,
            step_id=step_id,
            kind=GateKind.EVIDENCE_CHECK,
            outcome=GateOutcome.PASS,
            reason="satisfied by deterministic TOOL_EVIDENCE with PASS and "
            "valid command/exit metadata",
            satisfied_by=chosen.id,
            required_evidence_ids=(chosen.id,),
        )

    return GateEvaluation(
        gate_id=gate_id,
        step_id=step_id,
        kind=GateKind.EVIDENCE_CHECK,
        outcome=GateOutcome.NEED_ACTION,
        reason="required deterministic tool evidence missing/unverified",
        satisfied_by=None,
        required_evidence_ids=(),
    )


def _evaluate_human_gate(
    gate_id: str, step_id: str, evidence: Sequence[Evidence]
) -> GateEvaluation:
    """Evaluate a human gate under D11 Option C.

    Under Option C, no actor_id string pattern proves Human identity.
    The existing Evidence.actor_id is an arbitrary string boundary without
    an approved identity mapping.

    - ``decision=reject`` with any actor → HUMAN_DECISION (unverified)
    - ``decision=approve`` with any actor → HUMAN_DECISION (pending; no verified boundary)
    - No matching evidence → HUMAN_DECISION (pending)
    - Wrong status, ambiguous decision → HUMAN_DECISION (pending)
    """
    decisions = [
        e
        for e in evidence
        if e.type is EvidenceType.HUMAN_EVIDENCE
        and e.metadata.get(_HUMAN_GATE_METADATA_KEY) == gate_id
    ]
    if not decisions:
        return GateEvaluation(
            gate_id=gate_id,
            step_id=step_id,
            kind=GateKind.HUMAN_GATE,
            outcome=GateOutcome.HUMAN_DECISION,
            reason="human gate pending; no explicit decision evidence",
            satisfied_by=None,
            required_evidence_ids=(),
        )

    decided = max(decisions, key=lambda e: e.observed_at)

    # Validate HUMAN_EVIDENCE status is HUMAN_DECISION.
    if decided.status is not EvidenceStatus.HUMAN_DECISION:
        return GateEvaluation(
            gate_id=gate_id,
            step_id=step_id,
            kind=GateKind.HUMAN_GATE,
            outcome=GateOutcome.HUMAN_DECISION,
            reason=(
                f"human evidence has status {decided.status.value!r} "
                f"instead of HUMAN_DECISION; cannot auto-pass"
            ),
            satisfied_by=None,
            required_evidence_ids=(),
        )

    # D11 Option C: every decision remains unverified. No actor_id string,
    # prefix, or pattern proves Human identity. Without an approved identity
    # boundary, neither approve nor reject can become a verified decision.
    return GateEvaluation(
        gate_id=gate_id,
        step_id=step_id,
        kind=GateKind.HUMAN_GATE,
        outcome=GateOutcome.HUMAN_DECISION,
        reason=(
            "human gate pending; D11 Option C: no approved identity boundary "
            "exists to verify actor attribution; cannot auto-pass"
        ),
        satisfied_by=decided.id,
        required_evidence_ids=(decided.id,),
    )


def _compute_verdict(
    workflow: WorkflowDefinition, evaluations: Sequence[GateEvaluation]
) -> tuple[GateOutcome, str, str]:
    failed = [e for e in evaluations if e.outcome is GateOutcome.FAIL]
    need_action = [e for e in evaluations if e.outcome is GateOutcome.NEED_ACTION]
    human_evals = [e for e in evaluations if e.kind is GateKind.HUMAN_GATE]
    human_pending = [e for e in human_evals if e.outcome is GateOutcome.HUMAN_DECISION]

    if failed:
        return (
            GateOutcome.FAIL,
            "none",
            "one or more required deterministic gates failed; "
            "verdict cannot be PASS/VERIFIED",
        )
    if need_action:
        return (
            GateOutcome.NEED_ACTION,
            "none",
            "one or more required gates missing/unverified; "
            "verdict cannot be PASS/VERIFIED",
        )
    if human_evals and human_pending:
        return (
            GateOutcome.HUMAN_DECISION,
            "none",
            "human gate pending; explicit decision required before progression",
        )

    authority = (
        "verified-deterministic"
        if workflow.assurance is AssuranceMode.VERIFIED
        else "standard-deterministic"
    )
    return (
        GateOutcome.PASS,
        authority,
        "all required deterministic gates passed and human gates approved",
    )


def evaluate_workflow_gates(
    workflow: WorkflowDefinition,
    task: Task,
    run: Run,
    evidence_repo: EvidenceRepository,
    exclude_evidence_id: str | None = None,
) -> WorkflowGateReport:
    """Evaluate all EVIDENCE_CHECK/HUMAN_GATE steps for the run; fail closed on bad config.

    Validates Task/Run/workflow identity and version before evaluation.
    Validates run.task_id == task.id.
    Terminal Runs (FAILED/TIMED_OUT/CANCELLED/ORPHANED) cannot produce a
    PASS/VERIFIED verdict.
    """
    config_errors = validate_workflow_gates(workflow)
    if config_errors:
        raise WorkflowGateConfigError("; ".join(config_errors))

    # Validate Task/Run/workflow identity and version.
    if task.workflow_id != workflow.id:
        raise WorkflowIdentityError(
            f"task workflow_id {task.workflow_id!r} does not match "
            f"workflow id {workflow.id!r}"
        )
    if task.workflow_version != workflow.version:
        raise WorkflowIdentityError(
            f"task workflow_version {task.workflow_version} does not match "
            f"workflow version {workflow.version}"
        )
    if run.workflow_id != workflow.id:
        raise WorkflowIdentityError(
            f"run.workflow_id {run.workflow_id!r} does not match "
            f"workflow id {workflow.id!r}"
        )
    if run.workflow_version != workflow.version:
        raise WorkflowIdentityError(
            f"run.workflow_version {run.workflow_version} does not match "
            f"workflow version {workflow.version}"
        )
    if run.task_id != task.id:
        raise WorkflowIdentityError(
            f"run.task_id {run.task_id!r} does not match task.id {task.id!r}"
        )

    # Terminal Run states block PASS/VERIFIED.
    if run.state in _TERMINAL_FAILED_STATES:
        return WorkflowGateReport(
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            task_id=task.id,
            run_id=run.id,
            evaluations=(),
            verdict=GateOutcome.FAIL,
            authority="none",
            overall_reason=(
                f"run state {run.state.value!r} is terminal and cannot "
                f"produce a PASS/VERIFIED verdict"
            ),
        )

    evidence = _scope_evidence(
        task, run, evidence_repo, exclude_id=exclude_evidence_id
    )
    evaluations: list[GateEvaluation] = []
    for step in workflow.steps:
        if step.type == GateKind.EVIDENCE_CHECK.value:
            for gate_id in step.parameters.get("hard_gates", []):
                evaluations.append(_evaluate_evidence_gate(gate_id, step.id, evidence))
        elif step.type == GateKind.HUMAN_GATE.value:
            gate_id = step.parameters.get(_HUMAN_GATE_METADATA_KEY, step.id)
            evaluations.append(_evaluate_human_gate(gate_id, step.id, evidence))

    verdict, authority, overall_reason = _compute_verdict(workflow, evaluations)
    return WorkflowGateReport(
        workflow_id=workflow.id,
        workflow_version=workflow.version,
        task_id=task.id,
        run_id=run.id,
        evaluations=tuple(evaluations),
        verdict=verdict,
        authority=authority,
        overall_reason=overall_reason,
    )


# ---------------------------------------------------------------------------
# Durable persistence (accepted Evidence boundary; not a new model/table)
# ---------------------------------------------------------------------------


def _is_gate_report_candidate(evidence: Evidence) -> bool:
    """Recognize canonical or partially corrupted gate-report evidence.

    Actor and source are independent canonical markers — either alone is
    sufficient.  If both have been tampered, a full metadata fingerprint
    (ALL gate-report payload keys AND at least one extended provenance key)
    identifies the record.  Requiring an extended key avoids treating an
    ordinary document that happens to carry the core workflow/verdict keys
    as a gate report.
    Evidence type is not a discriminator because it is itself tamperable.
    """
    if evidence.actor_id == _GATE_ACTOR or evidence.source == _GATE_SOURCE:
        return True

    metadata_keys = set(evidence.metadata)
    return (
        _GATE_REPORT_ALL_METADATA_KEYS.issubset(metadata_keys)
        and bool(metadata_keys & _GATE_EXTENDED_METADATA_KEYS)
    )


def _is_bound_to(report: WorkflowGateReport, evidence: Evidence) -> bool:
    """Check whether evidence metadata binds to the target task/run identity."""
    return (
        evidence.metadata.get("workflow_id") == report.workflow_id
        and evidence.metadata.get("workflow_version") == str(report.workflow_version)
        and evidence.metadata.get("bound_task_id") == report.task_id
        and evidence.metadata.get("bound_run_id") == report.run_id
    )


def _compute_identity_hash(
    workflow_id: str, workflow_version: int, task_id: str, run_id: str
) -> str:
    """Compute a deterministic per-report identity fingerprint.

    Covers workflow/task/run binding only.  Changing actor_id or source does
    NOT affect this hash; changing task/run/workflow DOES.
    """
    payload = json.dumps(
        {"wid": workflow_id, "wv": workflow_version, "tid": task_id, "rid": run_id},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _compute_provenance_token(
    actor_id: str, source: str, task_id: str, run_id: str
) -> str:
    """Compute an independent provenance token over the actor/source/binding.

    Covers canonical attribution and task/run binding but NOT workflow
    identity.  Changing workflow_id/version does NOT affect this token;
    changing actor_id, source, task_id, or run_id DOES.
    """
    payload = json.dumps(
        {"aid": actor_id, "src": source, "tid": task_id, "rid": run_id},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def persist_gate_report(
    report: WorkflowGateReport, evidence_repo: EvidenceRepository
) -> Evidence:
    """Persist the gate report as a DOCUMENT_EVIDENCE evaluation record.

    Identity matching uses a two-phase strategy:

    Phase 1 — Scoped lookup with run-level disambiguation: search by run_id
    and task_id, then filter so only records bound to *this* task/run pair
    are considered. This correctly handles multiple runs under the same task.

    Phase 2 — Metadata-bound global scan: only when Phase 1 finds nothing,
    scan all evidence for records whose durable metadata binding matches
    this report but whose row-level IDs have been tampered.

    Different task/run pairs are naturally isolated because their metadata
    bindings reference different identities.
    """
    # Phase 1: Scoped lookup by run_id and/or task_id.
    by_run = evidence_repo.list_by_run(report.run_id)
    by_task = evidence_repo.list_by_task(report.task_id)
    seen_ids: set[str] = set()
    scoped: list[Evidence] = []
    for ev in by_run:
        if ev.id not in seen_ids:
            seen_ids.add(ev.id)
            scoped.append(ev)
    for ev in by_task:
        if ev.id not in seen_ids:
            seen_ids.add(ev.id)
            scoped.append(ev)

    # Filter to gate-report candidates belonging to THIS specific task/run.
    # A record is a match if its row-level IDs match OR its durable metadata
    # binding matches. This prevents cross-run contamination when multiple
    # runs exist under the same task.
    candidates = [
        ev
        for ev in scoped
        if _is_gate_report_candidate(ev)
        and (
            (ev.task_id == report.task_id and ev.run_id == report.run_id)
            or (
                ev.metadata.get("bound_task_id") == report.task_id
                and ev.metadata.get("bound_run_id") == report.run_id
            )
        )
    ]

    # Phase 2: Metadata-bound global scan for combined task_id+run_id tamper.
    # Only entered when Phase 1 found no candidates, so legitimate reports
    # from other task/run pairs are never pulled into scope.
    if not candidates:
        all_evidence = evidence_repo.list_all()
        candidates = [
            ev
            for ev in all_evidence
            if _is_gate_report_candidate(ev)
            and _is_bound_to(report, ev)
            and ev.task_id != report.task_id
            and ev.run_id != report.run_id
        ]

    if len(candidates) > 1:
        raise GateReportTamperedError(
            f"multiple gate-report candidates exist for task/run; refusing replay"
        )
    if candidates:
        ev = candidates[0]
        if ev.actor_id != _GATE_ACTOR:
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} has corrupted actor_id; "
                f"refusing to create duplicate"
            )
        if ev.source != _GATE_SOURCE:
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} has corrupted source "
                f"{ev.source!r}; refusing to create duplicate"
            )
        if ev.type is not EvidenceType.DOCUMENT_EVIDENCE:
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} has corrupted type "
                f"{ev.type.value!r}; refusing to create duplicate"
            )
        # Validate durable binding metadata is present and matches.
        bound_task = ev.metadata.get("bound_task_id")
        bound_run = ev.metadata.get("bound_run_id")
        if bound_task is None or bound_run is None:
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} missing durable binding "
                f"metadata (bound_task_id/bound_run_id); refusing to create duplicate"
            )
        if bound_task != report.task_id:
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} has tampered binding "
                f"bound_task_id {bound_task!r}; refusing to create duplicate"
            )
        if bound_run != report.run_id:
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} has tampered binding "
                f"bound_run_id {bound_run!r}; refusing to create duplicate"
            )
        # Validate durable identity hash.
        stored_hash = ev.metadata.get("identity_hash")
        expected_hash = _compute_identity_hash(
            report.workflow_id, report.workflow_version,
            report.task_id, report.run_id,
        )
        if stored_hash is None:
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} missing identity_hash; "
                f"refusing to create duplicate"
            )
        if not isinstance(stored_hash, str) or len(stored_hash) != 64:
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} has malformed identity_hash "
                f"{stored_hash!r}; refusing to create duplicate"
            )
        if stored_hash != expected_hash:
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} identity_hash mismatch: "
                f"stored {stored_hash!r} does not match recomputed "
                f"{expected_hash!r}; refusing to create duplicate"
            )
        # Validate redundant provenance token.
        stored_prov = ev.metadata.get("provenance_token")
        expected_prov = _compute_provenance_token(
            _GATE_ACTOR, _GATE_SOURCE, report.task_id, report.run_id
        )
        if stored_prov is None:
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} missing provenance_token; "
                f"refusing to create duplicate"
            )
        if not isinstance(stored_prov, str) or len(stored_prov) != 64:
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} has malformed provenance_token "
                f"{stored_prov!r}; refusing to create duplicate"
            )
        if stored_prov != expected_prov:
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} provenance_token mismatch: "
                f"stored {stored_prov!r} does not match recomputed "
                f"{expected_prov!r}; refusing to create duplicate"
            )
        # Row-level task_id/run_id must match the canonical report identity.
        if ev.task_id != report.task_id:
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} has tampered row-level "
                f"task_id {ev.task_id!r}; refusing to create duplicate"
            )
        if ev.run_id != report.run_id:
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} has tampered row-level "
                f"run_id {ev.run_id!r}; refusing to create duplicate"
            )
        required_report_metadata = {
            "workflow_id",
            "workflow_version",
            "verdict",
            "authority",
            "overall_reason",
            "evaluations",
        }
        if not required_report_metadata.issubset(ev.metadata):
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} has missing identity metadata; "
                f"refusing to create duplicate"
            )
        raw_wv = ev.metadata.get("workflow_version")
        try:
            existing_wv = int(raw_wv)
        except (ValueError, TypeError):
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} has malformed "
                f"workflow_version metadata {raw_wv!r}; refusing to create duplicate"
            )
        if (
            ev.metadata.get("workflow_id") != report.workflow_id
            or existing_wv != report.workflow_version
        ):
            raise GateReportTamperedError(
                f"existing gate report {ev.id!r} has corrupted identity metadata; "
                f"refusing to create duplicate report"
            )
        updated = Evidence(
            id=ev.id,
            task_id=ev.task_id,
            run_id=ev.run_id,
            actor_id=ev.actor_id,
            source=ev.source,
            type=ev.type,
            status=ev.status,
            metadata={
                **ev.metadata,
                "verdict": report.verdict.value,
                "authority": report.authority,
                "overall_reason": report.overall_reason,
                "evaluations": json.dumps(
                    [e.to_mapping() for e in report.evaluations], sort_keys=True
                ),
            },
            observed_at=ev.observed_at,
        )
        evidence_repo.update(updated)
        return updated

    # Pre-creation integrity check — independent dual-hash provenance.
    #
    # Two genuinely independent hashes are stored at creation time:
    #   identity_hash     SHA-256(workflow_id, version, task_id, run_id)
    #   provenance_token  SHA-256(actor_id, source, task_id, run_id)
    #
    # They cover DISJOINT field sets: changing actor/source breaks only
    # provenance_token; changing workflow/task/run breaks only identity_hash;
    # changing both breaks both.  The attacker must recompute BOTH correctly
    # to avoid detection.  Detection is inherently task/run-scoped: different
    # tasks produce different hashes, so cross-task isolation is preserved.
    expected_hash = _compute_identity_hash(
        report.workflow_id, report.workflow_version, report.task_id, report.run_id
    )
    expected_prov = _compute_provenance_token(
        _GATE_ACTOR, _GATE_SOURCE, report.task_id, report.run_id
    )
    dual_hash_matches = [
        ev
        for ev in evidence_repo.list_all()
        if (
            ev.metadata.get("identity_hash") == expected_hash
            or ev.metadata.get("provenance_token") == expected_prov
        )
        and ev.metadata.get("workflow_id") == report.workflow_id
    ]
    if dual_hash_matches:
        raise GateReportTamperedError(
            f"existing gate report {dual_hash_matches[0].id!r} detected via "
            f"dual-hash provenance for task/run; refusing to create duplicate"
        )

    evidence = Evidence(
        task_id=report.task_id,
        run_id=report.run_id,
        actor_id=_GATE_ACTOR,
        source=_GATE_SOURCE,
        type=EvidenceType.DOCUMENT_EVIDENCE,
        status=EvidenceStatus.OBSERVED,
        metadata={
            "workflow_id": report.workflow_id,
            "workflow_version": str(report.workflow_version),
            "bound_task_id": report.task_id,
            "bound_run_id": report.run_id,
            "identity_hash": _compute_identity_hash(
                report.workflow_id, report.workflow_version,
                report.task_id, report.run_id,
            ),
            "provenance_token": _compute_provenance_token(
                _GATE_ACTOR, _GATE_SOURCE,
                report.task_id, report.run_id,
            ),
            "verdict": report.verdict.value,
            "authority": report.authority,
            "overall_reason": report.overall_reason,
            "evaluations": json.dumps(
                [e.to_mapping() for e in report.evaluations], sort_keys=True
            ),
        },
    )
    evidence_repo.add(evidence)
    return evidence


def reload_gate_report(
    evidence_repo: EvidenceRepository,
    evidence_id: str,
    workflow: WorkflowDefinition,
    task: Task,
    run: Run,
) -> WorkflowGateReport:
    """Reconstruct a persisted gate report from its Evidence record.

    Requires full canonical workflow/task/run context. Performs strict
    re-validation against actual persisted evidence:
    - Validates evidence type is DOCUMENT_EVIDENCE and source/status canonical
    - Validates workflow/task/run identity and version
    - Validates authority is correct for workflow assurance mode
    - Validates required_evidence_ids exist in task/run evidence
      (excluding the gate report itself to prevent self-reference)
    - Validates evaluation structure matches workflow exactly
    - Re-evaluates actual evidence (excluding gate report) and compares
      verdict, authority, overall_reason, and ALL evaluation fields

    Fails closed on any tamper detection.
    """
    ev = evidence_repo.get(evidence_id)
    if ev is None:
        raise ValueError(f"Gate report evidence {evidence_id!r} not found")

    # Validate evidence type, source, actor, and status.
    if ev.type is not EvidenceType.DOCUMENT_EVIDENCE:
        raise GateReportTamperedError(
            f"evidence {evidence_id!r} has type {ev.type.value!r}, "
            f"expected DOCUMENT_EVIDENCE"
        )
    if ev.source != _GATE_SOURCE:
        raise GateReportTamperedError(
            f"evidence {evidence_id!r} has source {ev.source!r}, "
            f"expected {_GATE_SOURCE!r}"
        )
    if ev.actor_id != _GATE_ACTOR:
        raise GateReportTamperedError(
            f"evidence {evidence_id!r} has actor_id {ev.actor_id!r}, "
            f"expected {_GATE_ACTOR!r}"
        )
    if ev.status is not EvidenceStatus.OBSERVED:
        raise GateReportTamperedError(
            f"evidence {evidence_id!r} has status {ev.status.value!r}, "
            f"expected OBSERVED"
        )
    m = ev.metadata
    evaluations = [
        GateEvaluation.from_mapping(x) for x in json.loads(m["evaluations"])
    ]
    stored_verdict = GateOutcome(str(m["verdict"]))
    stored_authority = str(m["authority"])
    stored_overall_reason = str(m["overall_reason"])

    stored_workflow_id = str(m["workflow_id"])
    stored_workflow_version = int(m["workflow_version"])

    # Validate workflow identity.
    if workflow.id != stored_workflow_id:
        raise GateReportTamperedError(
            f"gate report workflow_id {stored_workflow_id!r} "
            f"does not match current workflow {workflow.id!r}"
        )
    if workflow.version != stored_workflow_version:
        raise GateReportTamperedError(
            f"gate report workflow_version {stored_workflow_version} "
            f"does not match current workflow {workflow.version}"
        )

    # Validate task/run identity.
    if task.id != ev.task_id:
        raise GateReportTamperedError(
            f"gate report task_id {ev.task_id!r} does not match task {task.id!r}"
        )
    if run.id != ev.run_id:
        raise GateReportTamperedError(
            f"gate report run_id {ev.run_id!r} does not match run {run.id!r}"
        )

    # Validate durable binding metadata matches the current task/run identity.
    bound_task = m.get("bound_task_id")
    bound_run = m.get("bound_run_id")
    if bound_task is None or bound_run is None:
        raise GateReportTamperedError(
            f"gate report {evidence_id!r} missing durable binding metadata "
            f"(bound_task_id/bound_run_id); cannot verify provenance"
        )
    if bound_task != task.id:
        raise GateReportTamperedError(
            f"gate report {evidence_id!r} binding bound_task_id "
            f"{bound_task!r} does not match task {task.id!r}"
        )
    if bound_run != run.id:
        raise GateReportTamperedError(
            f"gate report {evidence_id!r} binding bound_run_id "
            f"{bound_run!r} does not match run {run.id!r}"
        )

    # Validate durable identity hash matches canonical recomputation.
    stored_hash = m.get("identity_hash")
    expected_hash = _compute_identity_hash(
        workflow.id, workflow.version, task.id, run.id
    )
    if stored_hash is None:
        raise GateReportTamperedError(
            f"gate report {evidence_id!r} missing identity_hash; "
            f"cannot verify provenance"
        )
    if not isinstance(stored_hash, str) or len(stored_hash) != 64:
        raise GateReportTamperedError(
            f"gate report {evidence_id!r} has malformed identity_hash "
            f"{stored_hash!r}; expected 64-char hex digest"
        )
    if stored_hash != expected_hash:
        raise GateReportTamperedError(
            f"gate report {evidence_id!r} identity_hash mismatch: "
            f"stored {stored_hash!r} does not match recomputed "
            f"{expected_hash!r}"
        )

    # Validate redundant provenance token matches independent recomputation.
    stored_prov = m.get("provenance_token")
    expected_prov = _compute_provenance_token(
        _GATE_ACTOR, _GATE_SOURCE, task.id, run.id
    )
    if stored_prov is None:
        raise GateReportTamperedError(
            f"gate report {evidence_id!r} missing provenance_token; "
            f"cannot verify dual-hash provenance"
        )
    if not isinstance(stored_prov, str) or len(stored_prov) != 64:
        raise GateReportTamperedError(
            f"gate report {evidence_id!r} has malformed provenance_token "
            f"{stored_prov!r}; expected 64-char hex digest"
        )
    if stored_prov != expected_prov:
        raise GateReportTamperedError(
            f"gate report {evidence_id!r} provenance_token mismatch: "
            f"stored {stored_prov!r} does not match recomputed "
            f"{expected_prov!r}"
        )

    # Validate authority is correct for workflow assurance mode.
    expected_authority = (
        "verified-deterministic"
        if workflow.assurance is AssuranceMode.VERIFIED
        else "standard-deterministic"
    )
    if stored_authority not in _VALID_AUTHORITY_VALUES:
        raise GateReportTamperedError(
            f"gate report authority {stored_authority!r} "
            f"is not a valid authority value"
        )
    if stored_verdict is GateOutcome.PASS and stored_authority != expected_authority:
        raise GateReportTamperedError(
            f"gate report PASS verdict with authority {stored_authority!r} "
            f"does not match expected {expected_authority!r} for workflow assurance"
        )
    if stored_authority == "none" and stored_verdict is GateOutcome.PASS:
        raise GateReportTamperedError(
            "gate report has PASS verdict but authority is 'none'"
        )

    # Validate required_evidence_ids actually exist in task/run evidence,
    # excluding the gate report itself to prevent self-reference.
    actual_evidence = _scope_evidence(task, run, evidence_repo, exclude_id=evidence_id)
    actual_ids = {e.id for e in actual_evidence}
    for eval_item in evaluations:
        for req_id in eval_item.required_evidence_ids:
            if req_id not in actual_ids:
                raise GateReportTamperedError(
                    f"gate report references evidence {req_id!r} which "
                    f"does not exist in task/run evidence"
                )
        # satisfied_by must not reference the gate report itself.
        if eval_item.satisfied_by == evidence_id:
            raise GateReportTamperedError(
                f"evaluation satisfied_by references gate report itself"
            )

    # Validate evaluation structure matches workflow configuration.
    _validate_evaluation_structure(workflow, evaluations, evidence_id)

    # Re-evaluate against actual evidence and compare.
    re_evaluated = evaluate_workflow_gates(
        workflow, task, run, evidence_repo, exclude_evidence_id=evidence_id
    )

    # Strict comparison: verdict must match.
    if re_evaluated.verdict is not stored_verdict:
        raise GateReportTamperedError(
            f"gate report verdict {stored_verdict.value!r} does not match "
            f"re-evaluation ({re_evaluated.verdict.value!r})"
        )

    # Strict comparison: authority must match.
    if re_evaluated.authority != stored_authority:
        raise GateReportTamperedError(
            f"gate report authority {stored_authority!r} does not match "
            f"re-evaluation authority ({re_evaluated.authority!r})"
        )

    # Strict comparison: overall_reason must match.
    if re_evaluated.overall_reason != stored_overall_reason:
        raise GateReportTamperedError(
            f"gate report overall_reason does not match re-evaluation"
        )

    # Strict comparison: evaluations must match.
    if len(re_evaluated.evaluations) != len(evaluations):
        raise GateReportTamperedError(
            f"gate report has {len(evaluations)} evaluations but "
            f"re-evaluation has {len(re_evaluated.evaluations)}"
        )
    for stored_eval, fresh_eval in zip(evaluations, re_evaluated.evaluations):
        if stored_eval.gate_id != fresh_eval.gate_id:
            raise GateReportTamperedError(
                f"evaluation gate_id {stored_eval.gate_id!r} does not match "
                f"re-evaluation {fresh_eval.gate_id!r}"
            )
        if stored_eval.step_id != fresh_eval.step_id:
            raise GateReportTamperedError(
                f"evaluation {stored_eval.gate_id!r} step_id "
                f"{stored_eval.step_id!r} does not match "
                f"re-evaluation {fresh_eval.step_id!r}"
            )
        if stored_eval.kind is not fresh_eval.kind:
            raise GateReportTamperedError(
                f"evaluation {stored_eval.gate_id!r} kind "
                f"{stored_eval.kind.value!r} does not match "
                f"re-evaluation {fresh_eval.kind.value!r}"
            )
        if stored_eval.outcome is not fresh_eval.outcome:
            raise GateReportTamperedError(
                f"evaluation {stored_eval.gate_id!r} outcome "
                f"{stored_eval.outcome.value!r} does not match "
                f"re-evaluation {fresh_eval.outcome.value!r}"
            )
        if stored_eval.reason != fresh_eval.reason:
            raise GateReportTamperedError(
                f"evaluation {stored_eval.gate_id!r} reason "
                f"does not match re-evaluation"
            )
        if stored_eval.satisfied_by != fresh_eval.satisfied_by:
            raise GateReportTamperedError(
                f"evaluation {stored_eval.gate_id!r} satisfied_by "
                f"{stored_eval.satisfied_by!r} does not match "
                f"re-evaluation {fresh_eval.satisfied_by!r}"
            )
        if stored_eval.required_evidence_ids != fresh_eval.required_evidence_ids:
            raise GateReportTamperedError(
                f"evaluation {stored_eval.gate_id!r} required_evidence_ids "
                f"do not match re-evaluation"
            )

    return WorkflowGateReport(
        workflow_id=stored_workflow_id,
        workflow_version=stored_workflow_version,
        task_id=ev.task_id,
        run_id=ev.run_id,
        evaluations=tuple(evaluations),
        verdict=stored_verdict,
        authority=stored_authority,
        overall_reason=stored_overall_reason,
    )


def _validate_evaluation_structure(
    workflow: WorkflowDefinition,
    evaluations: Sequence[GateEvaluation],
    evidence_id: str,
) -> None:
    """Validate that evaluations match the workflow configuration.

    Terminal runs produce empty evaluations — this is a valid state and
    must not be treated as missing expected gates.
    """
    # Terminal runs produce empty evaluations; skip structure validation.
    if not evaluations:
        return
    # Build expected gate IDs from workflow.
    expected_evidence_gates: set[str] = set()
    expected_human_gates: set[str] = set()
    expected_steps: dict[str, str] = {}  # step_id -> type
    for step in workflow.steps:
        expected_steps[step.id] = step.type
        if step.type == GateKind.EVIDENCE_CHECK.value:
            for gid in step.parameters.get("hard_gates", []):
                expected_evidence_gates.add(gid)
        elif step.type == GateKind.HUMAN_GATE.value:
            gid = step.parameters.get(_HUMAN_GATE_METADATA_KEY, step.id)
            expected_human_gates.add(gid)

    actual_gate_ids = {e.gate_id for e in evaluations}
    actual_step_ids = {e.step_id for e in evaluations}

    # Validate all expected gates are present.
    for gid in expected_evidence_gates:
        if gid not in actual_gate_ids:
            raise GateReportTamperedError(
                f"gate report {evidence_id!r} missing expected gate {gid!r}"
            )
    for gid in expected_human_gates:
        if gid not in actual_gate_ids:
            raise GateReportTamperedError(
                f"gate report {evidence_id!r} missing expected human gate {gid!r}"
            )

    # Validate step_ids are valid.
    for sid in actual_step_ids:
        if sid not in expected_steps:
            raise GateReportTamperedError(
                f"gate report {evidence_id!r} references unknown step {sid!r}"
            )

    # Validate kinds match.
    for eval_item in evaluations:
        expected_type = expected_steps.get(eval_item.step_id)
        if expected_type == GateKind.EVIDENCE_CHECK.value:
            if eval_item.kind is not GateKind.EVIDENCE_CHECK:
                raise GateReportTamperedError(
                    f"evaluation for step {eval_item.step_id!r} has wrong kind "
                    f"{eval_item.kind.value!r}, expected EVIDENCE_CHECK"
                )
        elif expected_type == GateKind.HUMAN_GATE.value:
            if eval_item.kind is not GateKind.HUMAN_GATE:
                raise GateReportTamperedError(
                    f"evaluation for step {eval_item.step_id!r} has wrong kind "
                    f"{eval_item.kind.value!r}, expected HUMAN_GATE"
                )


def _recompute_verdict_from_evaluations(
    evaluations: Sequence[GateEvaluation],
) -> tuple[GateOutcome, str, str]:
    """Re-derive verdict from stored evaluations for best-effort tamper detection."""
    failed = [e for e in evaluations if e.outcome is GateOutcome.FAIL]
    need_action = [e for e in evaluations if e.outcome is GateOutcome.NEED_ACTION]
    human_evals = [e for e in evaluations if e.kind is GateKind.HUMAN_GATE]
    human_pending = [e for e in human_evals if e.outcome is GateOutcome.HUMAN_DECISION]

    if failed:
        return (
            GateOutcome.FAIL,
            "none",
            "one or more required deterministic gates failed; "
            "verdict cannot be PASS/VERIFIED",
        )
    if need_action:
        return (
            GateOutcome.NEED_ACTION,
            "none",
            "one or more required gates missing/unverified; "
            "verdict cannot be PASS/VERIFIED",
        )
    if human_evals and human_pending:
        return (
            GateOutcome.HUMAN_DECISION,
            "none",
            "human gate pending; explicit decision required before progression",
        )
    return (
        GateOutcome.PASS,
        "verified-deterministic",
        "all required deterministic gates passed and human gates approved",
    )
