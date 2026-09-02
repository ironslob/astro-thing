from __future__ import annotations

from datetime import UTC, datetime, timedelta

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db, get_geocoding_service, get_weather_cache
from app.core.db import Base
from app.core.redis import set_redis
from app.geocoding.service import GeocodingService
from app.importers.search_text import build_search_text
from app.main import create_app
from app.models.catalogue import DeepSkyObject
from app.weather.cache import WeatherCacheService
from tests.fakes import (
    FakePlacesProvider,
    FakePostcodesProvider,
    FakeWeatherProvider,
    forecast_from_builder,
    hour,
)


def _dso(
    ident: str,
    primary: str,
    *,
    common: str | None = None,
    ids: list[str] | None = None,
    otype: str = "galaxy",
    friendly: str = "Galaxy",
    ra: float = 10.6847,
    dec: float = 41.269,
    mag: float = 3.4,
    size: float = 190,
    prior: int = 100,
) -> DeepSkyObject:
    ids = ids or [primary]
    return DeepSkyObject(
        id=ident,
        primary_name=primary,
        common_name=common,
        catalogue_ids=ids,
        object_type=otype,
        friendly_type=friendly,
        ra=ra,
        dec=dec,
        magnitude=mag,
        angular_size=size,
        beginner_prior=prior,
        search_text=build_search_text(primary, common, ids),
        extra={},
    )


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
        _dso(
            "ngc-224",
            "NGC 224",
            common="Andromeda Galaxy",
            ids=["M31", "NGC 224"],
        )
    )
    db.add(
        _dso(
            "mel-22",
            "Mel 22",
            common="Pleiades",
            ids=["M45", "Pleiades"],
            otype="open_cluster",
            friendly="Open cluster",
            ra=56.871,
            dec=24.105,
            mag=1.2,
            size=150,
            prior=100,
        )
    )
    db.add(
        _dso(
            "ngc-9999",
            "NGC 9999",
            ids=["NGC 9999"],
            mag=14.0,
            size=1,
            prior=20,
        )
    )
    db.commit()
    db.close()

    provider = FakeWeatherProvider(forecast=fake_forecast)
    places = FakePlacesProvider()
    postcodes = FakePostcodesProvider()
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

    def override_geo():
        return GeocodingService(places, postcodes, redis_client=redis)

    application = create_app()
    application.dependency_overrides[get_db] = override_db
    application.dependency_overrides[get_weather_cache] = override_cache
    application.dependency_overrides[get_geocoding_service] = override_geo
    with TestClient(application) as c:
        c.extra = {
            "provider": provider,
            "places": places,
            "postcodes": postcodes,
            "redis": redis,
            "Session": Session,
        }
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
    assert client.extra["places"].calls
    assert client.extra["postcodes"].calls == []


def test_outcode_search(client: TestClient) -> None:
    r = client.get("/api/v1/locations/search", params={"q": "BN3 2AB"})
    assert r.status_code == 200
    assert r.json()["results"]
    assert client.extra["postcodes"].calls
    assert client.extra["places"].calls == []


def test_four_letter_town_is_not_an_outcode(client: TestClient) -> None:
    r = client.get("/api/v1/locations/search", params={"q": "Bath"})
    assert r.status_code == 200
    assert any("Bath" in x["display_name"] for x in r.json()["results"])
    assert client.extra["places"].calls
    assert client.extra["postcodes"].calls == []


def test_location_search_provider_error(client: TestClient) -> None:
    client.extra["places"].fail = True
    r = client.get("/api/v1/locations/search", params={"q": "Hove"})
    assert r.status_code == 503


def test_catalogue_search(client: TestClient) -> None:
    r = client.get("/api/v1/catalogue/search", params={"q": "Andromeda"})
    assert r.status_code == 200
    ids = [x["id"] for x in r.json()["results"]]
    assert "ngc-224" in ids
    andromeda = next(x for x in r.json()["results"] if x["id"] == "ngc-224")
    assert andromeda["images"][0]["url"].startswith("https://upload.wikimedia.org/")
    r = client.get("/api/v1/catalogue/search", params={"q": "Pleiades"})
    assert any(x["id"] == "mel-22" for x in r.json()["results"])
    r = client.get("/api/v1/catalogue/search", params={"q": "Venus"})
    venus = next(x for x in r.json()["results"] if x["id"] == "venus")
    assert venus["images"][0]["url"]


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


def test_targets_rank_beginner_objects_and_pin(client: TestClient) -> None:
    windows = client.get("/api/v1/forecast/windows", params={"lat": 50.8279, "lon": -0.1688})
    assert windows.status_code == 200
    window = windows.json()["windows"][0]
    r = client.get(
        "/api/v1/forecast/targets",
        params={
            "lat": 50.8279,
            "lon": -0.1688,
            "start": window["start"],
            "end": window["end"],
        },
    )
    assert r.status_code == 200, r.text
    ids = [t["id"] for t in r.json()["targets"]]
    assert "ngc-9999" not in ids
    assert "ngc-224" in ids or "mel-22" in ids

    pinned = client.get(
        "/api/v1/forecast/targets",
        params={
            "lat": 50.8279,
            "lon": -0.1688,
            "start": window["start"],
            "end": window["end"],
            "object": "ngc-9999",
        },
    )
    assert pinned.status_code == 200
    names = [t["id"] for t in pinned.json()["targets"]]
    assert names[0] == "ngc-9999"
    assert names.count("ngc-9999") == 1
    assert pinned.json()["targets"][0]["images"] == []

    andromeda = client.get(
        "/api/v1/forecast/targets",
        params={
            "lat": 50.8279,
            "lon": -0.1688,
            "start": window["start"],
            "end": window["end"],
            "object": "ngc-224",
        },
    )
    assert andromeda.status_code == 200
    lead = andromeda.json()["targets"][0]
    assert lead["id"] == "ngc-224"
    assert len(lead["images"]) >= 2
    assert lead["images"][0]["url"].startswith("https://upload.wikimedia.org/")
    assert lead["images"][0]["credit"]

    planet = client.get(
        "/api/v1/forecast/targets",
        params={
            "lat": 50.8279,
            "lon": -0.1688,
            "start": window["start"],
            "end": window["end"],
            "object": "venus",
        },
    )
    assert planet.status_code == 200
    assert planet.json()["targets"][0]["id"] == "venus"

    missing = client.get(
        "/api/v1/forecast/targets",
        params={
            "lat": 50.8279,
            "lon": -0.1688,
            "start": window["start"],
            "end": window["end"],
            "object": "not-a-real-object",
        },
    )
    assert missing.status_code == 404


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
