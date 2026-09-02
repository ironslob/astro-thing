from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.redis import get_redis
from app.core.security import parse_session_token
from app.geocoding.open_meteo import OpenMeteoGeocodingProvider
from app.geocoding.postcodes_io import PostcodesIoProvider
from app.geocoding.service import GeocodingService
from app.models.user import User
from app.services.locations import is_uk
from app.weather.cache import WeatherCacheService
from app.weather.open_meteo import OpenMeteoWeatherProvider

DbDep = Annotated[Session, Depends(get_db)]


def _optional_redis():
    try:
        client = get_redis()
        client.ping()
        return client
    except Exception:
        return None


def get_weather_cache(db: DbDep) -> WeatherCacheService:
    return WeatherCacheService(
        db=db, provider=OpenMeteoWeatherProvider(), redis_client=_optional_redis()
    )


def get_geocoding_service() -> GeocodingService:
    redis_client = _optional_redis()
    return GeocodingService(
        places=OpenMeteoGeocodingProvider(),
        postcodes=PostcodesIoProvider(),
        redis_client=redis_client,
    )


def optional_user(
    db: DbDep,
    session: Annotated[str | None, Cookie(alias=settings.session_cookie_name)] = None,
) -> User | None:
    if not session:
        return None
    data = parse_session_token(session)
    if not data:
        return None
    try:
        uid = UUID(data["uid"])
    except (KeyError, ValueError):
        return None
    return db.get(User, uid)


def require_user(user: Annotated[User | None, Depends(optional_user)]) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in required")
    return user


def validate_uk_coords(lat: float, lon: float) -> tuple[float, float]:
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Coordinates look invalid.")
    if not is_uk(lat, lon):
        raise HTTPException(
            status_code=400,
            detail="Astro Window v1 covers the UK only. Try a UK town, city or postcode.",
        )
    return lat, lon


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
