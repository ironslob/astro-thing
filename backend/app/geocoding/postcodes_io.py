from __future__ import annotations

import re

import httpx

from app.core.config import settings
from app.geocoding.provider import GeocodingProviderError, PlaceMatch

_FULL_POSTCODE = re.compile(r"^[A-Z]{1,2}\d[A-Z\d]?\d[A-Z]{2}$")


class PostcodesIoProvider:
    name = "postcodes-io"

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (base_url or settings.postcodes_io_base_url).rstrip("/")
        self.timeout = timeout or settings.geocoding_request_timeout_seconds
        self._client = client

    def search(self, q: str, limit: int = 8) -> list[PlaceMatch]:
        compact = re.sub(r"\s+", "", q.strip().upper())
        if _FULL_POSTCODE.match(compact):
            inward = compact[-3:]
            outward = compact[:-3]
            formatted = f"{outward} {inward}"
            return self._lookup(f"/postcodes/{formatted}", place_type="postcode")[:limit]
        return self._lookup(f"/outcodes/{compact}", place_type="outcode")[:limit]

    def _lookup(self, path: str, *, place_type: str) -> list[PlaceMatch]:
        url = f"{self.base_url}{path}"
        try:
            if self._client is not None:
                resp = self._client.get(url, timeout=self.timeout)
            else:
                resp = httpx.get(url, timeout=self.timeout)
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise GeocodingProviderError(f"postcodes.io request failed: {exc}") from exc
        if not isinstance(data, dict):
            raise GeocodingProviderError("postcodes.io returned an unexpected payload")
        row = data.get("result")
        if not isinstance(row, dict):
            return []
        try:
            lat = float(row["latitude"])
            lon = float(row["longitude"])
        except (KeyError, TypeError, ValueError):
            return []
        code = str(row.get("postcode") or row.get("outcode") or "").strip()
        district = _district(row)
        display = (
            f"{code}, {district}" if code and district else (code or district or "UK postcode")
        )
        return [
            PlaceMatch(
                display_name=display,
                latitude=lat,
                longitude=lon,
                place_type=place_type,
            )
        ]


def _district(row: dict) -> str:
    for key in ("admin_district", "parish", "region", "country"):
        value = row.get(key)
        if isinstance(value, list):
            value = next((v for v in value if v), None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""
