from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.core.db import engine
from app.core.redis import get_redis

router = APIRouter()


@router.get("/health")
def health() -> dict:
    db_ok = True
    redis_ok = True
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception:
        db_ok = False
    try:
        get_redis().ping()
    except Exception:
        redis_ok = False
    status = "ok" if db_ok else "degraded"
    return {
        "status": status,
        "environment": settings.environment,
        "database": db_ok,
        "redis": redis_ok,
        "scoring_version": settings.scoring_version,
    }
