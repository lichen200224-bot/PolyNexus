from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from polynexus_core.domain.enums import AssuranceMode


@dataclass(frozen=True)
class WorkflowStep:
    id: str
    type: str
    depends_on: tuple[str, ...] = ()
    # Retained gate/step configuration (e.g. EVIDENCE_CHECK hard_gates,
    # HUMAN_GATE human_gate id, TOOL profile, PARALLEL_AI roles). Captured as the
    # full set of non-identity step keys so the canonical WorkflowDefinition keeps
    # everything the schema permits without a migration or new persisted model.
    parameters: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("WorkflowStep id must not be empty")
        if not self.type.strip():
            raise ValueError("WorkflowStep type must not be empty")
        object.__setattr__(self, "depends_on", tuple(self.depends_on))
        object.__setattr__(self, "parameters", dict(self.parameters))


@dataclass(frozen=True)
class WorkflowDefinition:
    id: str
    version: int
    steps: tuple[WorkflowStep, ...]
    assurance: AssuranceMode | None = None
    parameters: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("WorkflowDefinition id must not be empty")
        if self.version < 1:
            raise ValueError("WorkflowDefinition version must be positive")
        if not self.steps:
            raise ValueError("WorkflowDefinition must have at least one step")
        object.__setattr__(self, "steps", tuple(self.steps))
        object.__setattr__(self, "parameters", dict(self.parameters))

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "WorkflowDefinition":
        raw_steps = data.get("steps")
        if not isinstance(raw_steps, list):
            raise ValueError("WorkflowDefinition steps must be a list")
        steps = tuple(
            WorkflowStep(
                id=str(step["id"]),
                type=str(step["type"]),
                depends_on=tuple(step.get("depends_on", ())),
                parameters={
                    k: v
                    for k, v in step.items()
                    if k not in ("id", "type", "depends_on")
                },
            )
            for step in raw_steps
        )
        assurance = data.get("assurance")
        return cls(
            id=str(data["id"]),
            version=int(data["version"]),
            steps=steps,
            assurance=AssuranceMode(str(assurance)) if assurance is not None else None,
            parameters=data.get("parameters", {}),
        )
