"""Rebuild Messier aliases and fill missing Wikimedia portraits in images.json.

Does not overwrite curated extras (H-alpha, wide field, and so on). Wikipedia is
only contacted for overlay keys that have no images yet.
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Sequence
from datetime import date
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import httpx

from app.importers.openngc import _object_id, _open_reader, _pretty_name, _split_names
from app.importers.paths import REFRESH_USER_AGENT, resolve_catalogue_dir
from app.services.images import Image, normalize_images, reload_overlay

logger = logging.getLogger(__name__)

WIKI_API = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
_SKIP_IMAGE = re.compile(
    r"constellation|locator[_-]?map|\.svg(?:$|\?)|iau[_-]?(?:chart|map)",
    re.I,
)
_HTML_TAG = re.compile(r"<[^>]+>")
SOURCE_NOTE = (
    "Wikimedia Commons thumbnails for Messier objects, named nebulae/clusters, "
    "major planets and the Moon. Each catalogue body may have multiple images. "
    "Imported onto deep_sky_objects.images at seed time. Not fetched from Wikipedia "
    "at request time."
)


def update_overlay(
    folder: Path | None = None,
    *,
    fill_missing: bool = False,
    client: httpx.Client | None = None,
    sleep_s: float = 0.15,
) -> dict[str, int]:
    base = resolve_catalogue_dir(folder)
    path = base / "images.json"
    overlay = _load_overlay(path)
    bodies: dict[str, list[Image]] = overlay.setdefault("bodies", {})
    aliases: dict[str, str] = overlay.setdefault("aliases", {})

    alias_updates = 0
    for key, target in messier_aliases_from_csvs(base).items():
        if aliases.get(key) != target:
            aliases[key] = target
            alias_updates += 1

    filled = 0
    if fill_missing:
        own_client = client is None
        http = client or httpx.Client(
            headers={"User-Agent": REFRESH_USER_AGENT, "Accept": "application/json"},
            timeout=30.0,
            follow_redirects=True,
        )
        try:
            for key, titles in overlay_candidates(base):
                if normalize_images(bodies.get(key)):
                    continue
                portrait = wikipedia_portrait(titles, client=http)
                if sleep_s:
                    time.sleep(sleep_s)
                if not portrait:
                    continue
                bodies[key] = [portrait]
                filled += 1
                logger.info("filled_portrait key=%s url=%s", key, portrait["url"])
        finally:
            if own_client:
                http.close()

    if alias_updates or filled:
        overlay["source"] = overlay.get("source") or SOURCE_NOTE
        if filled:
            overlay["retrieved"] = date.today().isoformat()
        overlay["bodies"] = bodies
        overlay["aliases"] = aliases
        _write_overlay(path, overlay)
        reload_overlay()
    return {"aliases": alias_updates, "filled": filled}


def _add_title(titles: list[str], value: str) -> None:
    token = value.strip()
    if token and token not in titles:
        titles.append(token)


def messier_aliases_from_csvs(folder: Path) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for name in ("NGC.csv", "addendum.csv"):
        path = folder / name
        if not path.exists():
            continue
        for row in _open_reader(path):
            ident = _row_object_id(row)
            messier = _messier_key(row)
            if ident and messier and ident != messier:
                aliases[ident] = messier
    return aliases


def overlay_candidates(folder: Path) -> list[tuple[str, list[str]]]:
    """Messier objects and named DSOs: overlay key plus Wikipedia titles to try."""
    seen: set[str] = set()
    out: list[tuple[str, list[str]]] = []
    for name in ("NGC.csv", "addendum.csv"):
        path = folder / name
        if not path.exists():
            continue
        for row in _open_reader(path):
            ident = _row_object_id(row)
            if not ident:
                continue
            messier = _messier_key(row)
            common_names = _split_names(row.get("Common names") or row.get("Common_names"))
            if not messier and not common_names:
                continue
            key = messier or ident
            if key in seen:
                continue
            seen.add(key)
            titles: list[str] = []
            for item in common_names:
                _add_title(titles, item)
            if messier:
                number = _messier_number(row)
                if number is not None:
                    _add_title(titles, f"Messier {number}")
            _add_title(titles, _pretty_name(row.get("Name") or ""))
            if titles:
                out.append((key, titles))
    return out


def wikipedia_portrait(titles: Sequence[str], *, client: httpx.Client) -> Image | None:
    for title in titles:
        page = _wiki_pageimage(client, title)
        if not page:
            continue
        thumb, file_name = page
        if skip_image(thumb, file_name):
            continue
        meta = _commons_metadata(client, file_name) if file_name else {}
        mime = str(meta.get("mime") or "")
        if mime.startswith("image/svg") or skip_image(thumb, file_name):
            continue
        return {
            "url": thumb.split("?")[0],
            "credit": str(meta.get("credit") or "Wikimedia Commons"),
            "license": str(meta.get("license") or "see Wikimedia Commons"),
            "page": str(meta.get("page") or ""),
            "label": "Portrait",
        }
    return None


def skip_image(url: str, title: str = "") -> bool:
    blob = f"{url} {unquote(title)}"
    return not url or bool(_SKIP_IMAGE.search(blob))


def _row_object_id(row: dict) -> str | None:
    name = (row.get("Name") or row.get("name") or "").strip()
    if not name:
        return None
    return _object_id(name)


def _messier_number(row: dict) -> int | None:
    raw = (row.get("M") or "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _messier_key(row: dict) -> str | None:
    number = _messier_number(row)
    return f"m{number}" if number is not None else None


def _wiki_pageimage(client: httpx.Client, title: str) -> tuple[str, str] | None:
    response = client.get(
        WIKI_API,
        params={
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "redirects": "1",
            "prop": "pageimages",
            "piprop": "thumbnail|name",
            "pithumbsize": "960",
            "titles": title,
        },
    )
    response.raise_for_status()
    pages = (response.json().get("query") or {}).get("pages") or []
    if not pages:
        return None
    page = pages[0]
    if page.get("missing"):
        return None
    thumb = ((page.get("thumbnail") or {}).get("source") or "").strip()
    file_name = str(page.get("pageimage") or "").strip()
    if not thumb:
        return None
    return thumb, file_name


def _commons_metadata(client: httpx.Client, file_name: str) -> dict[str, str]:
    title = file_name if file_name.lower().startswith("file:") else f"File:{file_name}"
    response = client.get(
        COMMONS_API,
        params={
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "titles": title,
            "prop": "imageinfo",
            "iiprop": "url|mime|extmetadata",
        },
    )
    response.raise_for_status()
    pages = (response.json().get("query") or {}).get("pages") or []
    if not pages:
        return {}
    infos = pages[0].get("imageinfo") or []
    if not infos:
        return {}
    info = infos[0]
    ext = info.get("extmetadata") or {}
    artist = _plain_text((ext.get("Artist") or {}).get("value"))
    credit = _plain_text((ext.get("Credit") or {}).get("value"))
    license_name = _plain_text((ext.get("LicenseShortName") or {}).get("value"))
    description = (ext.get("DescriptionUrl") or {}).get("value") or ""
    page = str(description or f"https://commons.wikimedia.org/wiki/{title.replace(' ', '_')}")
    return {
        "credit": artist or credit or "Wikimedia Commons",
        "license": license_name or "see Wikimedia Commons",
        "page": page,
        "mime": str(info.get("mime") or ""),
    }


def _plain_text(value: Any) -> str:
    if not value:
        return ""
    return unescape(_HTML_TAG.sub("", str(value))).strip()


def _load_overlay(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "source": SOURCE_NOTE,
            "retrieved": date.today().isoformat(),
            "bodies": {},
            "aliases": {},
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {
            "source": SOURCE_NOTE,
            "retrieved": date.today().isoformat(),
            "bodies": {},
            "aliases": {},
        }
    data["bodies"] = dict(data.get("bodies") or data.get("images") or {})
    data["aliases"] = dict(data.get("aliases") or {})
    return data


def _write_overlay(path: Path, overlay: dict[str, Any]) -> None:
    path.write_text(json.dumps(overlay, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
