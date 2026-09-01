from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.db import Base
from app.domain.models import NormalizedForecast
from app.weather.cache import WeatherCacheService
from app.weather.provider import WeatherProviderError
from tests.fakes import FakeWeatherProvider, forecast_from_builder, hour

NOW = datetime(2026, 1, 15, 18, 0, tzinfo=UTC)


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _forecast() -> NormalizedForecast:
    return forecast_from_builder(NOW, 72, lambda when, _i: hour(when, cloud=20))


def test_fresh_cache_does_not_call_provider() -> None:
    db = _session()
    provider = FakeWeatherProvider(forecast=_forecast())
    cache = WeatherCacheService(db, provider, redis_client=None, now_fn=lambda: NOW)
    cache.get(50.83, -0.14)
    assert provider.calls == 1
    cache.get(50.83, -0.14)
    assert provider.calls == 1
    cache.get(50.829, -0.141)  # same geohash-5 cell
    assert provider.calls == 1


def test_cache_miss_makes_one_full_horizon_call() -> None:
    db = _session()
    provider = FakeWeatherProvider(forecast=_forecast())
    cache = WeatherCacheService(db, provider, redis_client=None, now_fn=lambda: NOW)
    result = cache.get(50.83, -0.14)
    assert provider.calls == 1
    assert (result.forecast_end - result.forecast_start) >= timedelta(hours=48)


def test_provider_failure_with_stale_cache_returns_stale() -> None:
    db = _session()
    provider = FakeWeatherProvider(forecast=_forecast())
    t0 = NOW
    cache = WeatherCacheService(db, provider, redis_client=None, now_fn=lambda: t0)
    cache.get(50.83, -0.14)
    provider.fail = True
    later = t0 + timedelta(minutes=45)  # past 30 min fresh TTL, within 2h stale
    cache.now_fn = lambda: later
    result = cache.get(50.83, -0.14)
    assert result.stale is True
    assert provider.calls == 2


def test_provider_failure_without_cache_raises() -> None:
    db = _session()
    provider = FakeWeatherProvider(fail=True)
    cache = WeatherCacheService(db, provider, redis_client=None, now_fn=lambda: NOW)
    try:
        cache.get(50.83, -0.14)
        raise AssertionError("expected failure")
    except WeatherProviderError:
        pass
    assert provider.calls == 1
