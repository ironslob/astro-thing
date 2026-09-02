"""Static field-guide portraits for recommended targets.

Images are Wikimedia Commons thumbnails recorded in `data/catalogue/portraits.json`.
Nothing is fetched from Wikipedia or Commons at request time.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from functools import lru_cache
from typing import Any

from app.importers.catalogue import catalogue_dir

_CAT_PREFIX = re.compile(r"^([A-Za-z]+)0*(\d+[A-Za-z]?)$")
_MESSIER = re.compile(r"^m0*(\d+)$")


@lru_cache(maxsize=1)
def _catalogue() -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    try:
        path = catalogue_dir() / "portraits.json"
    except FileNotFoundError:
        return {}, {}
    if not path.exists():
        return {}, {}
    data = json.loads(path.read_text(encoding="utf-8"))
    images = data.get("images") or {}
    aliases = data.get("aliases") or {}
    return images, aliases


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


def portrait_for(
    *,
    object_id: str,
    catalogue_ids: Sequence[str] | None = None,
) -> dict[str, str] | None:
    images, aliases = _catalogue()
    if not images:
        return None
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in (object_id, *(catalogue_ids or ())):
        for key in _variants(raw):
            if key not in seen:
                seen.add(key)
                ordered.append(key)
    for key in ordered:
        canon = aliases.get(key, key)
        hit: dict[str, Any] | None = images.get(canon) or images.get(key)
        url = (hit or {}).get("url")
        if hit and url:
            return {
                "url": url,
                "credit": hit.get("credit") or "Wikimedia Commons",
                "license": hit.get("license") or "see Wikimedia Commons",
                "page": hit.get("page") or "",
            }
    return None
