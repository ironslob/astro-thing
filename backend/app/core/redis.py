from __future__ import annotations

from typing import Any

import redis

from app.core.config import settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def set_redis(client: Any) -> None:
    global _client
    _client = client
