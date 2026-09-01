from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.deps import get_geocoding_service
from app.api.rate_limit import enforce_geocoding_rate_limit
from app.geocoding.provider import GeocodingProviderError
from app.geocoding.service import GeocodingService

router = APIRouter()


@router.get("/locations/search")
def search(
    request: Request,
    q: str = Query(min_length=2, max_length=80),
    geo: GeocodingService = Depends(get_geocoding_service),
) -> dict:
    enforce_geocoding_rate_limit(request)
    try:
        rows = geo.search(q)
    except GeocodingProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We couldn't look up that place just now. Please try again in a moment.",
        ) from exc
    return {"results": [r.as_dict() for r in rows]}
