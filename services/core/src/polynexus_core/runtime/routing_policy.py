"""Fail-closed local routing policy for CP-04 WP-18.

This module contains no connector or vendor behavior.  It validates the
classification, loopback endpoint boundary, timeout, and normalized runtime
capabilities before a local adapter is allowed to make a request.
"""
from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable
from urllib.parse import SplitResult, urlsplit

from polynexus_core.domain.enums import AuthOwnership, ResumeMode, UsageVisibility
from polynexus_core.domain.runtime_binding import RuntimeBindingError


class DataClassification(StrEnum):
    """Bounded request classifications used by the local-only route."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


LOCAL_ONLY_ROUTE = "LOCAL_ONLY"
LOOPBACK_ENDPOINT_IDENTITY = "loopback"
MIN_TIMEOUT_SECONDS = 0.1
MAX_TIMEOUT_SECONDS = 120.0
MAX_MODEL_ID_LENGTH = 128
MAX_ENDPOINT_PATH_LENGTH = 128

_MODEL_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_CAPABILITY_NAMES = frozenset(
    {
        "cancel",
        "resume",
        "artifacts",
        "timeout_cleanup_verified",
        "usage_visibility",
        "auth_ownership",
    }
)


@dataclass(frozen=True, slots=True)
class LocalRouteDecision:
    """Safe route facts; no raw endpoint URL is retained in the decision."""

    classification: DataClassification
    endpoint_identity: str
    model_identity: str
    route: str
    timeout_seconds: float


@dataclass(frozen=True, slots=True)
class LocalRouteEvidence:
    """Bounded safe evidence for a local route probe or request."""

    endpoint_identity: str
    model_identity: str
    route: str
    timeout_seconds: float
    safe_error: str | None = None

    def __post_init__(self) -> None:
        if self.endpoint_identity != LOOPBACK_ENDPOINT_IDENTITY:
            raise RuntimeBindingError("Local route evidence is invalid")
        if self.route != LOCAL_ONLY_ROUTE:
            raise RuntimeBindingError("Local route evidence is invalid")
        validate_model_identity(self.model_identity)
        validate_timeout(self.timeout_seconds)
        if self.safe_error is not None and self.safe_error not in {
            "local_endpoint_cancel_unsupported",
            "local_endpoint_request_failed",
            "local_endpoint_response_invalid",
            "local_endpoint_timeout",
            "local_endpoint_resume_unsupported",
        }:
            raise RuntimeBindingError("Local route evidence is invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "endpoint_identity": self.endpoint_identity,
            "model_identity": self.model_identity,
            "route": self.route,
            "timeout_seconds": self.timeout_seconds,
            "safe_error": self.safe_error,
        }


def validate_classification(value: object) -> DataClassification:
    if isinstance(value, DataClassification):
        return value
    if isinstance(value, str):
        try:
            return DataClassification(value.upper())
        except ValueError:
            pass
    raise RuntimeBindingError("Runtime route classification is unsupported")


def validate_loopback_endpoint(endpoint_url: object) -> SplitResult:
    """Validate an HTTP(S) endpoint without exposing it in any error."""

    if not isinstance(endpoint_url, str) or not endpoint_url or len(endpoint_url) > 512:
        raise RuntimeBindingError("Local endpoint policy rejected the endpoint")
    try:
        parsed = urlsplit(endpoint_url)
        hostname = parsed.hostname
        port = parsed.port
    except (ValueError, TypeError):
        raise RuntimeBindingError("Local endpoint policy rejected the endpoint") from None
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeBindingError("Local endpoint policy rejected the endpoint")
    if parsed.username is not None or parsed.password is not None:
        raise RuntimeBindingError("Local endpoint policy rejected the endpoint")
    if parsed.query or parsed.fragment or hostname is None:
        raise RuntimeBindingError("Local endpoint policy rejected the endpoint")
    if len(parsed.path) > MAX_ENDPOINT_PATH_LENGTH:
        raise RuntimeBindingError("Local endpoint policy rejected the endpoint")
    normalized_host = hostname.rstrip(".").lower()
    is_localhost = normalized_host == "localhost"
    try:
        is_loopback = ipaddress.ip_address(normalized_host).is_loopback
    except ValueError:
        is_loopback = False
    if not is_localhost and not is_loopback:
        raise RuntimeBindingError("Local endpoint policy rejected the endpoint")
    if port is not None and not 1 <= port <= 65535:
        raise RuntimeBindingError("Local endpoint policy rejected the endpoint")
    return parsed


def validate_model_identity(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_MODEL_ID_LENGTH
        or _MODEL_ID_PATTERN.fullmatch(value) is None
    ):
        raise RuntimeBindingError("Local endpoint model identity is invalid")
    lowered = value.lower()
    if any(marker in lowered for marker in ("secret", "token", "password", "apikey", "cookie")):
        raise RuntimeBindingError("Local endpoint model identity is invalid")
    return value


def validate_timeout(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeBindingError("Local endpoint timeout is invalid")
    timeout = float(value)
    if timeout != timeout or timeout < MIN_TIMEOUT_SECONDS or timeout > MAX_TIMEOUT_SECONDS:
        raise RuntimeBindingError("Local endpoint timeout is invalid")
    return timeout


def validate_capability_compatibility(
    capabilities: object,
    required_capabilities: Iterable[str] = (),
) -> None:
    """Require every requested normalized capability; never downgrade."""

    try:
        required = tuple(required_capabilities)
    except Exception:
        raise RuntimeBindingError(
            "Runtime route capability compatibility check failed"
        ) from None
    if any(
        not isinstance(name, str) or name not in _CAPABILITY_NAMES
        for name in required
    ):
        raise RuntimeBindingError("Runtime route capability compatibility check failed")
    try:
        for name in required:
            value = getattr(capabilities, name)
            if name in {"cancel", "artifacts", "timeout_cleanup_verified"}:
                satisfied = value is True
            elif name == "resume":
                satisfied = isinstance(value, ResumeMode) and value is not ResumeMode.NONE
            elif name == "usage_visibility":
                satisfied = (
                    isinstance(value, UsageVisibility)
                    and value is not UsageVisibility.UNAVAILABLE
                )
            elif name == "auth_ownership":
                satisfied = isinstance(value, AuthOwnership)
            else:
                satisfied = False
            if not satisfied:
                raise RuntimeBindingError(
                    "Runtime route capability compatibility check failed"
                )
    except RuntimeBindingError:
        raise
    except Exception:
        raise RuntimeBindingError(
            "Runtime route capability compatibility check failed"
        ) from None


def evaluate_local_route(
    *,
    classification: object,
    endpoint_url: object,
    model_identity: object,
    timeout_seconds: object,
    capabilities: object,
    required_capabilities: Iterable[str] = (),
) -> LocalRouteDecision:
    """Return a route only when every local-only policy check passes."""

    selected_classification = validate_classification(classification)
    validate_loopback_endpoint(endpoint_url)
    selected_model = validate_model_identity(model_identity)
    selected_timeout = validate_timeout(timeout_seconds)
    validate_capability_compatibility(capabilities, required_capabilities)
    return LocalRouteDecision(
        classification=selected_classification,
        endpoint_identity=LOOPBACK_ENDPOINT_IDENTITY,
        model_identity=selected_model,
        route=LOCAL_ONLY_ROUTE,
        timeout_seconds=selected_timeout,
    )
