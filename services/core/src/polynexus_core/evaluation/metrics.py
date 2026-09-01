"""Descriptive, non-persistent evaluation metrics for existing run evidence.

This module deliberately computes only values that are observable from the
existing ``Run`` and ``Evidence`` domain objects. It does not persist data,
emit telemetry, infer product benefit, or expose an API surface. Optional
usage/fallback values are counted only when an evidence record explicitly
marks them with the bounded metadata keys documented below.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from polynexus_core.domain.enums import RunState
from polynexus_core.domain.models import Evidence, Run
from polynexus_core.domain.run_lifecycle import TERMINAL_STATES


_FAILURE_STATES = frozenset(
    {RunState.FAILED, RunState.TIMED_OUT, RunState.ORPHANED}
)
_TRUE_VALUES = frozenset({"1", "true", "yes"})
_FALSE_VALUES = frozenset({"0", "false", "no"})
_FALLBACK_KEY = "fallback_used"
_MANUAL_OPERATION_COUNT_KEY = "manual_operation_count"


@dataclass(frozen=True)
class EvaluationMetrics:
    """A bounded snapshot of metrics supported by current domain evidence.

    ``None`` means the metric is not observable from the supplied evidence;
    it is never a claim that the value is zero. Rates are fractions in the
    closed interval ``[0.0, 1.0]`` and use terminal runs as their denominator
    unless otherwise stated.
    """

    run_count: int
    terminal_run_count: int
    completed_run_count: int
    failed_run_count: int
    cancelled_run_count: int
    workflow_completion_rate: float | None
    runtime_failure_rate: float | None
    evidence_count: int
    runs_with_evidence: int
    evidence_coverage_rate: float | None
    fallback_run_count: int | None
    fallback_rate: float | None
    manual_operation_count: int | None


def calculate_evaluation_metrics(
    runs: Sequence[Run], evidence: Sequence[Evidence]
) -> EvaluationMetrics:
    """Calculate descriptive metrics without mutating or persisting inputs.

    Evidence is associated with a run only when its ``run_id`` matches one of
    the supplied runs. Fallback and manual-operation metrics remain
    unavailable unless evidence explicitly carries the bounded metadata keys
    ``fallback_used`` or ``manual_operation_count``. Invalid optional values
    make the corresponding metric unavailable instead of being guessed.
    """

    run_ids = {run.id for run in runs}
    run_count = len(runs)
    terminal_runs = [run for run in runs if run.state in TERMINAL_STATES]
    terminal_run_count = len(terminal_runs)
    completed_run_count = sum(
        run.state is RunState.COMPLETED for run in terminal_runs
    )
    failed_run_count = sum(run.state in _FAILURE_STATES for run in terminal_runs)
    cancelled_run_count = sum(
        run.state is RunState.CANCELLED for run in terminal_runs
    )

    matched_evidence = [item for item in evidence if item.run_id in run_ids]
    evidence_run_ids = {item.run_id for item in matched_evidence}

    fallback_values: dict[str, bool] = {}
    fallback_metadata_present = False
    fallback_metadata_valid = True
    manual_operation_total = 0
    manual_metadata_present = False
    manual_metadata_valid = True
    for item in matched_evidence:
        if _FALLBACK_KEY in item.metadata:
            fallback_metadata_present = True
            value = str(item.metadata[_FALLBACK_KEY]).strip().lower()
            if value in _TRUE_VALUES:
                fallback_values[item.run_id] = True
            elif value in _FALSE_VALUES:
                fallback_values.setdefault(item.run_id, False)
            else:
                fallback_metadata_valid = False

        if _MANUAL_OPERATION_COUNT_KEY in item.metadata:
            manual_metadata_present = True
            raw_value = str(item.metadata[_MANUAL_OPERATION_COUNT_KEY]).strip()
            try:
                value = int(raw_value)
            except (TypeError, ValueError):
                manual_metadata_valid = False
                continue
            if value < 0:
                manual_metadata_valid = False
                continue
            manual_operation_total += value

    fallback_run_count = (
        sum(fallback_values.values())
        if fallback_metadata_present and fallback_metadata_valid
        else None
    )
    fallback_rate = (
        fallback_run_count / run_count
        if fallback_run_count is not None and run_count
        else (0.0 if fallback_run_count == 0 and run_count else None)
    )
    manual_operation_count = (
        manual_operation_total
        if manual_metadata_present and manual_metadata_valid
        else None
    )

    return EvaluationMetrics(
        run_count=run_count,
        terminal_run_count=terminal_run_count,
        completed_run_count=completed_run_count,
        failed_run_count=failed_run_count,
        cancelled_run_count=cancelled_run_count,
        workflow_completion_rate=_rate(completed_run_count, terminal_run_count),
        runtime_failure_rate=_rate(failed_run_count, terminal_run_count),
        evidence_count=len(matched_evidence),
        runs_with_evidence=len(evidence_run_ids),
        evidence_coverage_rate=_rate(len(evidence_run_ids), run_count),
        fallback_run_count=fallback_run_count,
        fallback_rate=fallback_rate,
        manual_operation_count=manual_operation_count,
    )


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator
