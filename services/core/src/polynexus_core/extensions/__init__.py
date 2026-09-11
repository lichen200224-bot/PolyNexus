"""V1 static extension descriptors; execution remains owned by the runtime layer."""
from polynexus_core.extensions.manifest import (
    ConfigBoundary, ConformanceScope, HealthBoundary, LifecycleBoundary,
    ModuleError, ModuleManifest, ModuleMaturity, ModuleType, SecurityBoundary,
)
from polynexus_core.extensions.registry import ModuleRegistry
from polynexus_core.extensions.runtime_bridge import RuntimeModuleBridge, ModuleHealth

__all__ = [
    "ConfigBoundary", "ConformanceScope", "HealthBoundary", "LifecycleBoundary",
    "ModuleError", "ModuleManifest", "ModuleMaturity", "ModuleType",
    "SecurityBoundary", "ModuleRegistry", "RuntimeModuleBridge", "ModuleHealth",
]
