"""Full catalogue refresh: fetch OpenNGC, update related overlay data, apply to the DB.

OpenNGC changes a few times a year (corrections and the occasional IC/addendum
object; the Messier list is closed). Run this on the host or in CI — Docker
mounts `data/` read-only, so fetches must write the repo files, not the container.

Examples:
    python -m app.importers.refresh
    python -m app.importers.refresh --no-fill-images
    python -m app.importers.refresh --no-fetch --no-fill-images
    python -m app.importers.refresh --no-apply-db --no-fill-images
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import httpx

from app.importers.fetch_openngc import fetch_openngc
from app.importers.image_overlay import update_overlay
from app.importers.paths import resolve_catalogue_dir
from app.importers.sync import SyncResult, sync_from_files


def run_refresh(
    folder: Path | None = None,
    *,
    fetch: bool = True,
    fill_images: bool = True,
    apply_db: bool = True,
    force_db: bool = False,
    client: httpx.Client | None = None,
    sleep_s: float = 0.15,
) -> dict[str, object]:
    base = resolve_catalogue_dir(folder)
    fetched: dict[str, bool] = {}
    overlay = {"aliases": 0, "filled": 0}
    synced: SyncResult | None = None

    if fetch:
        from app.core.config import settings

        fetched = fetch_openngc(
            base,
            ngc_url=settings.openngc_ngc_url,
            addendum_url=settings.openngc_addendum_url,
            client=client,
        )
    if fetch or fill_images:
        overlay = update_overlay(
            base,
            fill_missing=fill_images,
            client=client,
            sleep_s=sleep_s if fill_images else 0.0,
        )
    if apply_db:
        from app.core.db import SessionLocal

        db = SessionLocal()
        try:
            synced = sync_from_files(db, base, force=force_db)
        finally:
            db.close()
    return {"folder": str(base), "fetched": fetched, "overlay": overlay, "sync": synced}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Refresh bundled OpenNGC files, image aliases/portraits, and the database."
    )
    parser.add_argument(
        "--folder",
        type=Path,
        default=None,
        help="Catalogue directory (default: repo data/catalogue)",
    )
    parser.add_argument("--no-fetch", action="store_true", help="Do not download OpenNGC CSVs")
    parser.add_argument(
        "--no-fill-images", action="store_true", help="Do not query Wikipedia for missing portraits"
    )
    parser.add_argument(
        "--no-apply-db", action="store_true", help="Do not import the bundle into the database"
    )
    parser.add_argument(
        "--force-db", action="store_true", help="Re-import even if the bundle digest is unchanged"
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = run_refresh(
        args.folder,
        fetch=not args.no_fetch,
        fill_images=not args.no_fill_images,
        apply_db=not args.no_apply_db,
        force_db=args.force_db,
    )
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
