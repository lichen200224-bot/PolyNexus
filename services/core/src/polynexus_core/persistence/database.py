from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from polynexus_core.persistence.models import Base

_engine = None
_session_factory = None
_ALEMBIC_DIR = Path(__file__).resolve().parents[3] / "alembic"
_SCHEMA_NOT_AT_HEAD = "Database schema is not at the Alembic head"
_SCHEMA_VERSION_UNAVAILABLE = "Database schema version could not be verified"


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


def verify_schema_head() -> None:
    """Fail closed unless the initialized engine is at the Alembic head.

    Application startup never upgrades or creates schema implicitly.  The
    migration authority is discovered from the repository's Alembic script
    directory and compared with the single revision recorded in the target
    database.  All failures use bounded, public-safe messages.
    """
    if _engine is None:
        raise RuntimeError("Engine not initialized. Call init_engine() first.")

    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        if not _ALEMBIC_DIR.is_dir():
            raise RuntimeError(_SCHEMA_VERSION_UNAVAILABLE)
        alembic_config = Config()
        alembic_config.set_main_option("script_location", str(_ALEMBIC_DIR))
        heads = tuple(ScriptDirectory.from_config(alembic_config).get_heads())
        if len(heads) != 1:
            raise RuntimeError(_SCHEMA_VERSION_UNAVAILABLE)

        if "alembic_version" not in inspect(_engine).get_table_names():
            raise RuntimeError(_SCHEMA_NOT_AT_HEAD)
        with _engine.connect() as connection:
            revisions = tuple(
                connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalars().all()
            )
        if revisions != heads:
            raise RuntimeError(_SCHEMA_NOT_AT_HEAD)
    except RuntimeError:
        raise
    except Exception:
        raise RuntimeError(_SCHEMA_VERSION_UNAVAILABLE) from None


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
