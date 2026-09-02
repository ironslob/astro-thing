"""Serve the API on IPv4 and IPv6.

Railway healthchecks connect over IPv4. Private networking between
services is IPv6. Binding only one family breaks one of those paths.
"""

from __future__ import annotations

import os
import socket

import uvicorn


def _listen_port() -> int:
    return int(os.environ.get("PORT", "8000"))


def bind_ipv4(port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.bind(("0.0.0.0", port))
    sock.listen(2048)
    sock.set_inheritable(True)
    return sock


def bind_ipv6(port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
    sock.bind(("::", port))
    sock.listen(2048)
    sock.set_inheritable(True)
    return sock


def bind_sockets(port: int) -> list[socket.socket]:
    return [bind_ipv4(port), bind_ipv6(port)]


def main() -> None:
    port = _listen_port()
    config = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
    uvicorn.Server(config).run(sockets=bind_sockets(port))


if __name__ == "__main__":
    main()
