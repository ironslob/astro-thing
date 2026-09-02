from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.astronomy.service import AstronomyService
from app.core.config import settings
from app.domain.constants import (
    BEGINNER_RANK_MIN_PRIOR,
    DEFAULT_TIMEZONE,
    MAJOR_PLANETS,
    MIN_USEFUL_ALTITUDE,
    SCORING_VERSION,
)
from app.domain.models import NormalizedForecast, ObservingWindow
from app.domain.targets import RankedTarget, TargetCandidate, rank_targets, unplaced_target
from app.domain.windows import generate_windows
from app.models.catalogue import DeepSkyObject
from app.services.images import images_for, normalize_images
from app.weather.cache import WeatherCacheService


class ForecastUnavailable(Exception):
    """No live weather and no usable stale cache."""


class UnknownTarget(Exception):
    """The requested catalogue object does not exist."""


class ForecastService:
    def __init__(
        self,
        db: Session,
        cache: WeatherCacheService,
        astronomy: AstronomyService | None = None,
    ) -> None:
        self.db = db
        self.cache = cache
        self.astronomy = astronomy or AstronomyService()

    def windows(self, lat: float, lon: float, now: datetime | None = None) -> dict:
        now = now or datetime.now(UTC)
        forecast = self.cache.get(lat, lon)
        tz = DEFAULT_TIMEZONE

        def sun_at(when: datetime) -> float:
            return self.astronomy.sun_altitude(lat, lon, when)

        windows = generate_windows(now=now, forecast=forecast, sun_altitude_at=sun_at, timezone=tz)
        return {
            "location": {
                "latitude": lat,
                "longitude": lon,
                "timezone": tz,
            },
            "forecast": {
                "fetched_at": forecast.fetched_at.isoformat(),
                "forecast_start": forecast.forecast_start.isoformat(),
                "forecast_end": forecast.forecast_end.isoformat(),
                "stale": forecast.stale,
                "source": forecast.source_label,
                "provider": forecast.provider,
            },
            "scoring_version": settings.scoring_version or SCORING_VERSION,
            "windows": [self._window_payload(w, tz) for w in windows],
            "cache_hit": self.cache.last_cache_hit,
        }

    def targets(
        self,
        lat: float,
        lon: float,
        start: datetime,
        end: datetime,
        now: datetime | None = None,
        object_id: str | None = None,
    ) -> dict:
        now = now or datetime.now(UTC)
        forecast = self.cache.get(lat, lon)

        def sun_at(when: datetime) -> float:
            return self.astronomy.sun_altitude(lat, lon, when)

        all_windows = generate_windows(now=now, forecast=forecast, sun_altitude_at=sun_at)
        matched = _matching_window(all_windows, start, end)
        weather_details = _window_weather(matched, forecast)

        objects: Sequence[DeepSkyObject] = (
            self.db.query(DeepSkyObject)
            .filter(DeepSkyObject.beginner_prior >= BEGINNER_RANK_MIN_PRIOR)
            .all()
        )
        mid = start + (end - start) / 2
        moon = self.astronomy.moon_state(lat, lon, mid)
        candidates: list[TargetCandidate] = []

        for obj in objects:
            cand = self._dso_candidate(lat, lon, obj, start, end, mid)
            if cand is not None:
                candidates.append(cand)

        candidates.extend(self.astronomy.planet_candidates(lat, lon, start, end))
        moon_cand = self.astronomy.moon_candidate(lat, lon, start, end)
        if moon_cand:
            candidates.append(moon_cand)
        for cand in candidates:
            self._ensure_images(cand)

        ranked = rank_targets(
            candidates,
            window_start=start,
            window_end=end,
            moon_illumination=moon.illumination,
            weather_details=weather_details,
        )[:12]

        if object_id:
            pinned = self._pin_object(
                object_id,
                lat,
                lon,
                start,
                end,
                mid,
                moon.illumination,
                weather_details,
            )
            ranked = [pinned] + [t for t in ranked if t.id != pinned.id]

        return {
            "window": (
                None
                if matched is None
                else {
                    "start": matched.start.isoformat(),
                    "end": matched.end.isoformat(),
                    "rating": matched.rating,
                    "explanation": matched.explanation,
                    "label": matched.label,
                }
            ),
            "forecast": {
                "fetched_at": forecast.fetched_at.isoformat(),
                "stale": forecast.stale,
                "source": forecast.source_label,
            },
            "scoring_version": settings.scoring_version or SCORING_VERSION,
            "targets": [_target_payload(t) for t in ranked],
            "empty_reason": (
                None
                if ranked
                else "Nothing worthwhile is high enough in this window. Try another night."
            ),
        }

    def _dso_candidate(
        self,
        lat: float,
        lon: float,
        obj: DeepSkyObject,
        start: datetime,
        end: datetime,
        mid: datetime,
        *,
        require_useful: bool = True,
    ) -> TargetCandidate | None:
        if require_useful and 90.0 - abs(lat - obj.dec) < MIN_USEFUL_ALTITUDE:
            return None
        samples = self.astronomy.sample_dso(lat, lon, obj.ra, obj.dec, start, end)
        if not samples:
            return None
        if require_useful and max(s.altitude for s in samples) < MIN_USEFUL_ALTITUDE:
            return None
        sep = self.astronomy.moon_separation(lat, lon, mid, obj.ra, obj.dec)
        day = self.astronomy.sample_dso(
            lat, lon, obj.ra, obj.dec, start - timedelta(hours=8), end + timedelta(hours=8)
        )
        rise, set_, transit = self.astronomy.rise_set_transit(day)
        return TargetCandidate(
            key=obj.id,
            name=obj.common_name or obj.primary_name,
            object_type=obj.object_type,
            friendly_type=obj.friendly_type,
            catalogue_ids=list(obj.catalogue_ids or []),
            ra=obj.ra,
            dec=obj.dec,
            magnitude=obj.magnitude,
            beginner_prior=float(obj.beginner_prior),
            samples=samples,
            kind="dso",
            moon_separation_deg=sep,
            rise=rise,
            set=set_,
            transit=transit,
            images=normalize_images(obj.images),
        )

    def _pin_object(
        self,
        object_id: str,
        lat: float,
        lon: float,
        start: datetime,
        end: datetime,
        mid: datetime,
        moon_illumination: float,
        weather_details: dict,
    ) -> RankedTarget:
        cand = self._lookup_candidate(object_id, lat, lon, start, end, mid)
        if cand is None:
            raise UnknownTarget(object_id)
        self._ensure_images(cand)
        ranked = rank_targets(
            [cand],
            window_start=start,
            window_end=end,
            moon_illumination=moon_illumination,
            weather_details=weather_details,
        )
        if ranked:
            top = ranked[0]
            top.featured = True
            return top
        reason = (
            "This never gets high enough from the UK."
            if cand.dec is not None and 90.0 - abs(lat - cand.dec) < MIN_USEFUL_ALTITUDE
            else "Not high enough in this window. Try another night."
        )
        return unplaced_target(
            cand,
            moon_illumination=moon_illumination,
            weather_details=weather_details,
            reason=reason,
        )

    def _lookup_candidate(
        self,
        object_id: str,
        lat: float,
        lon: float,
        start: datetime,
        end: datetime,
        mid: datetime,
    ) -> TargetCandidate | None:
        key = object_id.strip().lower()
        if key in MAJOR_PLANETS or key == "moon":
            return self.astronomy.body_candidate(
                lat, lon, key, start, end, require_above_horizon=False
            )
        obj = self.db.get(DeepSkyObject, key)
        if obj is None:
            obj = self.db.get(DeepSkyObject, object_id.strip())
        if obj is None:
            return None
        return self._dso_candidate(lat, lon, obj, start, end, mid, require_useful=False)

    @staticmethod
    def _ensure_images(cand: TargetCandidate) -> None:
        if not cand.images:
            cand.images = images_for(object_id=cand.key, catalogue_ids=cand.catalogue_ids)

    def _window_payload(self, window: ObservingWindow, tz_name: str) -> dict:
        tz = ZoneInfo(tz_name)
        start = window.start.astimezone(tz)
        end = window.end.astimezone(tz)
        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "night_date": window.night_date,
            "label": window.label,
            "rating": window.rating,
            "explanation": window.explanation,
            "duration_minutes": int(window.duration_minutes),
        }


def _matching_window(
    windows: list[ObservingWindow], start: datetime, end: datetime
) -> ObservingWindow | None:
    def _aware(dt: datetime) -> datetime:
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)

    s, e = _aware(start), _aware(end)
    best = None
    best_overlap = timedelta(0)
    for w in windows:
        ws, we = _aware(w.start), _aware(w.end)
        overlap = min(we, e) - max(ws, s)
        if overlap > best_overlap:
            best_overlap = overlap
            best = w
    if best is not None:
        return best
    # Exact-ish match on start
    for w in windows:
        if abs((_aware(w.start) - s).total_seconds()) < 1800:
            return w
    return windows[0] if windows else None


def _avg(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 1) if xs else None


def _window_weather(window: ObservingWindow | None, forecast: NormalizedForecast) -> dict:
    if window and window.slices:
        hours = [s.weather for s in window.slices]
        return {
            "cloud_cover": _avg([h.cloud_cover for h in hours]),
            "cloud_low": _avg([h.cloud_low for h in hours if h.cloud_low is not None]),
            "cloud_mid": _avg([h.cloud_mid for h in hours if h.cloud_mid is not None]),
            "cloud_high": _avg([h.cloud_high for h in hours if h.cloud_high is not None]),
            "visibility": _avg([h.visibility for h in hours if h.visibility is not None]),
            "wind_speed": _avg([h.wind_speed for h in hours]),
            "precipitation": _avg([h.precipitation for h in hours]),
            "source": forecast.source_label,
            "fetched_at": forecast.fetched_at.isoformat(),
            "stale": forecast.stale,
        }
    hour = forecast.nearest(datetime.now(UTC))
    if not hour:
        return {"source": forecast.source_label, "stale": forecast.stale}
    return {
        "cloud_cover": hour.cloud_cover,
        "cloud_low": hour.cloud_low,
        "cloud_mid": hour.cloud_mid,
        "cloud_high": hour.cloud_high,
        "visibility": hour.visibility,
        "wind_speed": hour.wind_speed,
        "precipitation": hour.precipitation,
        "source": forecast.source_label,
        "fetched_at": forecast.fetched_at.isoformat(),
        "stale": forecast.stale,
    }


def _target_payload(t: RankedTarget) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "object_type": t.friendly_type,
        "rating": t.rating,
        "direction": t.direction,
        "best_portion": t.best_portion,
        "reason": t.reason,
        "featured": t.featured,
        "kind": t.kind,
        "details": t.details,
        "images": list(t.images or []),
    }
