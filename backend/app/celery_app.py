from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "astro_window",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    timezone="Europe/London",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    beat_schedule={
        "refresh-saved-locations-hourly": {
            "task": "app.workers.tasks.refresh_saved_locations",
            "schedule": crontab(minute=12),
        }
    },
)
