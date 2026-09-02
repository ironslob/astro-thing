from __future__ import annotations

import logging

from app.core.db import SessionLocal
from app.domain.constants import CATALOGUE_RESEED_BELOW
from app.importers.sync import sync_from_files
from app.models.catalogue import DeepSkyObject

logger = logging.getLogger(__name__)


def seed_if_needed() -> None:
    db = SessionLocal()
    try:
        force = db.query(DeepSkyObject).count() < CATALOGUE_RESEED_BELOW
        result = sync_from_files(db, force=force)
        if result.skipped:
            logger.info("catalogue_up_to_date digest=%s", result.digest)
        else:
            logger.info(
                "imported_catalogue n=%s bright_stars=%s pruned=%s images=%s",
                result.imported,
                result.stars,
                result.pruned,
                result.images,
            )
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_if_needed()
    print("seed complete")
