from fastapi import APIRouter

from polynexus_core import __version__
from polynexus_core.api.dependencies import loopback_auth_configured
from polynexus_core.persistence.database import (
    relationship_integrity_status,
    schema_head_status,
)

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, object]:
    schema_ready = schema_head_status()
    integrity_ready = relationship_integrity_status()
    auth_ready = loopback_auth_configured()
    core_ready = schema_ready and integrity_ready
    bounded_ready = core_ready and auth_ready
    return {
        "status": "ok",
        "service": "polynexus-core",
        "version": __version__,
        "baseline": "development-v1.0",
        "readiness": "partial" if bounded_ready else "not_ready",
        "layers": {
            "process": {"status": "ready"},
            "schema": {"status": "ready" if schema_ready else "not_ready"},
            "database_integrity": {
                "status": "ready" if integrity_ready else "not_ready"
            },
            "core": {"status": "ready" if core_ready else "not_ready"},
            "api_auth": {"status": "ready" if auth_ready else "not_ready"},
            "web_client": {
                "status": "unknown",
                "reason": "not_observed_by_core",
            },
            "runtime": {
                "status": "unknown",
                "reason": "no_live_runtime_probe",
            },
        },
    }
