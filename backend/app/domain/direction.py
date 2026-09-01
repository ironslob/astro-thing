from __future__ import annotations

from app.domain.constants import MIN_USEFUL_ALTITUDE

_SECTORS = (
    (0, "North"),
    (45, "Northeast"),
    (90, "East"),
    (135, "Southeast"),
    (180, "South"),
    (225, "Southwest"),
    (270, "West"),
    (315, "Northwest"),
)


def compass_direction(azimuth_deg: float) -> str:
    az = azimuth_deg % 360
    idx = int((az + 22.5) // 45) % 8
    return _SECTORS[idx][1]


def altitude_phrase(altitude_deg: float) -> str:
    if altitude_deg < MIN_USEFUL_ALTITUDE:
        return "low on the horizon"
    if altitude_deg < 35:
        return "fairly low"
    if altitude_deg < 55:
        return "about halfway up the sky"
    if altitude_deg < 75:
        return "high in the sky"
    return "almost overhead"


def pointing_direction(azimuth_deg: float, altitude_deg: float) -> str:
    return f"{compass_direction(azimuth_deg)}, {altitude_phrase(altitude_deg)}"
