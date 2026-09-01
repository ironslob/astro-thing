from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.domain.windows import generate_windows, night_date_for
from tests.fakes import forecast_from_builder, hour

TZ = ZoneInfo("Europe/London")
# A winter evening in the UK so astronomical darkness exists.
NOW = datetime(2026, 1, 15, 16, 0, tzinfo=TZ)


def sun_factory(dark_from_hour: int = 18, dark_to_hour: int = 7):
    def sun_at(when: datetime) -> float:
        local = when.astimezone(TZ)
        h = local.hour + local.minute / 60.0
        if h >= dark_from_hour or h < dark_to_hour:
            return -30.0
        if h >= dark_from_hour - 1 or h < dark_to_hour + 1:
            return -10.0
        return 20.0

    return sun_at


def test_clear_dark_night_is_good_or_excellent() -> None:
    start = datetime(2026, 1, 15, 0, tzinfo=UTC)

    def builder(when, _i):
        return hour(when, cloud=8, low=2, mid=3, high=10)

    forecast = forecast_from_builder(start, 96, builder)
    windows = generate_windows(now=NOW, forecast=forecast, sun_altitude_at=sun_factory())
    tonight = [w for w in windows if w.label == "Tonight"]
    assert tonight, windows
    assert tonight[0].rating in {"Good", "Excellent"}
    assert tonight[0].duration_minutes >= 60


def test_heavy_cloud_is_poor() -> None:
    start = datetime(2026, 1, 15, 0, tzinfo=UTC)

    def builder(when, _i):
        return hour(when, cloud=98, low=95, mid=90, high=80)

    forecast = forecast_from_builder(start, 96, builder)
    windows = generate_windows(now=NOW, forecast=forecast, sun_altitude_at=sun_factory())
    tonight = [w for w in windows if w.label == "Tonight"]
    assert tonight
    assert tonight[0].rating == "Poor"


def test_rain_is_strong_penalty() -> None:
    start = datetime(2026, 1, 15, 0, tzinfo=UTC)

    def builder(when, _i):
        return hour(when, cloud=20, low=10, mid=10, high=10, precip=2.5, pop=90)

    forecast = forecast_from_builder(start, 96, builder)
    windows = generate_windows(now=NOW, forecast=forecast, sun_altitude_at=sun_factory())
    tonight = [w for w in windows if w.label == "Tonight"]
    assert tonight
    assert tonight[0].score < 45
    assert tonight[0].rating == "Poor"


def test_clear_spell_is_bounded_by_cloud() -> None:
    start = datetime(2026, 1, 15, 0, tzinfo=UTC)

    def builder(when, _i):
        local = when.astimezone(TZ)
        # Clear only 21:00-23:00 local
        if 21 <= local.hour < 23:
            return hour(when, cloud=5, low=0, mid=0, high=5)
        return hour(when, cloud=90, low=85, mid=70, high=40)

    forecast = forecast_from_builder(start, 96, builder)
    windows = generate_windows(now=NOW, forecast=forecast, sun_altitude_at=sun_factory())
    tonight = [w for w in windows if w.label == "Tonight"]
    goodish = [w for w in tonight if w.rating in {"Good", "Excellent", "Fair"}]
    assert goodish, [(w.rating, w.start, w.end, w.score) for w in tonight]
    w = goodish[0]
    local_start = w.start.astimezone(TZ)
    local_end = w.end.astimezone(TZ)
    assert local_start.hour >= 20
    assert local_end.hour <= 23 or (local_end.hour == 0)


def test_no_astronomical_darkness_is_poor_not_fabricated() -> None:
    start = datetime(2026, 6, 20, 0, tzinfo=UTC)
    now = datetime(2026, 6, 20, 16, 0, tzinfo=TZ)

    def always_twilight(when: datetime) -> float:
        return -12.0  # nautical, never astronomical

    def builder(when, _i):
        return hour(when, cloud=5, low=0, mid=0, high=5)

    forecast = forecast_from_builder(start, 96, builder)
    windows = generate_windows(now=now, forecast=forecast, sun_altitude_at=always_twilight)
    assert windows
    assert all(w.rating == "Poor" for w in windows)
    assert all(
        "dark" in w.explanation.lower() or "doesn't get dark" in w.explanation.lower()
        for w in windows
    )


def test_adjacent_similar_slices_merge() -> None:
    start = datetime(2026, 1, 15, 0, tzinfo=UTC)

    def builder(when, _i):
        return hour(when, cloud=10, low=5, mid=5, high=5)

    forecast = forecast_from_builder(start, 96, builder)
    windows = generate_windows(now=NOW, forecast=forecast, sun_altitude_at=sun_factory())
    tonight = [w for w in windows if w.label == "Tonight"]
    assert len(tonight) <= 2
    assert tonight[0].duration_minutes >= 120


def test_tiny_fragments_discarded() -> None:
    start = datetime(2026, 1, 15, 0, tzinfo=UTC)

    def builder(when, _i):
        local = when.astimezone(TZ)
        # A 30-minute clear hole at 22:00, otherwise socked in
        if local.hour == 22 and local.minute == 0:
            return hour(when, cloud=5, low=0, mid=0, high=0)
        return hour(when, cloud=92, low=90, mid=80, high=40)

    forecast = forecast_from_builder(start, 96, builder)
    windows = generate_windows(now=NOW, forecast=forecast, sun_altitude_at=sun_factory())
    tonight = [w for w in windows if w.label == "Tonight"]
    for w in tonight:
        if w.rating in {"Good", "Excellent"}:
            assert w.duration_minutes >= 60


def test_night_date_before_noon_belongs_to_previous_evening() -> None:
    two_am = datetime(2026, 1, 16, 2, 0, tzinfo=TZ)
    assert night_date_for(two_am).isoformat() == "2026-01-15"
