"""WP-25 deterministic tests for descriptive evaluation metrics."""

from polynexus_core.domain.enums import EvidenceStatus, EvidenceType, RunState
from polynexus_core.domain.models import ContextPackage, Evidence, Project, Run, Task
from polynexus_core.evaluation.metrics import calculate_evaluation_metrics


def _run(run_id: str, state: RunState) -> Run:
    project = Project(name="WP25")
    context = ContextPackage(project_id=project.id, version=1)
    task = Task(
        id=f"task-{run_id}",
        project_id=project.id,
        title="metrics fixture",
        workflow_id="review-minimal",
        workflow_version=1,
        context_package_id=context.id,
    )
    return Run(
        task_id=task.id,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=context.id,
        id=run_id,
        state=state,
    )


def _evidence(run_id: str, *, task_id: str | None = None, **metadata: str) -> Evidence:
    return Evidence(
        task_id=task_id or f"task-{run_id}",
        run_id=run_id,
        actor_id="fixture",
        source="fixture",
        type=EvidenceType.RUNTIME_EVIDENCE,
        status=EvidenceStatus.OBSERVED,
        metadata=metadata,
    )


def test_metrics_use_only_observable_terminal_runs_and_matching_evidence() -> None:
    runs = [
        _run("run-complete", RunState.COMPLETED),
        _run("run-failed", RunState.FAILED),
        _run("run-cancelled", RunState.CANCELLED),
        _run("run-active", RunState.RUNNING),
    ]
    evidence = [
        _evidence("run-complete", fallback_used="false"),
        _evidence("run-failed"),
        _evidence("unrelated", fallback_used="true"),
    ]

    metrics = calculate_evaluation_metrics(runs, evidence)

    assert metrics.run_count == 4
    assert metrics.terminal_run_count == 3
    assert metrics.completed_run_count == 1
    assert metrics.failed_run_count == 1
    assert metrics.cancelled_run_count == 1
    assert metrics.workflow_completion_rate == 1 / 3
    assert metrics.runtime_failure_rate == 1 / 3
    assert metrics.evidence_count == 2
    assert metrics.runs_with_evidence == 2
    assert metrics.evidence_coverage_rate == 1 / 2
    assert metrics.fallback_run_count == 0
    assert metrics.fallback_rate == 0.0
    assert metrics.manual_operation_count is None


def test_explicit_usage_metadata_is_counted_without_inference() -> None:
    runs = [_run("run-a", RunState.COMPLETED), _run("run-b", RunState.COMPLETED)]
    evidence = [
        _evidence("run-a", fallback_used="true", manual_operation_count="2"),
        _evidence("run-b", fallback_used="true", manual_operation_count="1"),
    ]

    metrics = calculate_evaluation_metrics(runs, evidence)

    assert metrics.fallback_run_count == 2
    assert metrics.fallback_rate == 1.0
    assert metrics.manual_operation_count == 3


def test_unsupported_or_invalid_optional_values_are_not_guessed() -> None:
    runs = [_run("run-a", RunState.COMPLETED)]

    unsupported = calculate_evaluation_metrics(runs, [_evidence("run-a")])
    invalid = calculate_evaluation_metrics(
        runs,
        [_evidence("run-a", fallback_used="maybe", manual_operation_count="unknown")],
    )

    assert unsupported.fallback_run_count is None
    assert unsupported.fallback_rate is None
    assert unsupported.manual_operation_count is None
    assert invalid.fallback_run_count is None
    assert invalid.fallback_rate is None
    assert invalid.manual_operation_count is None


def test_empty_input_has_no_zero_claim_for_unobservable_rates() -> None:
    metrics = calculate_evaluation_metrics([], [])

    assert metrics.run_count == 0
    assert metrics.terminal_run_count == 0
    assert metrics.workflow_completion_rate is None
    assert metrics.runtime_failure_rate is None
    assert metrics.evidence_coverage_rate is None
    assert metrics.fallback_run_count is None
    assert metrics.fallback_rate is None


def test_metrics_exclude_cross_task_evidence_even_when_run_id_matches() -> None:
    runs = [_run("run-a", RunState.COMPLETED)]

    metrics = calculate_evaluation_metrics(
        runs,
        [_evidence("run-a", task_id="other-task", fallback_used="true")],
    )

    assert metrics.evidence_count == 0
    assert metrics.runs_with_evidence == 0
    assert metrics.evidence_coverage_rate == 0.0
    assert metrics.fallback_run_count is None


def test_metrics_are_stable_after_reloading_equivalent_records() -> None:
    runs = [_run("run-a", RunState.COMPLETED), _run("run-b", RunState.FAILED)]
    evidence = [
        _evidence("run-a", fallback_used="true", manual_operation_count="2"),
        _evidence("run-b", manual_operation_count="1"),
    ]

    first = calculate_evaluation_metrics(runs, evidence)
    # The metrics function is intentionally non-persistent; this models a
    # fresh repository reload by rebuilding equivalent domain records.
    reloaded_runs = [_run("run-a", RunState.COMPLETED), _run("run-b", RunState.FAILED)]
    reloaded_evidence = [
        _evidence("run-a", fallback_used="true", manual_operation_count="2"),
        _evidence("run-b", manual_operation_count="1"),
    ]

    assert calculate_evaluation_metrics(reloaded_runs, reloaded_evidence) == first
