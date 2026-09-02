"""Catalogue image overlay: Wikimedia portraits, one or more per body.

`data/catalogue/images.json` is merged onto `DeepSkyObject.images` at seed time.
Solar-system bodies are not rows in that table, so they still resolve from the
same overlay at request time. Nothing is fetched from Wikipedia on a request.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from functools import lru_cache
from typing import Any

from sqlalchemy.orm import Session

from app.importers.catalogue import catalogue_dir
from app.models.catalogue import DeepSkyObject

_CAT_PREFIX = re.compile(r"^([A-Za-z]+)0*(\d+[A-Za-z]?)$")
_MESSIER = re.compile(r"^m0*(\d+)$")

Image = dict[str, str]


@lru_cache(maxsize=1)
def _overlay() -> tuple[dict[str, list[Image]], dict[str, str]]:
    try:
        path = catalogue_dir() / "images.json"
    except FileNotFoundError:
        return {}, {}
    if not path.exists():
        # Older checkouts stored a single-image map under portraits.json.
        legacy = catalogue_dir() / "portraits.json"
        if not legacy.exists():
            return {}, {}
        path = legacy
    data = json.loads(path.read_text(encoding="utf-8"))
    bodies = data.get("bodies") or data.get("images") or {}
    aliases = data.get("aliases") or {}
    normalised: dict[str, list[Image]] = {}
    for key, raw in bodies.items():
        images = normalize_images(raw)
        if images:
            normalised[key] = images
    return normalised, aliases


def normalize_images(raw: Any) -> list[Image]:
    if not raw:
        return []
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    out: list[Image] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").split("?")[0]
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(
            {
                "url": url,
                "credit": str(item.get("credit") or "Wikimedia Commons"),
                "license": str(item.get("license") or "see Wikimedia Commons"),
                "page": str(item.get("page") or ""),
                "label": str(item.get("label") or ""),
            }
        )
    return out


def _variants(raw: str) -> list[str]:
    text = raw.strip()
    if not text:
        return []
    lower = text.lower()
    compact = re.sub(r"[^a-z0-9]+", "", lower)
    keys = [lower, compact]
    match = _CAT_PREFIX.match(text.replace(" ", "")) or _CAT_PREFIX.match(compact)
    if match:
        keys.append(f"{match.group(1).lower()}-{match.group(2).lower()}")
    messier = _MESSIER.fullmatch(compact)
    if messier:
        keys.append(f"m{int(messier.group(1))}")
    return keys


def images_for(
    *,
    object_id: str,
    catalogue_ids: Sequence[str] | None = None,
) -> list[Image]:
    """Images from the bundled overlay (used at seed, and for planets/Moon)."""
    bodies, aliases = _overlay()
    if not bodies:
        return []
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in (object_id, *(catalogue_ids or ())):
        for key in _variants(raw):
            if key not in seen:
                seen.add(key)
                ordered.append(key)
    for key in ordered:
        canon = aliases.get(key, key)
        hit = bodies.get(canon) or bodies.get(key)
        if hit:
            return hit
    return []


def apply_catalogue_images(db: Session) -> int:
    """Copy overlay images onto matching deep-sky rows."""
    updated = 0
    for obj in db.query(DeepSkyObject).yield_per(500):
        found = images_for(object_id=obj.id, catalogue_ids=obj.catalogue_ids or [])
        current = normalize_images(obj.images)
        if found and found != current:
            obj.images = found
            updated += 1
    if updated:
        db.commit()
    return updated
