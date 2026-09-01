from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.direction import altitude_phrase, compass_direction, pointing_direction
from app.domain.targets import PositionSample, TargetCandidate, rank_targets, score_target


def _samples(
    altitudes: list[float], az: float = 45.0, start: datetime | None = None
) -> list[PositionSample]:
    start = start or datetime(2026, 1, 15, 21, 0, tzinfo=UTC)
    return [
        PositionSample(time=start + timedelta(minutes=30 * i), altitude=a, azimuth=az)
        for i, a in enumerate(altitudes)
    ]


def _cand(
    key: str,
    samples: list[PositionSample],
    *,
    prior: float = 80,
    sep: float | None = 80,
    kind: str = "dso",
    mag: float = 4.0,
    name: str | None = None,
) -> TargetCandidate:
    return TargetCandidate(
        key=key,
        name=name or key,
        object_type="galaxy",
        friendly_type="Galaxy",
        catalogue_ids=[key],
        ra=10.0,
        dec=41.0,
        magnitude=mag,
        beginner_prior=prior,
        samples=samples,
        kind=kind,
        moon_separation_deg=sep,
    )


START = datetime(2026, 1, 15, 21, 0, tzinfo=UTC)
END = datetime(2026, 1, 16, 1, 0, tzinfo=UTC)


def test_below_horizon_excluded() -> None:
    low = _cand("low", _samples([-5, -2, 5, 10]))
    ranked = rank_targets([low], window_start=START, window_end=END, moon_illumination=0.2)
    assert ranked == []


def test_high_target_ranks_above_low() -> None:
    high = _cand("high", _samples([50, 60, 65, 55]), prior=50)
    low = _cand("lowish", _samples([22, 24, 25, 23]), prior=50)
    ranked = rank_targets([low, high], window_start=START, window_end=END, moon_illumination=0.1)
    assert ranked[0].name == "high"
    assert ranked[0].score > ranked[1].score


def test_bright_moon_penalizes_nearby_dso() -> None:
    near = _cand("near", _samples([50, 55, 60, 55]), sep=8, prior=80)
    far = _cand("far", _samples([50, 55, 60, 55]), sep=90, prior=80)
    ranked = rank_targets([near, far], window_start=START, window_end=END, moon_illumination=0.95)
    assert ranked[0].name == "far"
    assert ranked[1].score < ranked[0].score


def test_moon_penalty_reduces_with_separation_and_low_illumination() -> None:
    near = _cand("near", _samples([50, 55, 50, 48]), sep=10, prior=80)
    bright = score_target(near, window_start=START, window_end=END, moon_illumination=0.95)
    dim = score_target(near, window_start=START, window_end=END, moon_illumination=0.1)
    far = _cand("far", _samples([50, 55, 50, 48]), sep=100, prior=80)
    far_bright = score_target(far, window_start=START, window_end=END, moon_illumination=0.95)
    assert dim > bright
    assert far_bright > bright


def test_direction_mapping() -> None:
    assert compass_direction(0) == "North"
    assert compass_direction(45) == "Northeast"
    assert compass_direction(180) == "South"
    assert compass_direction(359) == "North"
    assert altitude_phrase(10) == "low on the horizon"
    assert altitude_phrase(25) == "fairly low"
    assert altitude_phrase(45) == "about halfway up the sky"
    assert altitude_phrase(65) == "high in the sky"
    assert altitude_phrase(80) == "almost overhead"
    assert pointing_direction(45, 45) == "Northeast, about halfway up the sky"


def test_planets_only_when_visible() -> None:
    hidden = _cand("mars", _samples([-10, -5, -2, -1]), kind="planet", name="Mars")
    visible = _cand("jupiter", _samples([30, 40, 45, 40]), kind="planet", name="Jupiter")
    ranked = rank_targets(
        [hidden, visible], window_start=START, window_end=END, moon_illumination=0.3
    )
    names = [t.name for t in ranked]
    assert "Jupiter" in names
    assert "Mars" not in names
