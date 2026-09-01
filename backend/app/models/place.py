from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class UkPlace(Base):
    __tablename__ = "uk_places"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    display_name: Mapped[str] = mapped_column(String(256))
    region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    place_type: Mapped[str] = mapped_column(String(32), index=True)
    population: Mapped[int] = mapped_column(Integer, default=0)
    search_name: Mapped[str] = mapped_column(String(128), index=True)
