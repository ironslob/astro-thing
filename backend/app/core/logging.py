from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "-"
        return True


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())
    fmt = logging.Formatter(
        '{"level":"%(levelname)s","logger":"%(name)s","request_id":"%(request_id)s",'
        '"message":"%(message)s"}'
    )
    handler.setFormatter(fmt)
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def coarse_coords(lat: float, lon: float) -> tuple[float, float]:
    """Round coordinates for operational logs (privacy)."""
    return round(lat, 1), round(lon, 1)
