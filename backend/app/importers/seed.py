from __future__ import annotations

import logging

from sqlalchemy import delete

from app.core.db import SessionLocal
from app.domain.constants import CATALOGUE_RESEED_BELOW
from app.importers.catalogue import import_bright_stars
from app.importers.openngc import import_openngc
from app.models.catalogue import DeepSkyObject

logger = logging.getLogger(__name__)


def seed_if_needed() -> None:
    db = SessionLocal()
    try:
        dso_count = db.query(DeepSkyObject).count()
        if dso_count < CATALOGUE_RESEED_BELOW:
            if dso_count:
                db.execute(delete(DeepSkyObject))
                db.commit()
            n = import_openngc(db)
            stars = import_bright_stars(db)
            logger.info("imported_catalogue n=%s bright_stars=%s", n, stars)
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_if_needed()
    print("seed complete")
