from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.types import JSON_DOC


class DeepSkyObject(Base):
    __tablename__ = "deep_sky_objects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    primary_name: Mapped[str] = mapped_column(String(128), index=True)
    common_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    catalogue_ids: Mapped[list] = mapped_column(JSON_DOC)
    object_type: Mapped[str] = mapped_column(String(64), index=True)
    friendly_type: Mapped[str] = mapped_column(String(64))
    ra: Mapped[float] = mapped_column(Float)
    dec: Mapped[float] = mapped_column(Float)
    magnitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    angular_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    beginner_prior: Mapped[int] = mapped_column(Integer, default=50, index=True)
    search_text: Mapped[str] = mapped_column(String(1024), default="", index=True)
    extra: Mapped[dict] = mapped_column("metadata", JSON_DOC, default=dict)
    images: Mapped[list] = mapped_column(JSON_DOC, default=list)


class CatalogueMeta(Base):
    """Digest of the bundled catalogue files last applied to this database."""

    __tablename__ = "catalogue_meta"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    digest: Mapped[str] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
