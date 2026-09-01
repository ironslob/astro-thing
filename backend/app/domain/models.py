from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.ratings import rating_label


@dataclass(frozen=True)
class HourlyWeather:
    time: datetime
    cloud_cover: float
    cloud_low: float | None = None
    cloud_mid: float | None = None
    cloud_high: float | None = None
    visibility: float | None = None
    relative_humidity: float | None = None
    precipitation: float = 0.0
    precipitation_probability: float = 0.0
    wind_speed: float = 0.0
    wind_gusts: float | None = None


@dataclass
class NormalizedForecast:
    hours: list[HourlyWeather]
    provider: str
    fetched_at: datetime
    forecast_start: datetime
    forecast_end: datetime
    source_label: str = "Open-Meteo"
    stale: bool = False

    def nearest(self, when: datetime) -> HourlyWeather | None:
        if not self.hours:
            return None
        target = when.astimezone(self.hours[0].time.tzinfo) if when.tzinfo else when
        return min(self.hours, key=lambda h: abs((h.time - target).total_seconds()))


@dataclass
class SliceScore:
    start: datetime
    end: datetime
    score: float
    rating: str
    weather: HourlyWeather
    sun_altitude: float

    def __post_init__(self) -> None:
        if not self.rating:
            self.rating = rating_label(self.score)


@dataclass
class ObservingWindow:
    start: datetime
    end: datetime
    night_date: str
    label: str
    score: float
    rating: str
    explanation: str
    slices: list[SliceScore] = field(default_factory=list)

    @property
    def duration_minutes(self) -> float:
        return (self.end - self.start).total_seconds() / 60.0
