"""Capture a real owned OpenCode ACP idle timeout and verified cancellation.

This control sends no model prompt. It proves process ownership and cleanup,
while malformed JSON-RPC and postcondition negatives remain Core contract tests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "core" / "src"))

from polynexus_core.workspace.ownership import ControlledJob  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    args = parser.parse_args()
    root = args.artifact_root.resolve(strict=False)
    if root.exists():
        raise RuntimeError("artifact root must be new")
    root.mkdir(parents=True)
    executable = args.executable.resolve(strict=True)
    config = root / "isolated-config"
    config.mkdir()
    cwd = root / "idle-staging"
    cwd.mkdir()
    names = ("COMSPEC", "PATHEXT", "PATH", "SYSTEMDRIVE", "SYSTEMROOT", "TEMP", "TMP", "WINDIR", "USERPROFILE", "APPDATA", "LOCALAPPDATA")
    environment = {name: os.environ[name] for name in names if name in os.environ}
    environment.update({
        "XDG_CONFIG_HOME": str(config), "OPENCODE_CONFIG_DIR": str(config),
        "OPENCODE_CONFIG_CONTENT": json.dumps({"model": "opencode/mimo-v2.5-free", "plugin": [], "mcp": {}, "permission": {"*": "deny"}}),
        "OPENCODE_DISABLE_AUTOUPDATE": "1", "OPENCODE_AUTO_SHARE": "0",
    })
    job = ControlledJob([str(executable), "--pure", "acp"], cwd, environment=environment, interactive=True)
    timed_out = False
    error = ""
    try:
        try:
            job.read_line(0.5)
        except TimeoutError:
            timed_out = True
        except Exception as exc:
            error = type(exc).__name__ + ":" + str(exc)
        job.close_stdin()
        exit_code = job.stop(timeout=10)
        facts = job.facts()
        stdout, stderr = job.output()
        (root / "idle.stdout.jsonl").write_bytes(stdout)
        (root / "idle.stderr.log").write_bytes(stderr)
        receipt = {
            "executable": str(executable), "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
            "argv": [str(executable), "--pure", "acp"], "cwd": str(cwd),
            "idle_read_timeout_seconds": 0.5, "idle_read_timed_out": timed_out, "error": error,
            "owned_stop_exit": exit_code, "stopped": job.stopped(), "retained_process_facts": facts,
            "stdout_sha256": hashlib.sha256(stdout).hexdigest(), "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        }
        (root / "idle-control.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    finally:
        job.dispose()
    print("REAL_IDLE_TIMEOUT=" + str(timed_out))
    print("REAL_IDLE_STOPPED=" + str(receipt["stopped"]))
    print("REAL_IDLE_EXIT=" + str(receipt["owned_stop_exit"]))
    return 0 if timed_out and receipt["stopped"] and all(item["stopped"] for item in receipt["retained_process_facts"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
