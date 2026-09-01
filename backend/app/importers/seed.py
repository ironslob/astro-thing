from __future__ import annotations

import logging

from app.core.db import SessionLocal
from app.importers.catalogue import import_catalogue
from app.importers.places import import_places
from app.models.catalogue import DeepSkyObject
from app.models.place import UkPlace

logger = logging.getLogger(__name__)


def seed_if_needed() -> None:
    db = SessionLocal()
    try:
        dso_count = db.query(DeepSkyObject).count()
        if dso_count == 0:
            n = import_catalogue(db)
            logger.info("imported_catalogue n=%s", n)
        place_count = db.query(UkPlace).count()
        if place_count == 0:
            n = import_places(db)
            logger.info("imported_places n=%s", n)
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_if_needed()
    print("seed complete")
