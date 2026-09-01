from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models.location import SavedLocation
from app.models.user import User
from app.services.saved import persist_assessment
from app.workers.tasks import refresh_saved_locations


def test_persist_assessment_skips_identical_payload(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    user = User(email="a@example.com")
    db.add(user)
    db.commit()
    loc = SavedLocation(user_id=user.id, name="Hove", latitude=50.83, longitude=-0.14)
    db.add(loc)
    db.commit()
    payload = {"windows": [{"rating": "Good"}]}
    first = persist_assessment(db, loc.id, payload, datetime.now(UTC))
    second = persist_assessment(db, loc.id, payload, datetime.now(UTC))
    assert first is not None
    assert second is None


def test_refresh_task_groups_by_cell_and_is_idempotent(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    calls = {"n": 0}

    class DummyService:
        def __init__(self, db, cache):
            pass

        def windows(self, lat, lon):
            calls["n"] += 1
            return {
                "windows": [{"rating": "Fair", "lat": lat}],
                "forecast": {"fetched_at": datetime.now(UTC).isoformat()},
            }

    monkeypatch.setattr("app.workers.tasks.SessionLocal", Session)
    monkeypatch.setattr("app.workers.tasks.ForecastService", DummyService)
    monkeypatch.setattr("app.workers.tasks.WeatherCacheService", lambda **kwargs: object())
    monkeypatch.setattr("app.workers.tasks.get_redis", lambda: None)
    monkeypatch.setattr("app.workers.tasks.OpenMeteoWeatherProvider", lambda: object())

    db = Session()
    user = User(email="b@example.com")
    db.add(user)
    db.commit()
    # Two locations in the same ~5km cell
    db.add(
        SavedLocation(user_id=user.id, name="Hove seafront", latitude=50.8279, longitude=-0.1688)
    )
    db.add(SavedLocation(user_id=user.id, name="Hove park", latitude=50.8300, longitude=-0.1700))
    db.commit()

    result = refresh_saved_locations()
    assert calls["n"] == 1
    assert result["written"] == 2
    result2 = refresh_saved_locations()
    assert result2["skipped"] == 2
