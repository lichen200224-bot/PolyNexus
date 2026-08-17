import pytest

from polynexus_core.domain.enums import EvidenceType, RunState
from polynexus_core.domain.run_lifecycle import assert_transition, can_transition


def test_normal_run_transitions() -> None:
    assert can_transition(RunState.CREATED, RunState.STARTING)
    assert can_transition(RunState.STARTING, RunState.RUNNING)
    assert can_transition(RunState.RUNNING, RunState.COMPLETED)


def test_terminal_state_is_immutable() -> None:
    assert not can_transition(RunState.COMPLETED, RunState.RUNNING)
    with pytest.raises(ValueError):
        assert_transition(RunState.CANCELLED, RunState.RUNNING)


def test_cancel_requires_cancel_requested_path() -> None:
    assert can_transition(RunState.RUNNING, RunState.CANCEL_REQUESTED)
    assert can_transition(RunState.CANCEL_REQUESTED, RunState.CANCELLED)
    assert not can_transition(RunState.RUNNING, RunState.CANCELLED)


def test_ai_opinion_and_tool_evidence_are_distinct() -> None:
    assert EvidenceType.AI_OPINION != EvidenceType.TOOL_EVIDENCE
