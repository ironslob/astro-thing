from __future__ import annotations

import json
from typing import Any

from app.core.config import settings
from app.geocoding.provider import GeocodingProvider, GeocodingProviderError, PlaceMatch
from app.services.locations import classify_query, is_uk, normalize_query


class GeocodingService:
    def __init__(
        self,
        places: GeocodingProvider,
        postcodes: GeocodingProvider,
        redis_client: Any | None = None,
        cache_ttl_seconds: int | None = None,
    ) -> None:
        self.places = places
        self.postcodes = postcodes
        self.redis = redis_client
        self.cache_ttl = cache_ttl_seconds or settings.geocoding_cache_ttl_seconds

    def search(self, q: str, limit: int = 8) -> list[PlaceMatch]:
        needle = normalize_query(q)
        if len(needle) < 2:
            return []
        cached = self._cache_get(needle)
        if cached is not None:
            return cached[:limit]
        try:
            if classify_query(q) == "postcode":
                rows = self.postcodes.search(q, limit=limit)
            else:
                rows = self.places.search(q, limit=limit)
        except GeocodingProviderError:
            raise
        except Exception as exc:
            raise GeocodingProviderError(f"Geocoding failed: {exc}") from exc
        filtered = [r for r in rows if is_uk(r.latitude, r.longitude)]
        self._cache_set(needle, filtered)
        return filtered[:limit]

    def _cache_key(self, needle: str) -> str:
        return f"geo:v1:{needle}"

    def _cache_get(self, needle: str) -> list[PlaceMatch] | None:
        if self.redis is None:
            return None
        try:
            raw = self.redis.get(self._cache_key(needle))
        except Exception:
            return None
        if not raw:
            return None
        try:
            payload = json.loads(raw)
        except (TypeError, ValueError):
            return None
        if not isinstance(payload, list):
            return None
        out: list[PlaceMatch] = []
        for row in payload:
            try:
                out.append(
                    PlaceMatch(
                        display_name=str(row["display_name"]),
                        latitude=float(row["latitude"]),
                        longitude=float(row["longitude"]),
                        place_type=str(row.get("place_type") or "town"),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return out

    def _cache_set(self, needle: str, rows: list[PlaceMatch]) -> None:
        if self.redis is None:
            return
        try:
            self.redis.setex(
                self._cache_key(needle),
                self.cache_ttl,
                json.dumps([r.as_dict() for r in rows]),
            )
        except Exception:
            return
