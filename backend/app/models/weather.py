from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.types import JSON_DOC


class WeatherForecastCache(Base):
    __tablename__ = "weather_forecast_cache"

    cell_key: Mapped[str] = mapped_column(String(32), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    forecast_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    forecast_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict] = mapped_column(JSON_DOC)
