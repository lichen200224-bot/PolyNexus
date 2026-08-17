from fastapi import APIRouter

from polynexus_core import __version__

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "polynexus-core",
        "version": __version__,
        "baseline": "development-v1.0",
    }
