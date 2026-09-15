"""Scan publication bytes for credential values and unnormalized personal paths."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PATTERNS = (
    re.compile(rb"(?i)sk-[a-z0-9_-]{12,}"),
    re.compile(rb"(?i)bearer\s+[a-z0-9._-]{12,}"),
    re.compile(rb"(?i)(?:ghp_|github_pat_|xox[baprs]-)[a-z0-9_-]{12,}"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"(?i)(?:api[_-]?key|password|cookie|secret|credential)\s*[:=]\s*['\"]?[a-z0-9+/=_-]{12,}"),
    re.compile(rb'(?i)"(?:clientDataJSON|authenticatorData|attestationObject|credentialId)"\s*:\s*"[A-Za-z0-9+/=_-]{20,}"'),
)


def main() -> int:
    extra = [Path(value) for value in sys.argv[1:]]
    files = sorted(path for path in ROOT.rglob("*") if path.is_file()) + extra
    home = str(Path.home())
    variants = tuple(home.replace("\\", "\\" * count).encode() for count in (1, 2, 4, 8))
    for path in files:
        data = path.read_bytes()
        if path.is_relative_to(ROOT) and any(value in data for value in variants):
            raise ValueError("unnormalized personal home: " + str(path))
        for pattern in PATTERNS:
            if pattern.search(data):
                raise ValueError("secret-like value: " + str(path))
    print("SECRET_SCAN=PASS")
    print("FILES_SCANNED=" + str(len(files)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
