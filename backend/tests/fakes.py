from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.models import HourlyWeather, NormalizedForecast


def hour(
    when: datetime,
    *,
    cloud: float = 10,
    low: float | None = 5,
    mid: float | None = 5,
    high: float | None = 10,
    vis: float = 20000,
    rh: float = 55,
    precip: float = 0,
    pop: float = 0,
    wind: float = 8,
    gusts: float | None = 12,
) -> HourlyWeather:
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return HourlyWeather(
        time=when,
        cloud_cover=cloud,
        cloud_low=low,
        cloud_mid=mid,
        cloud_high=high,
        visibility=vis,
        relative_humidity=rh,
        precipitation=precip,
        precipitation_probability=pop,
        wind_speed=wind,
        wind_gusts=gusts,
    )


def forecast_from_builder(
    start: datetime,
    hours: int,
    builder,
) -> NormalizedForecast:
    rows = []
    t = start.astimezone(UTC) if start.tzinfo else start.replace(tzinfo=UTC)
    for i in range(hours):
        when = t + timedelta(hours=i)
        rows.append(builder(when, i))
    return NormalizedForecast(
        hours=rows,
        provider="fake",
        fetched_at=t,
        forecast_start=rows[0].time,
        forecast_end=rows[-1].time,
        source_label="fixture",
        stale=False,
    )


class FakeWeatherProvider:
    name = "fake"

    def __init__(self, forecast: NormalizedForecast | None = None, fail: bool = False) -> None:
        self.forecast = forecast
        self.fail = fail
        self.calls = 0

    def fetch(self, latitude: float, longitude: float) -> NormalizedForecast:
        self.calls += 1
        if self.fail:
            from app.weather.provider import WeatherProviderError

            raise WeatherProviderError("synthetic failure")
        assert self.forecast is not None
        return self.forecast
