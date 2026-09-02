from __future__ import annotations

import socket

from app.core.config import sqlalchemy_database_url
from app.run import bind_dualstack


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


def test_bind_dualstack_accepts_ipv4() -> None:
    sock = bind_dualstack(0)
    try:
        port = sock.getsockname()[1]
        with socket.create_connection(("127.0.0.1", port), timeout=1) as client:
            assert client.getpeername()[1] == port
    finally:
        sock.close()
