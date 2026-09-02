from __future__ import annotations

import socket

from app.core.config import sqlalchemy_database_url
from app.run import bind_sockets


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


def test_bind_sockets_accept_ipv4_and_ipv6() -> None:
    port = 0
    # Port 0 cannot be shared across two sockets; pick one free port.
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    sockets = bind_sockets(port)
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1) as client:
            assert client.getpeername()[1] == port
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as client:
            client.settimeout(1)
            client.connect(("::1", port))
            assert client.getpeername()[1] == port
    finally:
        for sock in sockets:
            sock.close()
