from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.assessment import ObservationAssessment
from app.models.location import SavedLocation
from app.weather.geocell import cell_key


def list_locations(db: Session, user_id: UUID) -> list[SavedLocation]:
    return (
        db.query(SavedLocation)
        .filter(SavedLocation.user_id == user_id)
        .order_by(SavedLocation.updated_at.desc())
        .all()
    )


def create_location(
    db: Session, user_id: UUID, name: str, latitude: float, longitude: float
) -> SavedLocation:
    loc = SavedLocation(user_id=user_id, name=name.strip(), latitude=latitude, longitude=longitude)
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


def get_owned(db: Session, user_id: UUID, location_id: UUID) -> SavedLocation | None:
    loc = db.get(SavedLocation, location_id)
    if loc is None or loc.user_id != user_id:
        return None
    return loc


def update_location(db: Session, loc: SavedLocation, name: str | None) -> SavedLocation:
    if name is not None:
        loc.name = name.strip()
    db.commit()
    db.refresh(loc)
    return loc


def delete_location(db: Session, loc: SavedLocation) -> None:
    db.delete(loc)
    db.commit()


def persist_assessment(
    db: Session,
    saved_location_id: UUID,
    assessment: dict,
    forecast_fetched_at: datetime | None,
) -> ObservationAssessment | None:
    windows = assessment.get("windows", assessment)
    blob = json.dumps(windows, sort_keys=True, default=str)
    digest = hashlib.sha256(blob.encode()).hexdigest()
    last = (
        db.query(ObservationAssessment)
        .filter(ObservationAssessment.saved_location_id == saved_location_id)
        .order_by(ObservationAssessment.generated_at.desc())
        .first()
    )
    if last and last.assessment_hash == digest:
        return None
    row = ObservationAssessment(
        saved_location_id=saved_location_id,
        generated_at=datetime.now(UTC),
        forecast_fetched_at=forecast_fetched_at,
        assessment_hash=digest,
        assessment=assessment,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def history(db: Session, loc: SavedLocation, limit: int = 20) -> list[ObservationAssessment]:
    return (
        db.query(ObservationAssessment)
        .filter(ObservationAssessment.saved_location_id == loc.id)
        .order_by(ObservationAssessment.generated_at.desc())
        .limit(limit)
        .all()
    )


def cells_for_locations(locations: list[SavedLocation]) -> dict[str, list[SavedLocation]]:
    grouped: dict[str, list[SavedLocation]] = {}
    for loc in locations:
        grouped.setdefault(cell_key(loc.latitude, loc.longitude), []).append(loc)
    return grouped
