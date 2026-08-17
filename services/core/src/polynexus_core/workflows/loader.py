from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


class WorkflowValidationError(ValueError):
    pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def default_schema_path() -> Path:
    return _repo_root() / "schemas" / "workflow.schema.json"


def load_workflow(path: str | Path, schema_path: str | Path | None = None) -> dict[str, Any]:
    workflow_path = Path(path)
    schema_file = Path(schema_path) if schema_path else default_schema_path()

    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_file.read_text(encoding="utf-8"))

    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda err: list(err.path))
    if errors:
        details = "; ".join(error.message for error in errors[:5])
        raise WorkflowValidationError(details)

    return data
