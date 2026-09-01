from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain.constants import (
    ASTRONOMICAL_TWILIGHT_ALT,
    DEFAULT_TIMEZONE,
    MAX_WINDOWS_PER_NIGHT,
    MIN_WINDOW_MINUTES,
    SLICE_MINUTES,
)
from app.domain.explanations import explain_poor_night, explain_window
from app.domain.models import HourlyWeather, NormalizedForecast, ObservingWindow, SliceScore
from app.domain.ratings import rating_label
from app.domain.scoring import score_conditions

SunAltitudeFn = Callable[[datetime], float]
FALLBACK_HOUR = HourlyWeather(
    time=datetime(2000, 1, 1),
    cloud_cover=50,
    visibility=10000,
    relative_humidity=70,
)


def night_date_for(local: datetime) -> datetime.date:
    """Evening-associated date: hours before noon belong to the previous night."""
    if local.hour < 12:
        return (local - timedelta(days=1)).date()
    return local.date()


def human_night_label(night_date, now_local: datetime) -> str:
    today_night = night_date_for(now_local)
    delta = (night_date - today_night).days
    if delta == 0:
        return "Tonight"
    if delta == 1:
        return "Tomorrow"
    return night_date.strftime("%A")


def _iter_slices(start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
    slices: list[tuple[datetime, datetime]] = []
    t = start
    step = timedelta(minutes=SLICE_MINUTES)
    while t < end:
        nxt = min(t + step, end)
        slices.append((t, nxt))
        t = nxt
    return slices


def _night_bounds(night_date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    """Local window covering dusk through dawn for a given evening date."""
    start = datetime(night_date.year, night_date.month, night_date.day, 16, 0, tzinfo=tz)
    end = start + timedelta(hours=16)
    return start, end


def generate_windows(
    *,
    now: datetime,
    forecast: NormalizedForecast,
    sun_altitude_at: SunAltitudeFn,
    timezone: str = DEFAULT_TIMEZONE,
) -> list[ObservingWindow]:
    tz = ZoneInfo(timezone)
    now_local = now.astimezone(tz) if now.tzinfo else now.replace(tzinfo=tz)
    first_night = night_date_for(now_local)
    windows: list[ObservingWindow] = []

    for offset in range(3):
        night = first_night + timedelta(days=offset)
        start, end = _night_bounds(night, tz)
        if end <= now_local:
            continue
        slice_start = max(start, now_local)
        dark_slices: list[SliceScore] = []
        any_dark = False
        for s, e in _iter_slices(slice_start, end):
            mid = s + (e - s) / 2
            sun = sun_altitude_at(mid)
            hour = forecast.nearest(mid) or FALLBACK_HOUR
            sc = score_conditions(hour, sun)
            if sun <= ASTRONOMICAL_TWILIGHT_ALT:
                any_dark = True
                dark_slices.append(
                    SliceScore(
                        start=s,
                        end=e,
                        score=sc,
                        rating=rating_label(sc),
                        weather=hour,
                        sun_altitude=sun,
                    )
                )

        label = human_night_label(night, now_local)
        night_key = night.isoformat()

        if not any_dark:
            # Represent the night so the UI can explain poor deep-sky conditions.
            dummy_hour = forecast.nearest(start + timedelta(hours=6)) or FALLBACK_HOUR
            sun_mid = sun_altitude_at(start + timedelta(hours=6))
            sc = min(40.0, score_conditions(dummy_hour, sun_mid))
            w = ObservingWindow(
                start=start + timedelta(hours=6),
                end=start + timedelta(hours=8),
                night_date=night_key,
                label=label,
                score=sc,
                rating="Poor",
                explanation=explain_poor_night("darkness"),
                slices=[],
            )
            windows.append(w)
            continue

        merged = _merge_slices(dark_slices)
        useful = [m for m in merged if m.duration_minutes >= MIN_WINDOW_MINUTES]
        if not useful:
            # Keep the longest fragment so the night is still explained.
            useful = sorted(merged, key=lambda w: w.duration_minutes, reverse=True)[:1]
            if useful:
                useful[0].rating = useful[0].rating if useful[0].duration_minutes >= 30 else "Poor"
                if useful[0].duration_minutes < MIN_WINDOW_MINUTES:
                    useful[0].explanation = "Only a short dark spell — too brief to be useful."

        useful.sort(key=lambda w: w.score, reverse=True)
        picked = useful[:MAX_WINDOWS_PER_NIGHT]
        picked.sort(key=lambda w: w.start)
        # Re-order for the night: quality first (spec: by night then quality)
        picked.sort(key=lambda w: w.score, reverse=True)
        for w in picked:
            w.night_date = night_key
            w.label = label
            if not w.explanation:
                w.explanation = explain_window(w)
            windows.append(w)

    return windows


def _merge_slices(slices: list[SliceScore]) -> list[ObservingWindow]:
    if not slices:
        return []
    groups: list[list[SliceScore]] = [[slices[0]]]
    for sl in slices[1:]:
        prev = groups[-1][-1]
        contiguous = sl.start <= prev.end + timedelta(minutes=1)
        same = sl.rating == prev.rating
        if contiguous and same:
            groups[-1].append(sl)
        elif contiguous and not same:
            # Break on rating change so quality-bounded windows stay honest
            groups.append([sl])
        else:
            groups.append([sl])

    windows: list[ObservingWindow] = []
    for group in groups:
        score = sum(s.score for s in group) / len(group)
        w = ObservingWindow(
            start=group[0].start,
            end=group[-1].end,
            night_date="",
            label="",
            score=score,
            rating=rating_label(score),
            explanation="",
            slices=group,
        )
        windows.append(w)
    return windows
