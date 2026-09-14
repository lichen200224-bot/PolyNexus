from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from polynexus_core.api.generations import router as generations_router
from polynexus_core.api.artifacts import router as artifacts_router
from polynexus_core.api.health import router as health_router
from polynexus_core.api.projects import router as projects_router
from polynexus_core.api.tasks import router as tasks_router
from polynexus_core.api.runs import router as runs_router
from polynexus_core.api.context_packages import router as context_packages_router
from polynexus_core.api.run_outputs import router as run_outputs_router
from polynexus_core.api.d1b import router as d1b_router


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Startup/shutdown lifecycle for the default application.

    On startup: initialise the database engine and verify the Alembic head.
    On shutdown: dispose the engine to release connections.

    The database URL is read from the POLYNEXUS_DATABASE_URL environment
    variable, falling back to ``sqlite:///poly.db`` (production default).
    """
    from polynexus_core.persistence.database import (
        dispose_engine,
        get_session,
        init_engine,
        verify_relationship_integrity,
        verify_schema_head,
    )
    from polynexus_core.runtime.reconciliation import reconcile_non_terminal_runs

    database_url = os.environ.get("POLYNEXUS_DATABASE_URL", "sqlite:///poly.db")
    init_engine(database_url)
    try:
        # Alembic is the only schema authority.  Startup never creates or
        # upgrades schema implicitly and fails closed on an unknown/non-head
        # revision.
        verify_schema_head()
        verify_relationship_integrity()

        # A restart must never resubmit a durable Run.  Reconcile existing
        # non-terminal Runs only after the schema exists and before serving routes.
        # The generator is closed explicitly so the startup transaction is owned
        # here rather than relying on request-scoped dependency cleanup.
        startup_session_generator = get_session()
        startup_session = next(startup_session_generator)
        try:
            await reconcile_non_terminal_runs(startup_session)
            startup_session.commit()
        except asyncio.CancelledError:
            # Persist the reconciler's fail-closed current Run before the
            # startup task unwinds; synchronous commit cannot be interrupted.
            startup_session.commit()
            raise
        except Exception:
            startup_session.rollback()
            raise
        finally:
            startup_session_generator.close()

        yield
    finally:
        # Startup failures are fail-closed, but must not leak the engine.
        dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title="PolyNexus Core",
        version="0.1.0",
        description="Local-first multi-AI collaboration and validation core.",
        lifespan=_lifespan,
    )
    app.include_router(generations_router, prefix="/api/v1")
    app.include_router(artifacts_router, prefix="/api/v1")
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(tasks_router, prefix="/api/v1")
    app.include_router(runs_router, prefix="/api/v1")
    app.include_router(context_packages_router, prefix="/api/v1")
    app.include_router(run_outputs_router, prefix="/api/v1")
    app.include_router(d1b_router, prefix="/api/v1")
    return app


app = create_app()
