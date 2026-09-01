from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.catalogue import DeepSkyObject

DATA_CANDIDATES = [
    Path("/data/catalogue/beginner_dsos.json"),
    Path(__file__).resolve().parents[3] / "data" / "catalogue" / "beginner_dsos.json",
]


def catalogue_path() -> Path:
    for p in DATA_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError("beginner_dsos.json not found")


def import_catalogue(db: Session, path: Path | None = None) -> int:
    data = json.loads((path or catalogue_path()).read_text())
    count = 0
    for row in data:
        existing = db.get(DeepSkyObject, row["id"])
        payload = {
            "primary_name": row["primary_name"],
            "common_name": row.get("common_name"),
            "catalogue_ids": row.get("catalogue_ids") or [],
            "object_type": row["object_type"],
            "friendly_type": row.get("friendly_type") or row["object_type"],
            "ra": row["ra"],
            "dec": row["dec"],
            "magnitude": row.get("magnitude"),
            "angular_size": row.get("angular_size"),
            "beginner_prior": int(row.get("beginner_prior") or 50),
            "extra": row.get("metadata") or {},
        }
        if existing is None:
            db.add(DeepSkyObject(id=row["id"], **payload))
        else:
            for k, v in payload.items():
                setattr(existing, k, v)
        count += 1
    db.commit()
    return count
