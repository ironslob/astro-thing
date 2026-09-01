from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.types import JSON_DOC, UUID_PK


class ObservationAssessment(Base):
    __tablename__ = "observation_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=uuid.uuid4)
    saved_location_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("saved_locations.id", ondelete="CASCADE"), index=True
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    forecast_fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    assessment_hash: Mapped[str] = mapped_column(String(64), index=True)
    assessment: Mapped[dict] = mapped_column(JSON_DOC)

    saved_location = relationship("SavedLocation", back_populates="assessments")
