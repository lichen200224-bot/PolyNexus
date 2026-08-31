from pathlib import Path

from alembic import command as alembic_cmd
from alembic.config import Config
from fastapi.testclient import TestClient

from polynexus_core.app import create_app


def test_health_endpoint(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "health.db"
    config = Config()
    config.set_main_option(
        "script_location", str(Path(__file__).parent.parent / "alembic")
    )
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    alembic_cmd.upgrade(config, "head")

    monkeypatch.setenv("POLYNEXUS_DATABASE_URL", f"sqlite:///{db_path}")
    from polynexus_core.persistence.database import dispose_engine

    dispose_engine()
    try:
        with TestClient(create_app()) as client:
            response = client.get("/api/v1/health")
            assert response.status_code == 200
            payload = response.json()
            assert payload["status"] == "ok"
            assert payload["baseline"] == "development-v1.0"
    finally:
        dispose_engine()
