"""Metadata and enablement only: this is not a runtime profile registry."""
from __future__ import annotations

from polynexus_core.extensions.manifest import (
    ModuleError, ModuleManifest, identifier, normalize_capabilities,
)


class ModuleRegistry:
    """Single-threaded static composition; disabling prevents new resolutions.

    Enablement is in-memory. It neither cancels active Runs nor rewrites their
    binding history. No install/remove/update or executable loading API exists.
    """

    def __init__(self) -> None:
        self._manifests: dict[str, ModuleManifest] = {}
        self._enabled: dict[str, bool] = {}

    def register(self, manifest: ModuleManifest) -> None:
        if type(manifest) is not ModuleManifest:
            raise ModuleError("Invalid module manifest")
        manifest.__post_init__()
        existing = self._manifests.get(manifest.module_id)
        if existing is not None and existing != manifest:
            raise ModuleError("Conflicting module registration")
        self._manifests[manifest.module_id] = manifest
        self._enabled.setdefault(manifest.module_id, True)

    def contains(self, module_id: str) -> bool:
        return identifier(module_id) in self._manifests

    def resolve(self, module_id: str, *, required_capabilities: tuple[str, ...] = ()) -> ModuleManifest:
        key = identifier(module_id)
        manifest = self._manifests.get(key)
        if manifest is None or not self._enabled[key]:
            raise ModuleError("Unknown or disabled module")
        required = normalize_capabilities(required_capabilities)
        if not set(required).issubset(manifest.capabilities):
            raise ModuleError("Module capability request is unavailable")
        return manifest

    def set_enabled(self, module_id: str, enabled: bool) -> None:
        key = identifier(module_id)
        if key not in self._manifests or type(enabled) is not bool:
            raise ModuleError("Invalid module enablement request")
        self._enabled[key] = enabled
