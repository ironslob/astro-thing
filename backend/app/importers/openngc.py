"""Optional OpenNGC CSV importer (offline). Not used at request time.

Place `NGC.csv` from https://github.com/mattiaverga/OpenNGC into
`data/catalogue/NGC.csv` then run:

    python -m app.importers.openngc
"""

from __future__ import annotations

import csv
from pathlib import Path

from app.core.db import SessionLocal
from app.importers.catalogue import import_catalogue
from app.models.catalogue import DeepSkyObject

TYPE_MAP = {
    "*": ("star", "Star"),
    "**": ("star", "Double star"),
    "G": ("galaxy", "Galaxy"),
    "GPair": ("galaxy", "Galaxy pair"),
    "GTrpl": ("galaxy", "Galaxy triplet"),
    "GGroup": ("galaxy", "Galaxy group"),
    "PN": ("planetary_nebula", "Planetary nebula"),
    "HII": ("nebula", "Nebula"),
    "EmN": ("nebula", "Nebula"),
    "Neb": ("nebula", "Nebula"),
    "RfN": ("nebula", "Reflection nebula"),
    "OCl": ("open_cluster", "Open cluster"),
    "GCl": ("globular_cluster", "Globular cluster"),
    "Cl+N": ("open_cluster", "Cluster with nebula"),
    "Ast": ("asterism", "Asterism"),
}


def _ra_to_deg(value: str) -> float | None:
    parts = value.strip().split(":")
    if len(parts) < 2:
        return None
    h = float(parts[0])
    m = float(parts[1])
    s = float(parts[2]) if len(parts) > 2 else 0.0
    return (abs(h) + m / 60.0 + s / 3600.0) * 15.0 * (1 if h >= 0 else -1)


def _dec_to_deg(value: str) -> float | None:
    sign = -1 if value.strip().startswith("-") else 1
    parts = value.replace("+", "").replace("-", "").split(":")
    if len(parts) < 2:
        return None
    d = float(parts[0])
    m = float(parts[1])
    s = float(parts[2]) if len(parts) > 2 else 0.0
    return sign * (d + m / 60.0 + s / 3600.0)


def import_openngc(path: Path) -> int:
    db = SessionLocal()
    n = 0
    try:
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                name = (row.get("Name") or row.get("name") or "").strip()
                if not name:
                    continue
                ra_s = row.get("RA") or row.get("ra") or ""
                dec_s = row.get("Dec") or row.get("dec") or ""
                ra = _ra_to_deg(ra_s)
                dec = _dec_to_deg(dec_s)
                if ra is None or dec is None:
                    continue
                otype, friendly = TYPE_MAP.get(
                    (row.get("Type") or "G").strip(), ("other", "Object")
                )
                ident = name.lower().replace(" ", "-")
                common = (row.get("Common names") or row.get("Common_names") or "").split(",")[
                    0
                ].strip() or None
                existing = db.get(DeepSkyObject, ident)
                payload = dict(
                    primary_name=name,
                    common_name=common,
                    catalogue_ids=[name],
                    object_type=otype,
                    friendly_type=friendly,
                    ra=ra,
                    dec=dec,
                    magnitude=_float(row.get("V-Mag") or row.get("B-Mag")),
                    angular_size=_float(row.get("MajAx")),
                    beginner_prior=40,
                    extra={"source": "openngc"},
                )
                if existing is None:
                    db.add(DeepSkyObject(id=ident, **payload))
                else:
                    for k, v in payload.items():
                        setattr(existing, k, v)
                n += 1
                if n % 500 == 0:
                    db.commit()
        db.commit()
    finally:
        db.close()
    return n


def _float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


if __name__ == "__main__":
    csv_path = Path("/data/catalogue/NGC.csv")
    if not csv_path.exists():
        csv_path = Path(__file__).resolve().parents[3] / "data" / "catalogue" / "NGC.csv"
    if csv_path.exists():
        print("imported", import_openngc(csv_path))
    else:
        print("NGC.csv not present; loading curated seed instead")
        db = SessionLocal()
        try:
            print("curated", import_catalogue(db))
        finally:
            db.close()
