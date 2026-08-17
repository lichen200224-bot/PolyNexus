from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "AGENTS.md",
    "docs/01_PRD.md",
    "docs/02_SA.md",
    "docs/03_SD.md",
    "docs/18_ARCHITECTURE_DECISIONS.md",
    "docs/19_DEVELOPMENT_BASELINE.md",
    "docs/20_FIRST_VERTICAL_SLICE_PLAN.md",
    "services/core/pyproject.toml",
    "apps/web/package.json",
    "extensions/browser-companion/manifest.json",
    "schemas/workflow.schema.json",
]

missing = [path for path in REQUIRED if not (ROOT / path).exists()]
if missing:
    raise SystemExit(f"Missing baseline files: {missing}")

schema = json.loads((ROOT / "schemas/workflow.schema.json").read_text(encoding="utf-8"))
validator = Draft202012Validator(schema)
for workflow_path in sorted((ROOT / "workflows/builtin").glob("*.yaml")):
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    errors = list(validator.iter_errors(data))
    if errors:
        raise SystemExit(f"Workflow invalid: {workflow_path}: {errors[0].message}")

manifest = json.loads((ROOT / "extensions/browser-companion/manifest.json").read_text(encoding="utf-8"))
if manifest.get("manifest_version") != 3:
    raise SystemExit("Browser companion must remain Manifest V3")

print(f"Baseline validation PASS: {len(REQUIRED)} required files; workflows valid; MV3 manifest valid")
