from fastapi import FastAPI

from polynexus_core.api.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="PolyNexus Core",
        version="0.1.0",
        description="Local-first multi-AI collaboration and validation core.",
    )
    app.include_router(health_router, prefix="/api/v1")
    return app


app = create_app()
