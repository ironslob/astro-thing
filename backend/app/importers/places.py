from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.place import UkPlace

ROOT_CANDIDATES = [
    Path("/data/places"),
    Path(__file__).resolve().parents[3] / "data" / "places",
]


def _dir() -> Path:
    for p in ROOT_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError("places data directory not found")


def import_places(db: Session) -> int:
    folder = _dir()
    places = json.loads((folder / "uk_places.json").read_text())
    outcodes = json.loads((folder / "uk_outcodes.json").read_text())
    db.execute(delete(UkPlace))
    db.commit()
    batch: list[UkPlace] = []
    for row in places + outcodes:
        batch.append(
            UkPlace(
                name=row["name"],
                display_name=row["display_name"],
                region=row.get("region"),
                latitude=row["latitude"],
                longitude=row["longitude"],
                place_type=row.get("place_type") or "town",
                population=int(row.get("population") or 0),
                search_name=row.get("search_name") or row["name"].lower(),
            )
        )
        if len(batch) >= 500:
            db.add_all(batch)
            db.commit()
            batch = []
    if batch:
        db.add_all(batch)
        db.commit()
    return db.query(UkPlace).count()
