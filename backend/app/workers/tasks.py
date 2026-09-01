from __future__ import annotations

import logging
from datetime import datetime

from app.celery_app import celery_app
from app.core.db import SessionLocal
from app.core.redis import get_redis
from app.models.location import SavedLocation
from app.services.forecast import ForecastService
from app.services.saved import cells_for_locations, persist_assessment
from app.weather.cache import WeatherCacheService
from app.weather.open_meteo import OpenMeteoWeatherProvider
from app.weather.provider import WeatherProviderError

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.refresh_saved_locations")
def refresh_saved_locations() -> dict:
    db = SessionLocal()
    refreshed = 0
    skipped = 0
    errors = 0
    try:
        locations = db.query(SavedLocation).all()
        grouped = cells_for_locations(locations)
        redis = get_redis()
        cache = WeatherCacheService(db=db, provider=OpenMeteoWeatherProvider(), redis_client=redis)
        service = ForecastService(db, cache)
        for cell, group in grouped.items():
            sample = group[0]
            try:
                payload = service.windows(sample.latitude, sample.longitude)
            except WeatherProviderError:
                logger.warning("refresh_cell_failed cell=%s", cell)
                errors += 1
                continue
            fetched = None
            stamp = payload.get("forecast", {}).get("fetched_at")
            if stamp:
                fetched = datetime.fromisoformat(stamp)
            for loc in group:
                written = persist_assessment(db, loc.id, payload, fetched)
                if written:
                    refreshed += 1
                else:
                    skipped += 1
        logger.info("refresh_done written=%s skipped=%s errors=%s", refreshed, skipped, errors)
        return {"written": refreshed, "skipped": skipped, "errors": errors}
    finally:
        db.close()
