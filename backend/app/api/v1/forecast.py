from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.deps import DbDep, get_weather_cache, validate_uk_coords
from app.api.rate_limit import enforce_forecast_rate_limit
from app.services.forecast import ForecastService, ForecastUnavailable
from app.weather.cache import WeatherCacheService
from app.weather.provider import WeatherProviderError

router = APIRouter()


@router.get("/forecast/windows")
def windows(
    request: Request,
    db: DbDep,
    lat: float = Query(),
    lon: float = Query(),
    cache: WeatherCacheService = Depends(get_weather_cache),
) -> dict:
    enforce_forecast_rate_limit(request)
    lat, lon = validate_uk_coords(lat, lon)
    service = ForecastService(db, cache)
    try:
        return service.windows(lat, lon)
    except WeatherProviderError as exc:
        raise HTTPException(
            status_code=503,
            detail="We couldn't check the clouds just now. Please try again in a moment.",
        ) from exc


@router.get("/forecast/targets")
def targets(
    request: Request,
    db: DbDep,
    lat: float = Query(),
    lon: float = Query(),
    start: datetime = Query(),
    end: datetime = Query(),
    cache: WeatherCacheService = Depends(get_weather_cache),
) -> dict:
    enforce_forecast_rate_limit(request)
    lat, lon = validate_uk_coords(lat, lon)
    if end <= start:
        raise HTTPException(status_code=400, detail="The window end needs to be after the start.")
    service = ForecastService(db, cache)
    try:
        return service.targets(lat, lon, start, end)
    except WeatherProviderError as exc:
        raise HTTPException(
            status_code=503,
            detail="We couldn't check the clouds just now. Please try again in a moment.",
        ) from exc
    except ForecastUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
