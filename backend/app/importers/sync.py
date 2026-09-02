"""Apply bundled catalogue files to the database when their digest changes."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.importers.catalogue import import_json_objects
from app.importers.openngc import import_openngc_ids
from app.importers.paths import BUNDLE_FILES, CATALOGUE_META_ID, resolve_catalogue_dir
from app.models.catalogue import CatalogueMeta, DeepSkyObject
from app.services.images import apply_catalogue_images, reload_overlay

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SyncResult:
    skipped: bool
    digest: str
    imported: int = 0
    stars: int = 0
    pruned: int = 0
    images: int = 0


def catalogue_digest(folder: Path) -> str:
    digest = hashlib.sha256()
    for name in BUNDLE_FILES:
        path = folder / name
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        if path.exists():
            digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def stored_digest(db: Session) -> str | None:
    row = db.get(CatalogueMeta, CATALOGUE_META_ID)
    return row.digest if row else None


def sync_from_files(
    db: Session,
    folder: Path | None = None,
    *,
    force: bool = False,
) -> SyncResult:
    base = resolve_catalogue_dir(folder)
    digest = catalogue_digest(base)
    if not force and stored_digest(db) == digest:
        logger.info("catalogue_bundle_unchanged digest=%s", digest)
        return SyncResult(skipped=True, digest=digest)

    openngc_ids = import_openngc_ids(db, [base / "NGC.csv", base / "addendum.csv"])
    if not openngc_ids:
        raise RuntimeError(f"OpenNGC import produced no objects from {base}")

    star_path = base / "bright_stars.json"
    star_ids = import_json_objects(db, star_path) if star_path.exists() else set()
    keep = openngc_ids | star_ids

    stale_ids = [ident for (ident,) in db.query(DeepSkyObject.id) if ident not in keep]
    pruned = 0
    if stale_ids:
        pruned = (
            db.query(DeepSkyObject)
            .filter(DeepSkyObject.id.in_(stale_ids))
            .delete(synchronize_session=False)
        )
        db.commit()

    images = apply_catalogue_images(db, base)
    reload_overlay()
    _store_digest(db, digest)
    logger.info(
        "synced_catalogue imported=%s stars=%s pruned=%s images=%s digest=%s",
        len(openngc_ids),
        len(star_ids),
        pruned,
        images,
        digest,
    )
    return SyncResult(
        skipped=False,
        digest=digest,
        imported=len(openngc_ids),
        stars=len(star_ids),
        pruned=pruned,
        images=images,
    )


def _store_digest(db: Session, digest: str) -> None:
    now = datetime.now(UTC)
    row = db.get(CatalogueMeta, CATALOGUE_META_ID)
    if row is None:
        db.add(CatalogueMeta(id=CATALOGUE_META_ID, digest=digest, updated_at=now))
    else:
        row.digest = digest
        row.updated_at = now
    db.commit()
