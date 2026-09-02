from __future__ import annotations

from app.geocoding.service import GeocodingService
from app.services.locations import classify_query
from tests.fakes import FakePlacesProvider, FakePostcodesProvider


def test_classify_hove_is_place() -> None:
    assert classify_query("Hove") == "place"
    assert classify_query("Ho") == "place"
    assert classify_query("Bath") == "place"


def test_classify_postcodes() -> None:
    assert classify_query("BN3") == "postcode"
    assert classify_query("BN3 2AB") == "postcode"
    assert classify_query("bn32ab") == "postcode"
    assert classify_query("EC1A 1BB") == "postcode"
    assert classify_query("M1") == "postcode"


def test_service_routes_town_to_places() -> None:
    places = FakePlacesProvider()
    postcodes = FakePostcodesProvider()
    geo = GeocodingService(places, postcodes, redis_client=None)
    rows = geo.search("Hove")
    assert rows and "Hove" in rows[0].display_name
    assert places.calls == ["Hove"]
    assert postcodes.calls == []


def test_service_routes_full_postcode_to_postcodes_io() -> None:
    places = FakePlacesProvider()
    postcodes = FakePostcodesProvider()
    geo = GeocodingService(places, postcodes, redis_client=None)
    rows = geo.search("BN3 2AB")
    assert rows
    assert postcodes.calls == ["BN3 2AB"]
    assert places.calls == []


def test_service_does_not_treat_bath_as_outcode() -> None:
    places = FakePlacesProvider()
    postcodes = FakePostcodesProvider()
    geo = GeocodingService(places, postcodes, redis_client=None)
    rows = geo.search("Bath")
    assert rows and "Bath" in rows[0].display_name
    assert places.calls
    assert postcodes.calls == []


def test_service_caches_results() -> None:
    places = FakePlacesProvider()
    postcodes = FakePostcodesProvider()
    redis: dict[str, str] = {}

    class Memory:
        def get(self, key: str):
            return redis.get(key)

        def setex(self, key: str, _ttl: int, value: str) -> None:
            redis[key] = value

    geo = GeocodingService(places, postcodes, redis_client=Memory())
    first = geo.search("Hove")
    second = geo.search("Hove")
    assert first == second
    assert places.calls == ["Hove"]
