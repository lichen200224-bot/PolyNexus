"""Deterministically normalize personal home paths in D2B-01 raw evidence.

Run outside Git checkout data sources. Reject a secret-bearing input instead of
publishing it; any such input requires an explicit deterministic redaction rule.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

HOME = Path.home()
PATTERNS = (
    re.compile(rb"(?i)sk-[a-z0-9_-]{12,}"),
    re.compile(rb"(?i)bearer\s+[a-z0-9._-]{12,}"),
    re.compile(rb"(?i)(?:ghp_|github_pat_|xox[baprs]-)[a-z0-9_-]{12,}"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"(?i)authorization\s*[:=]\s*['\"]?(?:basic|bearer)\s+[a-z0-9+/=_-]{12,}"),
    re.compile(rb"(?i)(?:api[_-]?key|token|password|cookie|secret|credential)\s*[:=]\s*['\"]?[a-z0-9+/=_-]{12,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"(?i)webauthn|passkey"),
)


def normalize(data: bytes) -> bytes:
    # Both JSON-escaped and direct Windows/slash paths are represented in logs.
    variants = (str(HOME).encode(), str(HOME).replace("\\", "\\\\").encode(),
                str(HOME).replace("\\", "/").encode())
    for variant in sorted(set(variants), key=len, reverse=True):
        data = data.replace(variant, b"<USER_HOME>")
    return data


def scan(data: bytes, source: Path) -> None:
    matches = sum(len(pattern.findall(data)) for pattern in PATTERNS)
    if matches:
        raise ValueError(f"secret-like material detected in {source.name}: {matches} matches; publication stopped")


def publish(source: Path, target: Path) -> None:
    raw = source.read_bytes()
    scan(raw, source)
    safe = normalize(raw)
    scan(safe, source)
    if b"C:\\Users\\shawn" in safe or b"C:\\\\Users\\\\shawn" in safe:
        raise ValueError(f"unredacted personal home in {source.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(safe)
    print(f"{target.relative_to(Path(__file__).parent)} bytes={len(safe)} raw_sha256={hashlib.sha256(raw).hexdigest()} sanitized_sha256={hashlib.sha256(safe).hexdigest()}")


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit("usage: SANITIZE.py REAL_ROOT CONTROL_ROOT VALIDATION_ROOT OUT_DIR")
    real, control, validation, out = (Path(value).resolve() for value in sys.argv[1:])
    pairs = (
        (real / "real-run.json", out / "real-run.json"),
        (real / "acp.stdout.jsonl", out / "acp.stdout.jsonl"),
        (real / "acp.stderr.log", out / "acp.stderr.log"),
        (real / "postcondition.stdout.log", out / "postcondition.stdout.log"),
        (real / "postcondition.stderr.log", out / "postcondition.stderr.log"),
        (real / "synthetic-source" / "bug.py", out / "source-before" / "bug.py"),
        (real / "synthetic-source" / "test_bug.py", out / "source-before" / "test_bug.py"),
        (real / "staging_4a9577ae2ecdafecf040ab61" / "bug.py", out / "source-after" / "bug.py"),
        (control / "idle-control.json", out / "idle-control.json"),
        (control / "idle.stdout.jsonl", out / "idle.stdout.jsonl"),
        (control / "idle.stderr.log", out / "idle.stderr.log"),
        (validation / "targeted.log", out / "targeted.log"),
        (validation / "affected.log", out / "affected.log"),
        (validation / "full-core.log", out / "full-core.log"),
        (validation / "full-core-final.log", out / "full-core-final.log"),
    )
    for source, target in pairs:
        publish(source, target)


if __name__ == "__main__":
    main()
