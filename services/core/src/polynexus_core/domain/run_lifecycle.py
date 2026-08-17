from polynexus_core.domain.enums import RunState

TERMINAL_STATES = {
    RunState.COMPLETED,
    RunState.FAILED,
    RunState.TIMED_OUT,
    RunState.CANCELLED,
    RunState.ORPHANED,
}

_ALLOWED: dict[RunState, set[RunState]] = {
    RunState.CREATED: {RunState.STARTING, RunState.CANCEL_REQUESTED},
    RunState.STARTING: {
        RunState.RUNNING,
        RunState.FAILED,
        RunState.CANCEL_REQUESTED,
    },
    RunState.RUNNING: {
        RunState.COMPLETED,
        RunState.FAILED,
        RunState.TIMED_OUT,
        RunState.CANCEL_REQUESTED,
    },
    RunState.CANCEL_REQUESTED: {
        RunState.CANCELLED,
        RunState.ORPHANED,
    },
    RunState.COMPLETED: set(),
    RunState.FAILED: set(),
    RunState.TIMED_OUT: set(),
    RunState.CANCELLED: set(),
    RunState.ORPHANED: set(),
}


def can_transition(current: RunState, target: RunState) -> bool:
    return target in _ALLOWED[current]


def assert_transition(current: RunState, target: RunState) -> None:
    if not can_transition(current, target):
        raise ValueError(f"Invalid run transition: {current} -> {target}")
