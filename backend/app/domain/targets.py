from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.constants import (
    MIN_USEFUL_ALTITUDE,
    PREFERRED_ALTITUDE,
    T_GEOMETRY,
    T_MOON,
    T_PLACED,
    T_PRIOR,
)
from app.domain.direction import pointing_direction
from app.domain.ratings import rating_label


@dataclass
class PositionSample:
    time: datetime
    altitude: float
    azimuth: float


@dataclass
class TargetCandidate:
    key: str
    name: str
    object_type: str
    friendly_type: str
    catalogue_ids: list[str]
    ra: float | None
    dec: float | None
    magnitude: float | None
    beginner_prior: float
    samples: list[PositionSample]
    kind: str  # dso | planet | moon
    moon_separation_deg: float | None = None
    rise: datetime | None = None
    set: datetime | None = None
    transit: datetime | None = None
    images: list[dict] = field(default_factory=list)


@dataclass
class RankedTarget:
    id: str
    name: str
    object_type: str
    friendly_type: str
    rating: str
    score: float
    direction: str
    best_portion: str | None
    reason: str
    featured: bool
    details: dict
    kind: str
    catalogue_ids: list[str] = field(default_factory=list)
    images: list[dict] = field(default_factory=list)


def _peak(samples: list[PositionSample]) -> PositionSample:
    return max(samples, key=lambda s: s.altitude)


def geometry_score(samples: list[PositionSample]) -> float:
    peak = _peak(samples)
    # 20° → 0, 90° → 100
    alt_part = max(0.0, min(100.0, (peak.altitude - MIN_USEFUL_ALTITUDE) * (100.0 / 70.0)))
    above_pref = sum(1 for s in samples if s.altitude >= PREFERRED_ALTITUDE)
    frac = above_pref / max(1, len(samples))
    return 0.7 * alt_part + 0.3 * (frac * 100.0)


def placed_score(
    samples: list[PositionSample], window_start: datetime, window_end: datetime
) -> float:
    peak = _peak(samples)
    in_window = window_start <= peak.time <= window_end
    above = sum(1 for s in samples if s.altitude >= PREFERRED_ALTITUDE)
    frac = above / max(1, len(samples))
    bonus = 20.0 if in_window else 0.0
    return min(100.0, frac * 80.0 + bonus)


def moon_score(separation_deg: float | None, illumination: float, kind: str) -> float:
    if kind in {"moon"}:
        return 100.0
    if separation_deg is None:
        return 80.0
    # Full penalty at 0° with full moon; none beyond ~90°
    proximity = max(0.0, 1.0 - (separation_deg / 90.0))
    penalty = 100.0 * illumination * proximity
    if kind == "planet":
        penalty *= 0.5
    return max(0.0, 100.0 - penalty)


def prior_score(beginner_prior: float, magnitude: float | None) -> float:
    mag_part = 50.0
    if magnitude is not None:
        # mag 1 → 100, mag 10 → 0
        mag_part = max(0.0, min(100.0, (10.0 - magnitude) * 11.0))
    return 0.7 * beginner_prior + 0.3 * mag_part


def score_target(
    candidate: TargetCandidate,
    *,
    window_start: datetime,
    window_end: datetime,
    moon_illumination: float,
) -> float | None:
    useful = [s for s in candidate.samples if s.altitude >= MIN_USEFUL_ALTITUDE]
    if not useful:
        return None
    peak = _peak(candidate.samples)
    if peak.altitude < MIN_USEFUL_ALTITUDE:
        return None
    geo = geometry_score(candidate.samples)
    placed = placed_score(candidate.samples, window_start, window_end)
    moon = moon_score(candidate.moon_separation_deg, moon_illumination, candidate.kind)
    prior = prior_score(candidate.beginner_prior, candidate.magnitude)
    return T_GEOMETRY * geo + T_PLACED * placed + T_MOON * moon + T_PRIOR * prior


def _best_portion(samples: list[PositionSample]) -> str | None:
    peak = _peak(samples)
    local = peak.time
    hour = local.hour
    minute = local.minute
    suffix = "am" if hour < 12 else "pm"
    h12 = hour % 12 or 12
    t = f"{h12}{suffix}" if minute == 0 else f"{h12}:{minute:02d}{suffix}"
    if peak.altitude >= PREFERRED_ALTITUDE:
        return f"Best around {t}"
    return None


def _reason(candidate: TargetCandidate, rating: str, moon_illumination: float) -> str:
    peak = _peak(candidate.samples)
    name = candidate.name
    if candidate.kind == "moon":
        pct = int(round(moon_illumination * 100))
        return f"The Moon is up and about {pct}% lit — an easy target if you want it."
    if candidate.kind == "planet":
        if peak.altitude >= 40:
            return f"{name} is well placed and obvious in this window."
        return f"{name} is visible, though not particularly high."
    if rating in {"Excellent", "Good"}:
        if peak.altitude >= 50:
            return "A strong target for most of this window."
        return "Well placed and a satisfying beginner target."
    if rating == "Fair":
        if candidate.moon_separation_deg is not None and candidate.moon_separation_deg < 40:
            return "Visible, but the Moon washes it out a little."
        return "Worth a look, though it never gets especially high."
    return "A stretch tonight — there are stronger options above."


def rank_targets(
    candidates: list[TargetCandidate],
    *,
    window_start: datetime,
    window_end: datetime,
    moon_illumination: float,
    weather_details: dict | None = None,
) -> list[RankedTarget]:
    scored: list[tuple[float, TargetCandidate]] = []
    for cand in candidates:
        sc = score_target(
            cand,
            window_start=window_start,
            window_end=window_end,
            moon_illumination=moon_illumination,
        )
        if sc is None:
            continue
        scored.append((sc, cand))
    scored.sort(key=lambda item: item[0], reverse=True)

    ranked: list[RankedTarget] = []
    for i, (sc, cand) in enumerate(scored):
        peak = _peak(cand.samples)
        rating = rating_label(sc)
        details = {
            "altitude_deg": round(peak.altitude, 1),
            "azimuth_deg": round(peak.azimuth, 1),
            "ra": cand.ra,
            "dec": cand.dec,
            "catalogue_ids": cand.catalogue_ids,
            "moon_separation_deg": (
                None if cand.moon_separation_deg is None else round(cand.moon_separation_deg, 1)
            ),
            "moon_illumination": round(moon_illumination, 3),
            "rise": cand.rise.isoformat() if cand.rise else None,
            "set": cand.set.isoformat() if cand.set else None,
            "transit": cand.transit.isoformat() if cand.transit else None,
            "kind": cand.kind,
        }
        if weather_details:
            details["weather"] = weather_details
        ranked.append(
            RankedTarget(
                id=cand.key,
                name=cand.name,
                object_type=cand.object_type,
                friendly_type=cand.friendly_type,
                rating=rating,
                score=sc,
                direction=pointing_direction(peak.azimuth, peak.altitude),
                best_portion=_best_portion(cand.samples),
                reason=_reason(cand, rating, moon_illumination),
                featured=i < 3,
                details=details,
                kind=cand.kind,
                catalogue_ids=cand.catalogue_ids,
                images=list(cand.images or []),
            )
        )
    return ranked


def unplaced_target(
    candidate: TargetCandidate,
    *,
    moon_illumination: float,
    weather_details: dict | None = None,
    reason: str,
) -> RankedTarget:
    """A Poor card for a looked-up object that is not usefully placed."""
    if candidate.samples:
        peak = _peak(candidate.samples)
        direction = (
            "Below the horizon"
            if peak.altitude < 0
            else pointing_direction(peak.azimuth, peak.altitude)
        )
        details = {
            "altitude_deg": round(peak.altitude, 1),
            "azimuth_deg": round(peak.azimuth, 1),
            "ra": candidate.ra,
            "dec": candidate.dec,
            "catalogue_ids": candidate.catalogue_ids,
            "moon_separation_deg": (
                None
                if candidate.moon_separation_deg is None
                else round(candidate.moon_separation_deg, 1)
            ),
            "moon_illumination": round(moon_illumination, 3),
            "rise": candidate.rise.isoformat() if candidate.rise else None,
            "set": candidate.set.isoformat() if candidate.set else None,
            "transit": candidate.transit.isoformat() if candidate.transit else None,
            "kind": candidate.kind,
        }
    else:
        direction = "Not visible from here"
        details = {
            "altitude_deg": None,
            "azimuth_deg": None,
            "ra": candidate.ra,
            "dec": candidate.dec,
            "catalogue_ids": candidate.catalogue_ids,
            "moon_separation_deg": candidate.moon_separation_deg,
            "moon_illumination": round(moon_illumination, 3),
            "rise": None,
            "set": None,
            "transit": None,
            "kind": candidate.kind,
        }
    if weather_details:
        details["weather"] = weather_details
    return RankedTarget(
        id=candidate.key,
        name=candidate.name,
        object_type=candidate.object_type,
        friendly_type=candidate.friendly_type,
        rating="Poor",
        score=0.0,
        direction=direction,
        best_portion=None,
        reason=reason,
        featured=True,
        details=details,
        kind=candidate.kind,
        catalogue_ids=candidate.catalogue_ids,
        images=list(candidate.images or []),
    )
