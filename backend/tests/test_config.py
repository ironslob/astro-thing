from __future__ import annotations

from app.core.config import sqlalchemy_database_url


def test_sqlalchemy_database_url_rewrites_railway_postgres() -> None:
    assert (
        sqlalchemy_database_url("postgresql://astro:pw@postgres.railway.internal:5432/railway")
        == "postgresql+psycopg://astro:pw@postgres.railway.internal:5432/railway"
    )
    assert (
        sqlalchemy_database_url("postgres://astro:pw@host:5432/db")
        == "postgresql+psycopg://astro:pw@host:5432/db"
    )


def test_sqlalchemy_database_url_leaves_sqlite_and_psycopg_alone() -> None:
    sqlite = "sqlite+pysqlite:///./ci.db"
    assert sqlalchemy_database_url(sqlite) == sqlite
    already = "postgresql+psycopg://astro:pw@localhost/db"
    assert sqlalchemy_database_url(already) == already
