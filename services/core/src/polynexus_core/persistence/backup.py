from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path


MAX_SQLITE_BYTES = 128 * 1024 * 1024
_SQLITE_HEADER = b"SQLite format 3\x00"
_SAFE_CODES = {
    "backup_copy_failed",
    "backup_integrity_failed",
    "backup_not_isolated",
    "backup_source_invalid",
    "backup_source_missing",
    "backup_target_exists",
    "backup_target_invalid",
    "backup_too_large",
    "backup_restore_failed",
}


class BackupRestoreError(RuntimeError):
    """Bounded failure for isolated SQLite backup/restore operations."""

    def __init__(self, code: str) -> None:
        safe_code = code if code in _SAFE_CODES else "backup_restore_failed"
        super().__init__(safe_code)
        self.code = safe_code


@dataclass(frozen=True)
class BackupReceipt:
    operation: str
    size_bytes: int
    sha256: str
    integrity: str = "ok"


def _isolated_root() -> Path:
    return Path(tempfile.gettempdir()).resolve()


def _validated_path(value: str | Path, *, source: bool) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise BackupRestoreError("backup_not_isolated")
    if path.is_symlink():
        raise BackupRestoreError("backup_not_isolated")
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(_isolated_root())
    except ValueError:
        raise BackupRestoreError("backup_not_isolated") from None
    if resolved == _isolated_root():
        raise BackupRestoreError("backup_not_isolated")
    if source and not resolved.exists():
        raise BackupRestoreError("backup_source_missing")
    if resolved.exists() and not resolved.is_file():
        raise BackupRestoreError("backup_source_invalid" if source else "backup_target_invalid")
    if not resolved.parent.is_dir():
        raise BackupRestoreError("backup_source_invalid" if source else "backup_target_invalid")
    return resolved


def _bounded_size(path: Path) -> int:
    try:
        size = path.stat().st_size
    except OSError:
        raise BackupRestoreError("backup_source_invalid") from None
    if size > MAX_SQLITE_BYTES:
        raise BackupRestoreError("backup_too_large")
    return size


def _sha256(path: Path, size: int | None = None) -> str:
    digest = hashlib.sha256()
    remaining = MAX_SQLITE_BYTES if size is None else size
    try:
        with path.open("rb") as stream:
            while remaining:
                chunk = stream.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                digest.update(chunk)
                remaining -= len(chunk)
    except OSError:
        raise BackupRestoreError("backup_source_invalid") from None
    return digest.hexdigest()


def _verify_sqlite(path: Path) -> tuple[int, str]:
    size = _bounded_size(path)
    try:
        with path.open("rb") as stream:
            if stream.read(len(_SQLITE_HEADER)) != _SQLITE_HEADER:
                raise BackupRestoreError("backup_integrity_failed")
        connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
        try:
            result = connection.execute("PRAGMA integrity_check").fetchone()
            if result != ("ok",):
                raise BackupRestoreError("backup_integrity_failed")
        finally:
            connection.close()
    except BackupRestoreError:
        raise
    except Exception:
        raise BackupRestoreError("backup_integrity_failed") from None
    return size, _sha256(path, size)


def create_sqlite_backup(source: str | Path, destination: str | Path) -> BackupReceipt:
    """Copy a verified temporary SQLite database without exposing its path."""
    source_path = _validated_path(source, source=True)
    destination_path = _validated_path(destination, source=False)
    if source_path == destination_path:
        raise BackupRestoreError("backup_target_invalid")
    if destination_path.exists():
        raise BackupRestoreError("backup_target_exists")
    _verify_sqlite(source_path)
    try:
        shutil.copy2(source_path, destination_path)
        size, digest = _verify_sqlite(destination_path)
    except BackupRestoreError:
        try:
            destination_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    except Exception:
        try:
            destination_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise BackupRestoreError("backup_copy_failed") from None
    return BackupReceipt("BACKUP", size, digest)


def restore_sqlite_backup(source: str | Path, destination: str | Path) -> BackupReceipt:
    """Atomically restore a verified temporary SQLite backup."""
    source_path = _validated_path(source, source=True)
    destination_path = _validated_path(destination, source=False)
    if source_path == destination_path:
        raise BackupRestoreError("backup_target_invalid")
    size, digest = _verify_sqlite(source_path)
    temporary_path = destination_path.with_name(destination_path.name + ".restore.tmp")
    if temporary_path.exists():
        raise BackupRestoreError("backup_target_invalid")
    try:
        shutil.copy2(source_path, temporary_path)
        restored_size, restored_digest = _verify_sqlite(temporary_path)
        if (restored_size, restored_digest) != (size, digest):
            raise BackupRestoreError("backup_integrity_failed")
        os.replace(temporary_path, destination_path)
        final_size, final_digest = _verify_sqlite(destination_path)
    except BackupRestoreError:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    except Exception:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise BackupRestoreError("backup_restore_failed") from None
    return BackupReceipt("RESTORE", final_size, final_digest)
