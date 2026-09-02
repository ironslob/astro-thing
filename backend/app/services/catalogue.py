from __future__ import annotations

from sqlalchemy.orm import Session

from app.astronomy.service import PLANET_LABELS
from app.domain.constants import MAJOR_PLANETS
from app.models.catalogue import DeepSkyObject
from app.services.locations import normalize_query

SOLAR_SYSTEM: list[dict] = [
    {
        "id": name,
        "display_name": PLANET_LABELS[name],
        "friendly_type": "Planet",
        "catalogue_ids": [PLANET_LABELS[name]],
    }
    for name in MAJOR_PLANETS
] + [
    {
        "id": "moon",
        "display_name": "Moon",
        "friendly_type": "Moon",
        "catalogue_ids": ["Moon"],
    }
]


def search_catalogue(db: Session, q: str, limit: int = 8) -> list[dict]:
    needle = normalize_query(q)
    if len(needle) < 2:
        return []
    results: list[dict] = []
    seen: set[str] = set()
    for item in SOLAR_SYSTEM:
        hay = f"{item['id']} {item['display_name']}".lower()
        if needle in hay:
            results.append(item)
            seen.add(item["id"])
    rows = (
        db.query(DeepSkyObject)
        .filter(DeepSkyObject.search_text.contains(needle))
        .order_by(DeepSkyObject.beginner_prior.desc())
        .limit(limit)
        .all()
    )
    for obj in rows:
        if obj.id in seen:
            continue
        results.append(
            {
                "id": obj.id,
                "display_name": obj.common_name or obj.primary_name,
                "friendly_type": obj.friendly_type,
                "catalogue_ids": list(obj.catalogue_ids or []),
            }
        )
        seen.add(obj.id)
        if len(results) >= limit:
            break
    return results[:limit]
