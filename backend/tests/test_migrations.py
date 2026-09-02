from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import settings
from app.core.db import Base

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _alembic_config() -> Config:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    return cfg


def test_alembic_upgrade_matches_orm_schema(tmp_path, monkeypatch) -> None:
    url = f"sqlite+pysqlite:///{tmp_path / 'schema.db'}"
    monkeypatch.setattr(settings, "database_url", url)

    command.upgrade(_alembic_config(), "head")

    inspector = inspect(create_engine(url))
    db_tables = set(inspector.get_table_names()) - {"alembic_version"}
    assert db_tables == set(Base.metadata.tables)
    assert "uk_places" not in db_tables

    command.check(_alembic_config())
