"""Download OpenNGC CSVs into the bundled catalogue directory.

Not used at request time. Safe to run with only httpx on the import path.
"""

from __future__ import annotations

import logging
from pathlib import Path

import httpx

from app.importers.paths import (
    DEFAULT_OPENNGC_ADDENDUM_URL,
    DEFAULT_OPENNGC_NGC_URL,
    REFRESH_USER_AGENT,
    resolve_catalogue_dir,
)

logger = logging.getLogger(__name__)


def fetch_openngc(
    folder: Path | None = None,
    *,
    ngc_url: str = DEFAULT_OPENNGC_NGC_URL,
    addendum_url: str = DEFAULT_OPENNGC_ADDENDUM_URL,
    client: httpx.Client | None = None,
) -> dict[str, bool]:
    dest = resolve_catalogue_dir(folder)
    dest.mkdir(parents=True, exist_ok=True)
    own_client = client is None
    http = client or httpx.Client(
        headers={"User-Agent": REFRESH_USER_AGENT, "Accept": "text/csv,text/plain,*/*"},
        timeout=60.0,
        follow_redirects=True,
    )
    changed: dict[str, bool] = {}
    try:
        for name, url in (("NGC.csv", ngc_url), ("addendum.csv", addendum_url)):
            changed[name] = _write_csv(http, url, dest / name)
    finally:
        if own_client:
            http.close()
    return changed


def _write_csv(client: httpx.Client, url: str, dest: Path) -> bool:
    response = client.get(url)
    response.raise_for_status()
    content = response.content
    _assert_openngc_csv(content, url)
    previous = dest.read_bytes() if dest.exists() else None
    if previous == content:
        logger.info("openngc_unchanged file=%s", dest.name)
        return False
    dest.write_bytes(content)
    logger.info("openngc_wrote file=%s bytes=%s", dest.name, len(content))
    return True


def _assert_openngc_csv(content: bytes, url: str) -> None:
    header = content.splitlines()[0] if content else b""
    text = header.decode("utf-8", errors="replace")
    if "Name" not in text or "RA" not in text:
        raise ValueError(f"OpenNGC download from {url} does not look like a catalogue CSV")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = fetch_openngc()
    print("fetched", result)
