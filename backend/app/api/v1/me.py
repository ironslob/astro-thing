from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import DbDep, get_weather_cache, require_user
from app.models.user import User
from app.services import saved as saved_service
from app.services.forecast import ForecastService
from app.services.locations import is_uk
from app.weather.cache import WeatherCacheService
from app.weather.provider import WeatherProviderError

router = APIRouter()
UserDep = Annotated[User, Depends(require_user)]


class LocationIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    latitude: float
    longitude: float


class LocationPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)


def _loc_out(loc) -> dict:
    return {
        "id": str(loc.id),
        "name": loc.name,
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "created_at": loc.created_at.isoformat() if loc.created_at else None,
        "updated_at": loc.updated_at.isoformat() if loc.updated_at else None,
    }


@router.get("/me/locations")
def list_locations(db: DbDep, user: UserDep) -> dict:
    rows = saved_service.list_locations(db, user.id)
    return {"locations": [_loc_out(r) for r in rows]}


@router.post("/me/locations", status_code=201)
def create_location(payload: LocationIn, db: DbDep, user: UserDep) -> dict:
    if not is_uk(payload.latitude, payload.longitude):
        raise HTTPException(status_code=400, detail="Saved locations must be in the UK.")
    loc = saved_service.create_location(
        db, user.id, payload.name, payload.latitude, payload.longitude
    )
    return _loc_out(loc)


@router.patch("/me/locations/{location_id}")
def patch_location(location_id: UUID, payload: LocationPatch, db: DbDep, user: UserDep) -> dict:
    loc = saved_service.get_owned(db, user.id, location_id)
    if loc is None:
        raise HTTPException(status_code=404, detail="Location not found.")
    loc = saved_service.update_location(db, loc, payload.name)
    return _loc_out(loc)


@router.delete("/me/locations/{location_id}")
def delete_location(location_id: UUID, db: DbDep, user: UserDep) -> dict:
    loc = saved_service.get_owned(db, user.id, location_id)
    if loc is None:
        raise HTTPException(status_code=404, detail="Location not found.")
    saved_service.delete_location(db, loc)
    return {"ok": True}


@router.get("/me/locations/{location_id}/history")
def location_history(location_id: UUID, db: DbDep, user: UserDep) -> dict:
    loc = saved_service.get_owned(db, user.id, location_id)
    if loc is None:
        raise HTTPException(status_code=404, detail="Location not found.")
    rows = saved_service.history(db, loc)
    return {
        "location": _loc_out(loc),
        "history": [
            {
                "id": str(r.id),
                "generated_at": r.generated_at.isoformat(),
                "forecast_fetched_at": (
                    r.forecast_fetched_at.isoformat() if r.forecast_fetched_at else None
                ),
                "assessment": r.assessment,
            }
            for r in rows
        ],
    }


@router.post("/me/locations/{location_id}/refresh")
def refresh_location(
    location_id: UUID,
    db: DbDep,
    user: UserDep,
    cache: WeatherCacheService = Depends(get_weather_cache),
) -> dict:
    loc = saved_service.get_owned(db, user.id, location_id)
    if loc is None:
        raise HTTPException(status_code=404, detail="Location not found.")
    service = ForecastService(db, cache)
    try:
        payload = service.windows(loc.latitude, loc.longitude)
    except WeatherProviderError as exc:
        raise HTTPException(status_code=503, detail="Couldn't refresh the forecast.") from exc
    fetched = None
    if payload.get("forecast", {}).get("fetched_at"):
        fetched = datetime.fromisoformat(payload["forecast"]["fetched_at"])
    saved_service.persist_assessment(db, loc.id, payload, fetched)
    return payload
