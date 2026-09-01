from __future__ import annotations

import time

from fastapi import HTTPException, Request, status

from app.api.deps import client_ip
from app.core.config import settings
from app.core.redis import get_redis


def enforce_forecast_rate_limit(request: Request) -> None:
    ip = client_ip(request)
    key = f"rl:forecast:{ip}"
    try:
        redis = get_redis()
        current = redis.incr(key)
        if current == 1:
            redis.expire(key, 60)
        if current > settings.forecast_rate_limit_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Slow down a little — try again in a minute.",
            )
    except HTTPException:
        raise
    except Exception:
        # Redis optional for rate limits in unit tests without a server.
        return
    _ = time.time()
