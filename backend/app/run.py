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


def bind_dualstack(port: int) -> socket.socket:
    sock = socket.create_server(
        ("::", port),
        family=socket.AF_INET6,
        dualstack_ipv6=True,
    )
    sock.set_inheritable(True)
    return sock


def main() -> None:
    port = _listen_port()
    config = uvicorn.Config(
        "app.main:app",
        host="::",
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
    config.bind_socket = lambda: bind_dualstack(port)  # type: ignore[method-assign]
    uvicorn.Server(config).run()


if __name__ == "__main__":
    main()
