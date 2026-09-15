"""Build and verify SHA-256 for every published D2B-01 evidence file."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "MANIFEST.sha256"


def evidence_files() -> list[Path]:
    return sorted((path for path in ROOT.rglob("*") if path.is_file() and path != MANIFEST),
                  key=lambda path: path.relative_to(ROOT).as_posix())


def main() -> None:
    rows = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}"
            for path in evidence_files()]
    MANIFEST.write_bytes(("\n".join(rows) + "\n").encode("utf-8"))
    for row in MANIFEST.read_text(encoding="utf-8").splitlines():
        digest, relative = row.split("  ", 1)
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != digest:
            raise ValueError("manifest mismatch: " + relative)
    print("MANIFEST_FILES=" + str(len(rows)))
    print("MANIFEST_SHA256=" + hashlib.sha256(MANIFEST.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
