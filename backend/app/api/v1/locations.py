from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DbDep
from app.services.locations import search_places

router = APIRouter()


@router.get("/locations/search")
def search(db: DbDep, q: str = Query(min_length=2, max_length=80)) -> dict:
    rows = search_places(db, q)
    return {
        "results": [
            {
                "display_name": r.display_name,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "place_type": r.place_type,
            }
            for r in rows
        ]
    }
