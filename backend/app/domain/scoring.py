from __future__ import annotations

from app.domain.constants import (
    ASTRONOMICAL_TWILIGHT_ALT,
    CIVIL_TWILIGHT_ALT,
    NAUTICAL_TWILIGHT_ALT,
    W_CLOUD,
    W_DARKNESS,
    W_PRECIP,
    W_VIS_HUMIDITY,
    W_WIND,
)
from app.domain.models import HourlyWeather


def _cloud_cover(hour: HourlyWeather) -> float:
    if hour.cloud_low is not None and hour.cloud_mid is not None and hour.cloud_high is not None:
        return 0.50 * hour.cloud_low + 0.35 * hour.cloud_mid + 0.15 * hour.cloud_high
    return hour.cloud_cover


def cloud_score(hour: HourlyWeather) -> float:
    return max(0.0, min(100.0, 100.0 - _cloud_cover(hour)))


def precip_score(hour: HourlyWeather) -> float:
    chance = hour.precipitation_probability or 0.0
    mm = hour.precipitation or 0.0
    score = 100.0 - chance
    if mm > 1.0:
        score = min(score, 5.0)
    elif mm > 0.1:
        score = min(score, 20.0)
    return max(0.0, score)


def vis_humidity_score(hour: HourlyWeather) -> float:
    vis = 10000.0 if hour.visibility is None else hour.visibility
    vis_s = max(0.0, min(100.0, vis / 100.0))
    rh = 70.0 if hour.relative_humidity is None else hour.relative_humidity
    rh_s = max(0.0, 100.0 - max(0.0, rh - 50.0) * 2.0)
    return 0.6 * vis_s + 0.4 * rh_s


def wind_score(hour: HourlyWeather) -> float:
    spd = hour.wind_speed or 0.0
    gust = hour.wind_gusts if hour.wind_gusts is not None else spd
    speed_s = max(0.0, 100.0 - min(100.0, spd * 2.0))
    gust_s = max(0.0, 100.0 - min(100.0, gust * 1.5))
    return min(speed_s, gust_s)


def darkness_score(sun_altitude: float) -> float:
    if sun_altitude <= ASTRONOMICAL_TWILIGHT_ALT:
        return 100.0
    if sun_altitude <= NAUTICAL_TWILIGHT_ALT:
        return 40.0
    if sun_altitude <= CIVIL_TWILIGHT_ALT:
        return 10.0
    return 0.0


def score_conditions(hour: HourlyWeather, sun_altitude: float) -> float:
    raw = (
        W_CLOUD * cloud_score(hour)
        + W_PRECIP * precip_score(hour)
        + W_VIS_HUMIDITY * vis_humidity_score(hour)
        + W_WIND * wind_score(hour)
        + W_DARKNESS * darkness_score(sun_altitude)
    )
    cover = _cloud_cover(hour)
    mm = hour.precipitation or 0.0
    if mm > 0.2:
        raw *= 0.35
    if cover >= 85 or hour.cloud_cover >= 90:
        raw *= 0.40
    if sun_altitude > NAUTICAL_TWILIGHT_ALT:
        raw = min(raw, 40.0)
    if sun_altitude > CIVIL_TWILIGHT_ALT:
        raw = min(raw, 20.0)
    return max(0.0, min(100.0, raw))
