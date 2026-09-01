"""CP06 WP31 deterministic packaging and compatibility checks."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_core_and_web_package_metadata_are_explicit_and_bounded() -> None:
    core = tomllib.loads((ROOT / "services/core/pyproject.toml").read_text(encoding="utf-8"))
    web = json.loads((ROOT / "apps/web/package.json").read_text(encoding="utf-8"))

    assert core["project"]["requires-python"] == ">=3.12"
    assert core["project"]["dependencies"]
    assert all("@" not in dependency for dependency in core["project"]["dependencies"])
    assert web["private"] is True
    assert web["engines"]["node"] == ">=22.12.0"
    assert web["scripts"] == {
        "dev": "vite --host 127.0.0.1",
        "build": "tsc -b && vite build",
        "test": "vitest run",
    }


def test_baseline_validator_is_reproducible_from_candidate_source() -> None:
    result = subprocess.run(
        [sys.executable, "-B", str(ROOT / "scripts/validate_baseline.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0


def test_compatibility_matrix_uses_truthful_maturity_labels() -> None:
    matrix = (ROOT / "docs/31_COMPATIBILITY_MATRIX.md").read_text(encoding="utf-8")
    limitations = (ROOT / "docs/32_KNOWN_LIMITATIONS.md").read_text(encoding="utf-8")

    for label in ("PREVIEW", "EXPERIMENTAL", "IN_DEVELOPMENT", "UNVERIFIED"):
        assert label in matrix or label in limitations
    assert "CERTIFIED" not in matrix
    assert "SUPPORTED" not in matrix
    assert "no silent cloud fallback" in matrix.lower()
    assert "browser" in limitations.lower()
