from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from polynexus_core.persistence.models import Base

_engine = None
_session_factory = None


def init_engine(database_url: str | None = None) -> None:
    global _engine, _session_factory
    if database_url is None:
        database_url = "sqlite:///poly.db"
    _engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        future=True,
    )
    if "sqlite" in _engine.url.database:
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    _session_factory = sessionmaker(bind=_engine, expire_on_commit=False, future=True)


def create_all() -> None:
    if _engine is None:
        raise RuntimeError("Engine not initialized. Call init_engine() first.")
    Base.metadata.create_all(_engine)


def drop_all() -> None:
    if _engine is None:
        raise RuntimeError("Engine not initialized. Call init_engine() first.")
    Base.metadata.drop_all(_engine)


def get_session() -> Generator[Session, None, None]:
    if _session_factory is None:
        raise RuntimeError("Session factory not initialized. Call init_engine() first.")
    session = _session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_engine():
    if _engine is None:
        raise RuntimeError("Engine not initialized. Call init_engine() first.")
    return _engine


def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _session_factory = None
