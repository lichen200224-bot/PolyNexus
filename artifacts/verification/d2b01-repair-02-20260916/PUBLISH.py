"""Publish exact-source D2B-01 diagnostic bytes with deterministic path normalization."""
from __future__ import annotations

import hashlib
import json
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SANITIZER = ROOT.parent / "d2b01-opencode-20260915" / "SANITIZE.py"
helpers = runpy.run_path(str(SANITIZER))
scan = helpers["scan"]


def normalize(data: bytes) -> bytes:
    home = str(Path.home())
    for count in (8, 4, 2, 1):
        data = data.replace(home.replace("\\", "\\" * count).encode(), b"<USER_HOME>")
    return data.replace(home.replace("\\", "/").encode(), b"<USER_HOME>")


def publish(source: Path, target: Path) -> None:
    raw = source.read_bytes()
    scan(raw, source)
    safe = normalize(raw)
    scan(safe, source)
    if any(str(Path.home()).replace("\\", "\\" * count).encode() in safe
           for count in (1, 2, 4, 8)):
        raise ValueError("personal path remained: " + str(source))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(safe)
    print(f"{target.relative_to(ROOT).as_posix()} raw_sha256={hashlib.sha256(raw).hexdigest()} sanitized_sha256={hashlib.sha256(safe).hexdigest()}")


def command_record(kind: str, attempt: int) -> dict[str, object]:
    rows = json.loads((ROOT / "EXECUTION_COMMAND_RECORDS.json").read_text(encoding="utf-8"))
    found = [row for row in rows if row["kind"] == kind and row["artifact_attempt"] == attempt]
    if len(found) != 1:
        raise ValueError("exact app command record missing or ambiguous")
    return found[0]


def build_provenance(first: Path, success: Path, preflight_first: Path, preflight_success: Path) -> None:
    before = json.loads(preflight_first.read_text(encoding="utf-8-sig"))
    executed = json.loads(preflight_success.read_text(encoding="utf-8-sig"))
    run = json.loads((success / "production-run.json").read_text(encoding="utf-8"))
    readback = json.loads((success / "production-readback.json").read_text(encoding="utf-8"))
    first_run = command_record("real_product_path", 1)
    first_readback = command_record("independent_readback", 1)
    real_run = command_record("real_product_path", 2)
    independent = command_record("independent_readback", 2)
    repository = ROOT.parents[2]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=repository, text=True).strip()
    executable = Path(run["launch_observations_before_effect"][0]["argv"][0])
    version = [e["metadata"].get("executable_version") for e in run["persisted_runtime_evidence"]
               if e["source"] == "runtime.opencode.acp"]
    if (
        before["executed_source_sha"] != "4b1c2c57b78ad8e55833080400819c591133bf54"
        or executed["executed_source_sha"] != "98e674570f357b4e8af23d9f203f993f42ce638e"
        or first_run["actual_exit"] != 1 or first_readback["actual_exit"] != 0
        or real_run["actual_exit"] != 0 or independent["actual_exit"] != 0
        or run["outcome"] != "COMPLETED" or readback["run"]["state"] != "COMPLETED"
        or run["run_id"] != readback["run"]["id"]
        or run["selected_profile"] != readback["binding"]["runtime_profile_ref"]
        or set(run["all_evidence_sources"]) != {e["source"] for e in readback["evidence"]}
        or head != executed["executed_source_sha"] or tree != executed["executed_tree_sha"]
        or hashlib.sha256((repository / "tools" / "run_d2b01_production.py").read_bytes()).hexdigest() != executed["runner_sha256"]
        or hashlib.sha256((repository / "tools" / "readback_d2b01_production.py").read_bytes()).hexdigest() != executed["readback_runner_sha256"]
        or hashlib.sha256(executable.read_bytes()).hexdigest() != executed["opencode_executable_sha256"]
        or version != ["opencode-" + executed["opencode_version"]]
    ):
        raise ValueError("source/run/readback provenance mismatch")
    for key in ("raw_artifact_root",):
        executed.pop(key, None)
    provenance = {
        **executed,
        "real_run_actual_exit": real_run["actual_exit"],
        "readback_actual_exit": independent["actual_exit"],
        "run_id": run["run_id"],
        "publication_parent_sha": executed["executed_source_sha"],
        "intermediate_frozen_attempt": {
            "source_sha": before["executed_source_sha"],
            "tree_sha": before["executed_tree_sha"],
            "runner_sha256": before["runner_sha256"],
            "real_run_actual_exit": first_run["actual_exit"],
            "readback_actual_exit": first_readback["actual_exit"],
            "tool_failure": "RuntimeDispatchAuthorizationEventRow was subscripted in final oracle",
            "raw_ref": "commit-a1-failed-run/production-run.json",
        },
    }
    (ROOT / "SOURCE_PROVENANCE.json").write_bytes(
        (json.dumps(provenance, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def manifest() -> None:
    target = ROOT / "MANIFEST.sha256"
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}"
             for path in sorted(ROOT.rglob("*"), key=lambda item: item.as_posix())
             if path.is_file() and path != target]
    target.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    print("MANIFEST_FILES=" + str(len(lines)))
    print("MANIFEST_SHA256=" + hashlib.sha256(target.read_bytes()).hexdigest())


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit("usage: PUBLISH.py RAW_A1 RAW_A2 PREFLIGHT_A1 PREFLIGHT_A2")
    first, success, preflight_first, preflight_success = (Path(value).resolve() for value in sys.argv[1:])
    record = json.loads((success / "production-run.json").read_text(encoding="utf-8"))
    staging = Path(record["launch_observations_before_effect"][0]["cwd"])
    pairs = (
        (first / "production-run.json", ROOT / "commit-a1-failed-run" / "production-run.json"),
        (first / "production-readback.json", ROOT / "commit-a1-failed-run" / "production-readback.json"),
        (first / "production-acp.stdout.jsonl", ROOT / "commit-a1-failed-run" / "production-acp.stdout.jsonl"),
        (first / "production-acp.stderr.log", ROOT / "commit-a1-failed-run" / "production-acp.stderr.log"),
        (first / "production-postcondition.stdout.log", ROOT / "commit-a1-failed-run" / "production-postcondition.stdout.log"),
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
        (preflight_first, ROOT / "commit-a1-failed-run" / "source-preflight.json"),
        (preflight_success, ROOT / "source-preflight.json"),
    )
    for source, target in pairs:
        publish(source, target)
    build_provenance(first, success, preflight_first, preflight_success)
    manifest()


if __name__ == "__main__":
    main()
