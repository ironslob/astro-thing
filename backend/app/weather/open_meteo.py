from __future__ import annotations

from datetime import UTC, datetime

import httpx

from app.core.config import settings
from app.domain.models import HourlyWeather, NormalizedForecast
from app.weather.provider import WeatherProviderError

HOURLY_FIELDS = (
    "cloud_cover",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "visibility",
    "relative_humidity_2m",
    "precipitation_probability",
    "precipitation",
    "wind_speed_10m",
    "wind_gusts_10m",
)


def _f(values: list, i: int) -> float | None:
    if i >= len(values):
        return None
    v = values[i]
    if v is None:
        return None
    return float(v)


class OpenMeteoWeatherProvider:
    name = "open-meteo"

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (base_url or settings.open_meteo_base_url).rstrip("/")
        self.timeout = timeout or settings.weather_request_timeout_seconds
        self._client = client

    def fetch(self, latitude: float, longitude: float) -> NormalizedForecast:
        params = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "hourly": ",".join(HOURLY_FIELDS),
            "forecast_days": 4,
            "timezone": "UTC",
            "wind_speed_unit": "kmh",
        }
        url = f"{self.base_url}/v1/forecast"
        try:
            if self._client is not None:
                resp = self._client.get(url, params=params, timeout=self.timeout)
            else:
                resp = httpx.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise WeatherProviderError(f"Open-Meteo request failed: {exc}") from exc
        return self._normalize(data)

    def _normalize(self, data: dict) -> NormalizedForecast:
        hourly = data.get("hourly") or {}
        times = hourly.get("time") or []
        hours: list[HourlyWeather] = []
        for i, stamp in enumerate(times):
            when = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if when.tzinfo is None:
                when = when.replace(tzinfo=UTC)
            hours.append(
                HourlyWeather(
                    time=when,
                    cloud_cover=_f(hourly.get("cloud_cover") or [], i) or 0.0,
                    cloud_low=_f(hourly.get("cloud_cover_low") or [], i),
                    cloud_mid=_f(hourly.get("cloud_cover_mid") or [], i),
                    cloud_high=_f(hourly.get("cloud_cover_high") or [], i),
                    visibility=_f(hourly.get("visibility") or [], i),
                    relative_humidity=_f(hourly.get("relative_humidity_2m") or [], i),
                    precipitation=_f(hourly.get("precipitation") or [], i) or 0.0,
                    precipitation_probability=_f(hourly.get("precipitation_probability") or [], i)
                    or 0.0,
                    wind_speed=_f(hourly.get("wind_speed_10m") or [], i) or 0.0,
                    wind_gusts=_f(hourly.get("wind_gusts_10m") or [], i),
                )
            )
        if not hours:
            raise WeatherProviderError("Open-Meteo returned no hourly data")
        fetched = datetime.now(UTC)
        return NormalizedForecast(
            hours=hours,
            provider=self.name,
            fetched_at=fetched,
            forecast_start=hours[0].time,
            forecast_end=hours[-1].time,
            source_label="Open-Meteo",
            stale=False,
        )
