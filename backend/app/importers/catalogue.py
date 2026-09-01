from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.importers.search_text import build_search_text
from app.models.catalogue import DeepSkyObject

DATA_CANDIDATES = [
    Path("/data/catalogue"),
    Path(__file__).resolve().parents[3] / "data" / "catalogue",
]


def catalogue_dir() -> Path:
    for p in DATA_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError("catalogue data directory not found")


def import_json_objects(db: Session, path: Path) -> int:
    data = json.loads(path.read_text())
    count = 0
    for row in data:
        count += _upsert_row(db, row)
    db.commit()
    return count


def import_bright_stars(db: Session, path: Path | None = None) -> int:
    star_path = path or catalogue_dir() / "bright_stars.json"
    if not star_path.exists():
        return 0
    return import_json_objects(db, star_path)


def _upsert_row(db: Session, row: dict) -> int:
    ident = row["id"]
    ids = list(row.get("catalogue_ids") or [])
    primary = row["primary_name"]
    common = row.get("common_name")
    payload = {
        "primary_name": primary,
        "common_name": common,
        "catalogue_ids": ids,
        "object_type": row["object_type"],
        "friendly_type": row.get("friendly_type") or row["object_type"],
        "ra": row["ra"],
        "dec": row["dec"],
        "magnitude": row.get("magnitude"),
        "angular_size": row.get("angular_size"),
        "beginner_prior": int(row.get("beginner_prior") or 50),
        "search_text": build_search_text(primary, common, ids),
        "extra": row.get("metadata") or {},
    }
    existing = db.get(DeepSkyObject, ident)
    if existing is None:
        db.add(DeepSkyObject(id=ident, **payload))
    else:
        for k, v in payload.items():
            setattr(existing, k, v)
    return 1
