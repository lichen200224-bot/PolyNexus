"""Read independent persisted facts from an isolated D2B-01 diagnostic run."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: readback_d2b01_production.py RAW_ROOT")
    root = Path(sys.argv[1]).resolve()
    receipt = json.loads((root / "production-run.json").read_text(encoding="utf-8"))
    staging = Path(receipt["launch_observations_before_effect"][0]["cwd"])
    source = root / "source-root" / "synthetic"
    with sqlite3.connect(root / "core.db") as db:
        db.row_factory = sqlite3.Row
        generation = dict(db.execute(
            "SELECT task_id, revision, control_revision, aborted, closed, ownership_unknown "
            "FROM work_generations WHERE task_id=? AND revision=?",
            (receipt["task_id"], receipt["generation"]["generation_revision"]),
        ).fetchone())
        run = dict(db.execute(
            "SELECT id, task_id, generation_revision, state, result_artifact_ids FROM runs WHERE id=?",
            (receipt["run_id"],),
        ).fetchone())
        binding = dict(db.execute(
            "SELECT run_id, runtime_profile_ref, adapter_id FROM run_binding_snapshots WHERE run_id=?",
            (receipt["run_id"],),
        ).fetchone())
        authorization = dict(db.execute(
            "SELECT authorization_id, run_id, state, issuer_class, policy_digest, policy_evidence_id "
            "FROM runtime_dispatch_authorizations WHERE run_id=?",
            (receipt["run_id"],),
        ).fetchone())
        events = [dict(row) for row in db.execute(
            "SELECT event_kind, from_state, to_state FROM runtime_dispatch_authorization_events "
            "WHERE authorization_id=? ORDER BY occurred_at",
            (authorization["authorization_id"],),
        )]
        evidence = [dict(row) for row in db.execute(
            "SELECT id, run_id, source, status FROM evidence WHERE run_id=? ORDER BY id",
            (receipt["run_id"],),
        )]
        artifacts = [dict(row) for row in db.execute(
            "SELECT id, run_id, storage_ref, sha256 FROM artifacts WHERE run_id=?",
            (receipt["run_id"],),
        )]
    files = {name: {
        "source_sha256": digest(source / name),
        "staging_sha256": digest(staging / name),
    } for name in ("bug.py", "test_bug.py")}
    result = {
        "run": run, "generation": generation, "binding": binding,
        "authorization": authorization, "authorization_events": events,
        "evidence": evidence, "artifacts": artifacts,
        "selected_source_files": files,
        "original_source_unchanged": files["bug.py"]["source_sha256"] == receipt["source_before_sha256"],
        "test_input_unchanged": files["test_bug.py"]["source_sha256"] == files["test_bug.py"]["staging_sha256"],
        "single_changed_path": files["bug.py"]["source_sha256"] != files["bug.py"]["staging_sha256"] and files["test_bug.py"]["source_sha256"] == files["test_bug.py"]["staging_sha256"],
    }
    (root / "production-readback.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )
    print("READBACK_RUN_STATE=" + run["state"])
    print("READBACK_GENERATION_CLOSED=" + str(generation["closed"]))
    print("READBACK_SINGLE_CHANGED_PATH=" + str(result["single_changed_path"]))
    print("READBACK_AUTH_CONSUMED_ONCE=" + str(sum(e["event_kind"] == "CONSUME" for e in events) == 1))
    return 0 if (
        run["state"] == "COMPLETED" and generation["closed"] == 1
        and result["original_source_unchanged"] and result["single_changed_path"]
        and authorization["state"] == "CONSUMED"
        and sum(e["event_kind"] == "CONSUME" for e in events) == 1
        and binding["run_id"] == run["id"]
        and len(artifacts) == 1 and artifacts[0]["run_id"] == run["id"]
        and {"runtime.routing_policy", "runtime.dispatch_authorization", "runtime.opencode.acp"}
        <= {e["source"] for e in evidence}
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
