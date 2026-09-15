"""Deterministically publish raw isolated Run records with home-path normalization."""
from __future__ import annotations

import hashlib
import json
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT_SANITIZER = ROOT.parent / "d2b01-opencode-20260915" / "SANITIZE.py"
helpers = runpy.run_path(str(PARENT_SANITIZER))
normalize, scan = helpers["normalize"], helpers["scan"]


def publish(source: Path, target: Path) -> None:
    raw = source.read_bytes()
    scan(raw, source)
    safe = normalize(raw)
    scan(safe, source)
    home = str(Path.home())
    if home.encode() in safe or home.replace("\\", "\\\\").encode() in safe:
        raise ValueError("personal home prefix remained: " + source.name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(safe)
    print(f"{target.relative_to(ROOT)} raw_sha256={hashlib.sha256(raw).hexdigest()} sanitized_sha256={hashlib.sha256(safe).hexdigest()}")


def manifest() -> None:
    target = ROOT / "MANIFEST.sha256"
    rows = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}"
            for path in sorted(ROOT.rglob("*"), key=lambda item: item.as_posix())
            if path.is_file() and path != target]
    target.write_bytes(("\n".join(rows) + "\n").encode("utf-8"))
    print("MANIFEST_FILES=" + str(len(rows)))
    print("MANIFEST_SHA256=" + hashlib.sha256(target.read_bytes()).hexdigest())


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: PUBLISH.py FAILED_RAW_ROOT SUCCESS_RAW_ROOT VALIDATION_RAW_ROOT")
    failed, success, validation = (Path(arg).resolve() for arg in sys.argv[1:])
    record = json.loads((success / "production-run.json").read_text(encoding="utf-8"))
    staging = Path(record["launch_observations_before_effect"][0]["cwd"])
    pairs = (
        (failed / "production-run.json", ROOT / "first-timeout-production-run.json"),
        (failed / "production-acp.stdout.jsonl", ROOT / "first-timeout-acp.stdout.jsonl"),
        (failed / "production-acp.stderr.log", ROOT / "first-timeout-acp.stderr.log"),
        (failed / "production-postcondition.stdout.log", ROOT / "first-timeout-postcondition.stdout.log"),
        (success / "production-run.json", ROOT / "production-run.json"),
        (success / "production-readback.json", ROOT / "production-readback.json"),
        (success / "production-acp.stdout.jsonl", ROOT / "production-acp.stdout.jsonl"),
        (success / "production-acp.stderr.log", ROOT / "production-acp.stderr.log"),
        (success / "production-postcondition.stdout.log", ROOT / "production-postcondition.stdout.log"),
        (success / "production-postcondition.stderr.log", ROOT / "production-postcondition.stderr.log"),
        (success / "source-root" / "synthetic" / "bug.py", ROOT / "source-before" / "bug.py"),
        (success / "source-root" / "synthetic" / "test_bug.py", ROOT / "source-before" / "test_bug.py"),
        (staging / "bug.py", ROOT / "source-after" / "bug.py"),
        (staging / "test_bug.py", ROOT / "source-after" / "test_bug.py"),
        (validation / "targeted.log", ROOT / "targeted.log"),
        (validation / "factory.log", ROOT / "factory.log"),
        (validation / "cancel.log", ROOT / "cancel.log"),
        (validation / "affected.log", ROOT / "affected.log"),
        (validation / "migration.log", ROOT / "migration.log"),
        (validation / "full-core.log", ROOT / "full-core.log"),
    )
    for source, target in pairs:
        publish(source, target)
    manifest()


if __name__ == "__main__":
    main()
