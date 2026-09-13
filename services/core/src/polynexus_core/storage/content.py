"""Core-owned blobs. Locators are never accepted as evidence of identity.

All reads verify the metadata hash and length, including previously existing
content. The configured root must be private to Core. Reparse points are not
supported. No provider location is read implicitly.
"""
from __future__ import annotations
import hashlib
import os
import re
import stat
from pathlib import Path
from polynexus_core.domain.models import Artifact

MAX_CONTENT_BYTES = 16 * 1024 * 1024
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


class ContentError(ValueError):
    pass


def _plain(path: Path) -> None:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ContentError("content_path_unsupported")


class ContentStore:
    def __init__(self, root: Path):
        if not root.is_absolute():
            raise ContentError("content_root_invalid")
        # Reject reparse points throughout the configured ancestor chain.
        for ancestor in [root, *root.parents]:
            if ancestor.exists():
                _plain(ancestor)
        root.mkdir(parents=True, exist_ok=True)
        self.root = root.resolve(strict=True)

    def _path(self, digest: str) -> Path:
        if not _DIGEST.fullmatch(digest):
            raise ContentError("content_identity_invalid")
        _plain(self.root)
        return self.root / digest

    def put(self, content: bytes) -> tuple[str, int]:
        if not isinstance(content, bytes) or len(content) > MAX_CONTENT_BYTES:
            raise ContentError("content_size_invalid")
        digest = hashlib.sha256(content).hexdigest()
        path = self._path(digest)
        try:
            with path.open("xb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            pass
        self.read(digest, len(content))
        return digest, len(content)

    def read(self, digest: str, size: int) -> bytes:
        if size < 0 or size > MAX_CONTENT_BYTES:
            raise ContentError("content_size_invalid")
        path = self._path(digest)
        try:
            _plain(path)
            before = path.stat()
            if not stat.S_ISREG(before.st_mode):
                raise ContentError("content_path_unsupported")
            with path.open("rb") as stream:
                opened = os.fstat(stream.fileno())
                if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
                    raise ContentError("content_changed_during_read")
                content = stream.read(MAX_CONTENT_BYTES + 1)
                after = os.fstat(stream.fileno())
            _plain(path)
            current = path.stat()
            if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
                raise ContentError("content_changed_during_read")
            if (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino):
                raise ContentError("content_changed_during_read")
        except OSError:
            raise ContentError("content_unavailable") from None
        if len(content) != size or hashlib.sha256(content).hexdigest() != digest:
            raise ContentError("content_identity_mismatch")
        return content

    def read_artifact(self, artifact: Artifact) -> bytes:
        if artifact.storage_ref != "core-blob:" + artifact.sha256:
            raise ContentError("content_locator_unverified")
        return self.read(artifact.sha256, artifact.size)

    def delete(self, digest: str) -> None:
        # D1a retention is preserve-only: without complete Candidate/EvidenceSet
        # closure authority, collection cannot prove that a blob is unreferenced.
        self._path(digest)
        raise ContentError("content_retention_protected")
