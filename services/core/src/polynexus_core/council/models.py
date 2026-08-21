"""WP-12 Council domain models.

Additive orchestration contracts using existing Task/Run/RunEvent/Evidence
boundaries. No new persisted table, migration, RunState, WorkMode, EvidenceType,
or REST endpoint is introduced by WP-12.

A Council is executed under a normal Task (mode DISCUSS / REVIEW / VALIDATE).
Each participant's independent analysis is a Run; cross-review and synthesis are
additional Runs. Stage ordering and participant/round correlation are persisted
as RunEvents (durable, ordered) and as a reloadable CouncilPlan Evidence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping, Sequence
from uuid import uuid4


class CouncilStage(StrEnum):
    ANALYSIS = "ANALYSIS"
    CROSS_REVIEW = "CROSS_REVIEW"
    SYNTHESIS = "SYNTHESIS"


class ParticipantOutcome(StrEnum):
    """WP-12 participant outcome classification.

    COMPLETED / FAILED / TIMED_OUT / CANCELLED map to existing RunState values
    for executed participants. UNAVAILABLE is a Council-only policy outcome for
    participants the orchestration decided not to execute (no Run created).
    """

    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class CouncilParticipant:
    id: str
    role: str
    round: int = 1
    analysis_run_id: str | None = None
    cross_review_run_ids: tuple[str, ...] = ()
    outcome: ParticipantOutcome | None = None
    output_ref: str | None = None
    reason: str | None = None
    target_participant_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Participant id must not be empty")
        if not self.role.strip():
            raise ValueError("Participant role must not be empty")
        if self.round < 1:
            raise ValueError("Council round must be positive")
        object.__setattr__(self, "cross_review_run_ids", tuple(self.cross_review_run_ids))
        object.__setattr__(self, "target_participant_ids", tuple(self.target_participant_ids))

    def to_mapping(self) -> dict[str, object]:
        return {
            "id": self.id,
            "role": self.role,
            "round": self.round,
            "analysis_run_id": self.analysis_run_id,
            "cross_review_run_ids": list(self.cross_review_run_ids),
            "outcome": self.outcome.value if self.outcome else None,
            "output_ref": self.output_ref,
            "reason": self.reason,
            "target_participant_ids": list(self.target_participant_ids),
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "CouncilParticipant":
        outcome = data.get("outcome")
        return cls(
            id=str(data["id"]),
            role=str(data["role"]),
            round=int(data["round"]),
            analysis_run_id=data.get("analysis_run_id"),
            cross_review_run_ids=tuple(data.get("cross_review_run_ids", ())),
            outcome=ParticipantOutcome(str(outcome)) if outcome else None,
            output_ref=data.get("output_ref"),
            reason=data.get("reason"),
            target_participant_ids=tuple(data.get("target_participant_ids", ())),
        )


@dataclass
class CouncilPlan:
    council_run_id: str
    mode: str
    participants: tuple[CouncilParticipant, ...]
    round: int = 1
    stages_completed: tuple[CouncilStage, ...] = ()
    synthesis_run_id: str | None = None
    consensus_ref: str | None = None
    partial: bool = False
    # Runtime-only evidence (not persisted): max concurrent analysis executions
    # observed during the most recent run. Used by contract tests to prove
    # bounded parallel execution.
    max_concurrency_observed: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "participants", tuple(self.participants))
        object.__setattr__(self, "stages_completed", tuple(self.stages_completed))

    def to_mapping(self) -> dict[str, object]:
        return {
            "council_run_id": self.council_run_id,
            "mode": self.mode,
            "round": self.round,
            "participants": [p.to_mapping() for p in self.participants],
            "stages_completed": [s.value for s in self.stages_completed],
            "synthesis_run_id": self.synthesis_run_id,
            "consensus_ref": self.consensus_ref,
            "partial": self.partial,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "CouncilPlan":
        return cls(
            council_run_id=str(data["council_run_id"]),
            mode=str(data["mode"]),
            participants=tuple(
                CouncilParticipant.from_mapping(p) for p in data["participants"]
            ),
            round=int(data.get("round", 1)),
            stages_completed=tuple(
                CouncilStage(str(s)) for s in data.get("stages_completed", ())
            ),
            synthesis_run_id=data.get("synthesis_run_id"),
            consensus_ref=data.get("consensus_ref"),
            partial=bool(data.get("partial", False)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> "CouncilPlan":
        return cls.from_mapping(json.loads(text))


def new_council_id() -> str:
    return f"council_{uuid4().hex}"


@dataclass
class CouncilSpec:
    """Input specification for one Council participant (before execution)."""

    id: str
    role: str
    expected_outcome: ParticipantOutcome | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Participant id must not be empty")
        if not self.role.strip():
            raise ValueError("Participant role must not be empty")


def validate_participant_specs(specs: Sequence[CouncilSpec], round: int = 1) -> None:
    """Reject <2 or >4 participants and duplicate participant identity within a round."""
    if len(specs) < 2:
        raise ValueError("Council requires at least 2 participants")
    if len(specs) > 4:
        raise ValueError("Council allows at most 4 participants")
    seen: set[str] = set()
    for spec in specs:
        if spec.id in seen:
            raise ValueError(f"Duplicate participant identity in round {round}: {spec.id}")
        seen.add(spec.id)
