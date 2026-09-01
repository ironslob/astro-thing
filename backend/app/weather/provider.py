from __future__ import annotations

from typing import Protocol

from app.domain.models import NormalizedForecast


class WeatherProvider(Protocol):
    name: str

    def fetch(self, latitude: float, longitude: float) -> NormalizedForecast:
        """Return a normalized multi-night hourly forecast.

        Implementations must not leak vendor-specific payload shapes.
        """


class WeatherProviderError(Exception):
    """Raised when a live weather provider cannot be reached or parsed."""
