"""Private W1 references; no replacement Run state or Attempt aggregate."""
from dataclasses import dataclass

@dataclass(frozen=True)
class WorkGenerationRef:
    task_id: str
    generation_revision: int

    def __post_init__(self):
        if not self.task_id or not isinstance(self.generation_revision,int) or isinstance(self.generation_revision, bool) or self.generation_revision < 1:
            raise GenerationConflict("Invalid exact generation reference")


class GenerationConflict(ValueError):
    """Bounded rejected mutation, with no launch side effect."""
