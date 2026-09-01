from __future__ import annotations

from datetime import UTC, datetime

from app.domain.ratings import rating_label
from app.domain.scoring import score_conditions
from tests.fakes import hour


def test_rating_thresholds() -> None:
    assert rating_label(80) == "Excellent"
    assert rating_label(65) == "Good"
    assert rating_label(45) == "Fair"
    assert rating_label(44.9) == "Poor"


def test_scoring_is_deterministic() -> None:
    h = hour(datetime(2026, 1, 15, 22, tzinfo=UTC), cloud=22, low=10, mid=15, high=40)
    a = score_conditions(h, -25)
    b = score_conditions(h, -25)
    assert a == b
