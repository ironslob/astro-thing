from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.constants import UK_LAT_MAX, UK_LAT_MIN, UK_LON_MAX, UK_LON_MIN
from app.models.place import UkPlace


def is_uk(lat: float, lon: float) -> bool:
    return UK_LAT_MIN <= lat <= UK_LAT_MAX and UK_LON_MIN <= lon <= UK_LON_MAX


def normalize_query(q: str) -> str:
    return " ".join(q.strip().lower().split())


def extract_outcode(q: str) -> str | None:
    compact = q.strip().upper().replace(" ", "")
    # Full postcode like BN32AB or outcode BN3 / EC1A
    if len(compact) >= 5 and compact[-3:].isalnum() and compact[-3] in "0123456789":
        # inward code is digit + 2 letters
        outward = compact[:-3]
        if 2 <= len(outward) <= 4:
            return outward
    if 2 <= len(compact) <= 4 and compact[:1].isalpha():
        return compact
    return None


def search_places(db: Session, q: str, limit: int = 8) -> list[UkPlace]:
    needle = normalize_query(q)
    if len(needle) < 2:
        return []
    outcode = extract_outcode(q)
    results: list[UkPlace] = []
    if outcode:
        matches = (
            db.query(UkPlace)
            .filter(UkPlace.place_type == "outcode", UkPlace.search_name == outcode.lower())
            .limit(limit)
            .all()
        )
        results.extend(matches)
    prefix = f"{needle}%"
    places = (
        db.query(UkPlace)
        .filter(UkPlace.place_type != "outcode", UkPlace.search_name.like(prefix))
        .order_by(UkPlace.population.desc())
        .limit(limit)
        .all()
    )
    seen = {r.id for r in results}
    for p in places:
        if p.id not in seen:
            results.append(p)
            seen.add(p.id)
    if len(results) < limit:
        contains = (
            db.query(UkPlace)
            .filter(UkPlace.place_type != "outcode", UkPlace.search_name.contains(needle))
            .order_by(UkPlace.population.desc())
            .limit(limit)
            .all()
        )
        for p in contains:
            if p.id not in seen:
                results.append(p)
                seen.add(p.id)
    return results[:limit]
