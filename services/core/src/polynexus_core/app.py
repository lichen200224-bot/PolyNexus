from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from polynexus_core.api.health import router as health_router
from polynexus_core.api.projects import router as projects_router
from polynexus_core.api.tasks import router as tasks_router
from polynexus_core.api.runs import router as runs_router
from polynexus_core.api.context_packages import router as context_packages_router
from polynexus_core.api.run_outputs import router as run_outputs_router


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Startup/shutdown lifecycle for the default application.

    On startup: initialise the database engine and create all tables.
    On shutdown: dispose the engine to release connections.

    The database URL is read from the POLYNEXUS_DATABASE_URL environment
    variable, falling back to ``sqlite:///poly.db`` (production default).
    """
    from polynexus_core.persistence.database import create_all, dispose_engine, init_engine

    database_url = os.environ.get("POLYNEXUS_DATABASE_URL", "sqlite:///poly.db")
    init_engine(database_url)
    create_all()

    yield

    dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title="PolyNexus Core",
        version="0.1.0",
        description="Local-first multi-AI collaboration and validation core.",
        lifespan=_lifespan,
    )
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(tasks_router, prefix="/api/v1")
    app.include_router(runs_router, prefix="/api/v1")
    app.include_router(context_packages_router, prefix="/api/v1")
    app.include_router(run_outputs_router, prefix="/api/v1")
    return app


app = create_app()
