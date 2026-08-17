from pathlib import Path

import pytest

from polynexus_core.workflows.loader import WorkflowValidationError, load_workflow

ROOT = Path(__file__).resolve().parents[3]


def test_builtin_review_workflow_validates() -> None:
    workflow = load_workflow(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    assert workflow["id"] == "review-minimal"
    assert workflow["version"] == 1


def test_invalid_node_is_rejected(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text(
        "id: invalid\nversion: 1\nsteps:\n  - id: bad\n    type: ARBITRARY_SCRIPT\n",
        encoding="utf-8",
    )
    with pytest.raises(WorkflowValidationError):
        load_workflow(invalid)
