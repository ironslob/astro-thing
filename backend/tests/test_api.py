from __future__ import annotations

from datetime import UTC, datetime, timedelta

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db, get_weather_cache
from app.core.db import Base
from app.core.redis import set_redis
from app.main import create_app
from app.models.catalogue import DeepSkyObject
from app.models.place import UkPlace
from app.weather.cache import WeatherCacheService
from tests.fakes import FakeWeatherProvider, forecast_from_builder, hour


@pytest.fixture
def fake_forecast():
    start = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) - timedelta(hours=2)
    return forecast_from_builder(
        start, 96, lambda when, _i: hour(when, cloud=12, low=5, mid=5, high=15)
    )


@pytest.fixture
def client(fake_forecast):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.add(
        UkPlace(
            name="Hove",
            display_name="Hove, England",
            region="England",
            latitude=50.8279,
            longitude=-0.1688,
            place_type="town",
            population=91000,
            search_name="hove",
        )
    )
    db.add(
        UkPlace(
            name="BN3",
            display_name="BN3, Hove",
            region="England",
            latitude=50.83,
            longitude=-0.17,
            place_type="outcode",
            population=0,
            search_name="bn3",
        )
    )
    db.add(
        DeepSkyObject(
            id="ngc-224",
            primary_name="NGC 224",
            common_name="Andromeda Galaxy",
            catalogue_ids=["M31", "NGC 224"],
            object_type="galaxy",
            friendly_type="Galaxy",
            ra=10.6847,
            dec=41.269,
            magnitude=3.4,
            angular_size=190,
            beginner_prior=100,
            extra={},
        )
    )
    db.commit()
    db.close()

    provider = FakeWeatherProvider(forecast=fake_forecast)
    redis = fakeredis.FakeRedis(decode_responses=True)
    set_redis(redis)

    def override_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    def override_cache():
        session = Session()
        try:
            yield WeatherCacheService(session, provider, redis_client=redis)
        finally:
            session.close()

    application = create_app()
    application.dependency_overrides[get_db] = override_db
    application.dependency_overrides[get_weather_cache] = override_cache
    with TestClient(application) as c:
        c.extra = {"provider": provider, "redis": redis, "Session": Session}
        yield c
    set_redis(None)


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["scoring_version"]


def test_location_search(client: TestClient) -> None:
    r = client.get("/api/v1/locations/search", params={"q": "Hove"})
    assert r.status_code == 200
    names = [x["display_name"] for x in r.json()["results"]]
    assert any("Hove" in n for n in names)


def test_outcode_search(client: TestClient) -> None:
    r = client.get("/api/v1/locations/search", params={"q": "BN3 2AB"})
    assert r.status_code == 200
    assert r.json()["results"]


def test_windows_anonymous_and_single_provider_call(client: TestClient) -> None:
    r = client.get("/api/v1/forecast/windows", params={"lat": 50.8279, "lon": -0.1688})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["windows"]
    assert {w["rating"] for w in body["windows"]} <= {"Excellent", "Good", "Fair", "Poor"}
    assert all("explanation" in w for w in body["windows"])
    r2 = client.get("/api/v1/forecast/windows", params={"lat": 50.8279, "lon": -0.1688})
    assert r2.status_code == 200
    assert client.extra["provider"].calls == 1


def test_rejects_non_uk(client: TestClient) -> None:
    r = client.get("/api/v1/forecast/windows", params={"lat": 40.7, "lon": -74.0})
    assert r.status_code == 400


def test_saved_locations_require_auth(client: TestClient) -> None:
    r = client.get("/api/v1/me/locations")
    assert r.status_code == 401
    r = client.post(
        "/api/v1/me/locations",
        json={"name": "Hove", "latitude": 50.83, "longitude": -0.17},
    )
    assert r.status_code == 401


def test_magic_link_save_rename_delete_history(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("app.services.auth._send_email", lambda *a, **k: None)
    r = client.post("/api/v1/auth/magic-link", json={"email": "sky@example.com"})
    assert r.status_code == 200
    keys = list(client.extra["redis"].scan_iter("magic:*"))
    assert keys
    token = keys[0].split(":", 1)[1]
    r = client.get("/api/v1/auth/verify", params={"token": token})
    assert r.status_code == 200
    assert client.get("/api/v1/me").json()["user"]["email"] == "sky@example.com"

    created = client.post(
        "/api/v1/me/locations",
        json={"name": "Hove", "latitude": 50.8279, "longitude": -0.1688},
    )
    assert created.status_code == 201, created.text
    loc_id = created.json()["id"]
    renamed = client.patch(f"/api/v1/me/locations/{loc_id}", json={"name": "Home"})
    assert renamed.json()["name"] == "Home"

    refreshed = client.post(f"/api/v1/me/locations/{loc_id}/refresh")
    assert refreshed.status_code == 200
    hist = client.get(f"/api/v1/me/locations/{loc_id}/history")
    assert hist.status_code == 200
    assert hist.json()["history"]

    gone = client.delete(f"/api/v1/me/locations/{loc_id}")
    assert gone.status_code == 200
    assert client.get("/api/v1/me/locations").json()["locations"] == []
