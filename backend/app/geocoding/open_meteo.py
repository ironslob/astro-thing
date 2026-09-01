from __future__ import annotations

import httpx

from app.core.config import settings
from app.geocoding.provider import GeocodingProviderError, PlaceMatch

_FEATURE_TYPES = {
    "PPLC": "city",
    "PPLA": "city",
    "PPLA2": "city",
    "PPLA3": "town",
    "PPLA4": "town",
    "PPL": "town",
    "PPLX": "town",
    "STLMT": "town",
}


class OpenMeteoGeocodingProvider:
    name = "open-meteo-geocoding"

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (base_url or settings.open_meteo_geocoding_base_url).rstrip("/")
        self.timeout = timeout or settings.geocoding_request_timeout_seconds
        self._client = client

    def search(self, q: str, limit: int = 8) -> list[PlaceMatch]:
        params = {
            "name": q.strip(),
            "count": max(1, min(limit, 20)),
            "language": "en",
            "format": "json",
            "countryCode": "GB",
        }
        url = f"{self.base_url}/v1/search"
        try:
            if self._client is not None:
                resp = self._client.get(url, params=params, timeout=self.timeout)
            else:
                resp = httpx.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise GeocodingProviderError(f"Open-Meteo geocoding failed: {exc}") from exc
        if not isinstance(data, dict):
            raise GeocodingProviderError("Open-Meteo geocoding returned an unexpected payload")
        out: list[PlaceMatch] = []
        for row in data.get("results") or []:
            try:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
            except (KeyError, TypeError, ValueError):
                continue
            name = str(row.get("name") or "").strip()
            if not name:
                continue
            admin = str(row.get("admin1") or "").strip()
            display = f"{name}, {admin}" if admin and admin.lower() != name.lower() else name
            code = str(row.get("feature_code") or "")
            out.append(
                PlaceMatch(
                    display_name=display,
                    latitude=lat,
                    longitude=lon,
                    place_type=_FEATURE_TYPES.get(code, "town"),
                )
            )
        return out[:limit]
