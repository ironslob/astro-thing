from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol


@dataclass(frozen=True)
class PlaceMatch:
    display_name: str
    latitude: float
    longitude: float
    place_type: str

    def as_dict(self) -> dict:
        return asdict(self)


class GeocodingProvider(Protocol):
    name: str

    def search(self, q: str, limit: int = 8) -> list[PlaceMatch]:
        """Return compact place matches. Must not leak vendor payload shapes."""


class GeocodingProviderError(Exception):
    """Raised when a live geocoding provider cannot be reached or parsed."""
