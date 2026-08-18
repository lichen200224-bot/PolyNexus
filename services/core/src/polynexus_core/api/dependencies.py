"""API dependencies for authenticated loopback access and database session injection."""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from polynexus_core.persistence.database import get_session

# Production loopback token — read from environment at startup.
# When set: only requests presenting the exact token are allowed.
# When empty/not set: ALL non-health requests are denied (fail closed).
_LOOPBACK_TOKEN = os.environ.get("LOOPBACK_TOKEN", "")


def require_loopback(
    x_loopback_token: Annotated[str | None, Header()] = None,
) -> None:
    """Authenticated loopback boundary.

    Production behaviour:
      - If LOOPBACK_TOKEN env var is set, the request must present it via
        X-Loopback-Token header. Missing/incorrect token → 403.
      - If LOOPBACK_TOKEN env var is NOT set (empty string), ALL requests
        are denied (fail closed). An arbitrary non-empty header does NOT
        constitute authentication.

    This never allows anonymous or remote callers.  No secret value is
    written to DB, Domain, Evidence, log, or response.
    """
    if not _LOOPBACK_TOKEN:
        # No credential verifier configured — fail closed for all callers.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Loopback authentication not configured",
        )
    if x_loopback_token != _LOOPBACK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid loopback token",
        )


def get_db_session(session: Session = Depends(get_session)) -> Session:
    """Yield a SQLAlchemy session for the request lifetime."""
    return session


# Type alias for FastAPI Depends annotation
DbSession = Annotated[Session, Depends(get_db_session)]
AuthLoopback = Annotated[None, Depends(require_loopback)]
