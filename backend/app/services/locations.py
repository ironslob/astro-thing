from __future__ import annotations

import re

from app.domain.constants import UK_LAT_MAX, UK_LAT_MIN, UK_LON_MAX, UK_LON_MIN

_OUTCODE_RE = re.compile(r"^[A-Z]{1,2}\d[A-Z\d]?$")


def is_uk(lat: float, lon: float) -> bool:
    return UK_LAT_MIN <= lat <= UK_LAT_MAX and UK_LON_MIN <= lon <= UK_LON_MAX


def normalize_query(q: str) -> str:
    return " ".join(q.strip().lower().split())


def classify_query(q: str) -> str:
    """Return 'postcode' for strict UK postcode/outcode shapes, otherwise 'place'."""
    compact = re.sub(r"\s+", "", q.strip().upper())
    if len(compact) >= 5:
        inward = compact[-3:]
        if inward[0].isdigit() and inward[1:].isalpha() and len(inward) == 3:
            outward = compact[:-3]
            if _OUTCODE_RE.match(outward):
                return "postcode"
    if _OUTCODE_RE.match(compact):
        return "postcode"
    return "place"
