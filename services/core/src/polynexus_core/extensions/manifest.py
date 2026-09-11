"""Versioned, non-secret module metadata. Declarations are not evidence."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from polynexus_core.domain.runtime_binding import (
    RuntimeBindingError, validate_opaque_identifier,
)


class ModuleError(RuntimeBindingError):
    """Fixed public-safe extension contract rejection."""


class ModuleType(StrEnum):
    RUNTIME = "RUNTIME"
    TOOL = "TOOL"
    SURFACE = "SURFACE"
    INTEGRATION = "INTEGRATION"


class ConfigBoundary(StrEnum):
    NO_CONFIG = "NO_CONFIG"


class LifecycleBoundary(StrEnum):
    STATIC = "STATIC"


class HealthBoundary(StrEnum):
    RUNTIME_PROBE = "RUNTIME_PROBE"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class SecurityBoundary(StrEnum):
    CORE_POLICY = "CORE_POLICY"


class ModuleMaturity(StrEnum):
    # No self-issued supported/certified state in this foundation.
    EXPERIMENTAL = "EXPERIMENTAL"


class ConformanceScope(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    DETERMINISTIC_LOCAL_CONFORMANCE = "DETERMINISTIC_LOCAL_CONFORMANCE"


def identifier(value: object) -> str:
    try:
        result = validate_opaque_identifier(value, "module identifier")
        # The existing grammar uses match(); require the entire string here.
        if result != result.strip():
            raise ValueError
        return result
    except (RuntimeBindingError, ValueError):
        raise ModuleError("Invalid module identifier") from None


def normalize_capabilities(values: object) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)) or len(values) > 64:
        raise ModuleError("Invalid module capability declaration")
    try:
        normalized = tuple(sorted({identifier(value) for value in values}))
    except ModuleError:
        raise ModuleError("Invalid module capability declaration") from None
    return normalized


@dataclass(frozen=True)
class ModuleManifest:
    module_id: str
    module_type: ModuleType
    module_version: str
    capabilities: tuple[str, ...] = ()
    contract_version: int = 1
    provider_id: str | None = None
    config: ConfigBoundary = ConfigBoundary.NO_CONFIG
    lifecycle: LifecycleBoundary = LifecycleBoundary.STATIC
    health: HealthBoundary = HealthBoundary.NOT_IMPLEMENTED
    security: SecurityBoundary = SecurityBoundary.CORE_POLICY
    maturity: ModuleMaturity = ModuleMaturity.EXPERIMENTAL
    conformance_scope: ConformanceScope = ConformanceScope.UNVERIFIED

    def __post_init__(self) -> None:
        identifier(self.module_id)
        if self.provider_id is not None:
            identifier(self.provider_id)
        if type(self.contract_version) is not int or self.contract_version != 1:
            raise ModuleError("Unsupported module contract version")
        if (
            not isinstance(self.module_version, str)
            or len(self.module_version) > 32
            or re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", self.module_version) is None
        ):
            raise ModuleError("Invalid module version")
        for value, kind in (
            (self.module_type, ModuleType), (self.config, ConfigBoundary),
            (self.lifecycle, LifecycleBoundary), (self.health, HealthBoundary),
            (self.security, SecurityBoundary), (self.maturity, ModuleMaturity),
            (self.conformance_scope, ConformanceScope),
        ):
            if not isinstance(value, kind):
                raise ModuleError("Invalid module boundary declaration")
        if self.module_type is not ModuleType.RUNTIME and self.health is not HealthBoundary.NOT_IMPLEMENTED:
            raise ModuleError("Executable health contract is unavailable for module type")
        object.__setattr__(self, "capabilities", normalize_capabilities(self.capabilities))
