from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import coarse_coords
from app.domain.models import HourlyWeather, NormalizedForecast
from app.models.weather import WeatherForecastCache
from app.weather.geocell import cell_key
from app.weather.provider import WeatherProvider, WeatherProviderError

logger = logging.getLogger(__name__)

LOCK_TTL = 20
LOCK_WAIT_SECONDS = 8


def forecast_to_payload(forecast: NormalizedForecast) -> dict[str, Any]:
    return {
        "provider": forecast.provider,
        "source_label": forecast.source_label,
        "fetched_at": forecast.fetched_at.isoformat(),
        "forecast_start": forecast.forecast_start.isoformat(),
        "forecast_end": forecast.forecast_end.isoformat(),
        "stale": forecast.stale,
        "hours": [
            {
                "time": h.time.isoformat(),
                "cloud_cover": h.cloud_cover,
                "cloud_low": h.cloud_low,
                "cloud_mid": h.cloud_mid,
                "cloud_high": h.cloud_high,
                "visibility": h.visibility,
                "relative_humidity": h.relative_humidity,
                "precipitation": h.precipitation,
                "precipitation_probability": h.precipitation_probability,
                "wind_speed": h.wind_speed,
                "wind_gusts": h.wind_gusts,
            }
            for h in forecast.hours
        ],
    }


def payload_to_forecast(payload: dict[str, Any], *, stale: bool) -> NormalizedForecast:
    hours = [
        HourlyWeather(
            time=datetime.fromisoformat(h["time"]),
            cloud_cover=h["cloud_cover"],
            cloud_low=h.get("cloud_low"),
            cloud_mid=h.get("cloud_mid"),
            cloud_high=h.get("cloud_high"),
            visibility=h.get("visibility"),
            relative_humidity=h.get("relative_humidity"),
            precipitation=h.get("precipitation") or 0.0,
            precipitation_probability=h.get("precipitation_probability") or 0.0,
            wind_speed=h.get("wind_speed") or 0.0,
            wind_gusts=h.get("wind_gusts"),
        )
        for h in payload["hours"]
    ]
    return NormalizedForecast(
        hours=hours,
        provider=payload.get("provider", "open-meteo"),
        fetched_at=datetime.fromisoformat(payload["fetched_at"]),
        forecast_start=datetime.fromisoformat(payload["forecast_start"]),
        forecast_end=datetime.fromisoformat(payload["forecast_end"]),
        source_label=payload.get("source_label", "Open-Meteo"),
        stale=stale,
    )


class WeatherCacheService:
    def __init__(
        self,
        db: Session,
        provider: WeatherProvider,
        redis_client: Any | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        self.db = db
        self.provider = provider
        self.redis = redis_client
        self.now_fn = now_fn or (lambda: datetime.now(UTC))
        self.provider_calls = 0
        self.last_cache_hit = False
        self.last_stale = False

    def get(self, latitude: float, longitude: float) -> NormalizedForecast:
        key = cell_key(latitude, longitude)
        now = self.now_fn()
        row = self.db.get(WeatherForecastCache, key)
        fresh_after = now - timedelta(seconds=settings.weather_cache_ttl_seconds)
        stale_after = now - timedelta(seconds=settings.weather_stale_ttl_seconds)

        if row and row.fetched_at.replace(tzinfo=row.fetched_at.tzinfo or UTC) >= fresh_after:
            self.last_cache_hit = True
            self.last_stale = False
            logger.info("weather_cache hit cell=%s", key)
            return payload_to_forecast(row.payload, stale=False)

        lock_key = f"weather:lock:{key}"
        token = self._acquire_lock(lock_key)
        try:
            # Re-check after lock (another worker may have filled the cache).
            self.db.expire_all()
            row = self.db.get(WeatherForecastCache, key)
            if row and row.fetched_at.replace(tzinfo=row.fetched_at.tzinfo or UTC) >= fresh_after:
                self.last_cache_hit = True
                self.last_stale = False
                return payload_to_forecast(row.payload, stale=False)
            try:
                t0 = time.perf_counter()
                forecast = self.provider.fetch(latitude, longitude)
                forecast.fetched_at = self.now_fn()
                latency_ms = int((time.perf_counter() - t0) * 1000)
                self.provider_calls += 1
                self.last_cache_hit = False
                self.last_stale = False
                logger.info(
                    "weather_provider ok cell=%s latency_ms=%s coords=%s",
                    key,
                    latency_ms,
                    coarse_coords(latitude, longitude),
                )
                self._store(key, forecast)
                return forecast
            except WeatherProviderError:
                logger.warning("weather_provider failure cell=%s", key, exc_info=True)
                if (
                    row
                    and row.fetched_at.replace(tzinfo=row.fetched_at.tzinfo or UTC) >= stale_after
                ):
                    self.last_cache_hit = True
                    self.last_stale = True
                    forecast = payload_to_forecast(row.payload, stale=True)
                    logger.info("weather_cache stale_serve cell=%s", key)
                    return forecast
                raise
        finally:
            if token:
                self._release_lock(lock_key)

    def _store(self, key: str, forecast: NormalizedForecast) -> None:
        payload = forecast_to_payload(forecast)
        row = self.db.get(WeatherForecastCache, key)
        if row is None:
            row = WeatherForecastCache(
                cell_key=key,
                provider=forecast.provider,
                fetched_at=forecast.fetched_at,
                forecast_start=forecast.forecast_start,
                forecast_end=forecast.forecast_end,
                payload=payload,
            )
            self.db.add(row)
        else:
            row.provider = forecast.provider
            row.fetched_at = forecast.fetched_at
            row.forecast_start = forecast.forecast_start
            row.forecast_end = forecast.forecast_end
            row.payload = payload
        self.db.commit()

    def _acquire_lock(self, lock_key: str) -> bool:
        if self.redis is None:
            return False
        deadline = time.time() + LOCK_WAIT_SECONDS
        while time.time() < deadline:
            if self.redis.set(lock_key, "1", nx=True, ex=LOCK_TTL):
                return True
            time.sleep(0.15)
            # If the other holder finished, the caller re-checks cache.
            return False
        return False

    def _release_lock(self, lock_key: str) -> None:
        if self.redis is None:
            return
        try:
            self.redis.delete(lock_key)
        except Exception:
            logger.debug("redis lock release failed", exc_info=True)
