"""OpenNGC CSV importer (offline). Not used at request time.

Expects `NGC.csv` and optionally `addendum.csv` from
https://github.com/mattiaverga/OpenNGC (database_files/).
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.importers.paths import catalogue_dir
from app.importers.search_text import build_search_text
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
    "DrkN": ("nebula", "Dark nebula"),
    "OCl": ("open_cluster", "Open cluster"),
    "GCl": ("globular_cluster", "Globular cluster"),
    "Cl+N": ("open_cluster", "Cluster with nebula"),
    "Ast": ("asterism", "Asterism"),
}

_CATALOGUE_PREFIX = re.compile(r"^([A-Za-z]+)0*(\d+[A-Za-z]?)$")
_SKIP_IDENTIFIER_PREFIXES = (
    "2MAS",
    "IRAS",
    "MCG",
    "PGC",
    "UGC",
    "SDSS",
    "WISE",
    "NVSS",
    "HIPASS",
    "6dF",
)


def _object_id(name: str) -> str:
    raw = name.strip()
    match = _CATALOGUE_PREFIX.match(raw.replace(" ", ""))
    if match:
        return f"{match.group(1).lower()}-{match.group(2).lower()}"
    return raw.lower().replace(" ", "-")


def _pretty_name(name: str) -> str:
    match = _CATALOGUE_PREFIX.match(name.strip().replace(" ", ""))
    if match:
        prefix = match.group(1)
        if prefix.lower() == "mel":
            prefix = "Mel"
        else:
            prefix = prefix.upper()
        return f"{prefix} {match.group(2)}"
    return name.strip()


def _ra_to_deg(value: str) -> float | None:
    parts = value.strip().split(":")
    if len(parts) < 2:
        return None
    h = float(parts[0])
    m = float(parts[1])
    s = float(parts[2]) if len(parts) > 2 else 0.0
    return (abs(h) + m / 60.0 + s / 3600.0) * 15.0 * (1 if h >= 0 else -1)


def _dec_to_deg(value: str) -> float | None:
    text = value.strip()
    if not text:
        return None
    sign = -1 if text.startswith("-") else 1
    parts = text.replace("+", "").replace("-", "").split(":")
    if len(parts) < 2:
        return None
    d = float(parts[0])
    m = float(parts[1])
    s = float(parts[2]) if len(parts) > 2 else 0.0
    return sign * (d + m / 60.0 + s / 3600.0)


def _float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _split_names(value: str | None) -> list[str]:
    if not value:
        return []
    out: list[str] = []
    for part in value.split(","):
        token = part.strip()
        if token:
            out.append(token)
    return out


def _catalogue_ids(row: dict, pretty: str, common_names: list[str]) -> list[str]:
    ids: list[str] = [pretty]
    messier = (row.get("M") or "").strip()
    if messier:
        try:
            ids.append(f"M{int(messier)}")
        except ValueError:
            ids.append(f"M{messier}")
    for col, label in (("NGC", "NGC"), ("IC", "IC")):
        raw = (row.get(col) or "").strip()
        if not raw:
            continue
        for part in raw.split(","):
            token = part.strip().lstrip("0") or "0"
            if token and f"{label} {token}" not in ids:
                ids.append(f"{label} {token}")
    for ident in _split_names(row.get("Identifiers")):
        if ident.startswith(_SKIP_IDENTIFIER_PREFIXES):
            continue
        if ident not in ids:
            ids.append(ident)
    for name in common_names:
        if name not in ids:
            ids.append(name)
    return ids


def _beginner_prior(
    *,
    object_type: str,
    magnitude: float | None,
    angular_size: float | None,
    common_name: str | None,
    catalogue_ids: list[str],
) -> int:
    prior = 35
    if any(i.startswith("M") and i[1:].isdigit() for i in catalogue_ids):
        prior += 30
    if common_name:
        prior += 15
    if object_type in {"nebula", "open_cluster", "globular_cluster", "planetary_nebula"}:
        prior += 8
    elif object_type == "galaxy":
        prior += 4
    elif object_type == "star":
        prior += 6
    if magnitude is not None:
        if magnitude <= 4:
            prior += 20
        elif magnitude <= 6:
            prior += 12
        elif magnitude <= 8:
            prior += 6
        elif magnitude > 12:
            prior -= 15
    if angular_size is not None:
        if angular_size >= 30:
            prior += 10
        elif angular_size >= 10:
            prior += 5
    return max(0, min(100, prior))


def _open_reader(path: Path) -> csv.DictReader:
    text = path.read_text(encoding="utf-8")
    first = text.splitlines()[0] if text else ""
    delim = ";" if first.count(";") > first.count(",") else ","
    return csv.DictReader(io.StringIO(text), delimiter=delim)


def _upsert_openngc_row(db: Session, row: dict) -> str | None:
    name = (row.get("Name") or row.get("name") or "").strip()
    if not name:
        return None
    ra = _ra_to_deg(row.get("RA") or row.get("ra") or "")
    dec = _dec_to_deg(row.get("Dec") or row.get("dec") or "")
    if ra is None or dec is None:
        return None
    raw_type = (row.get("Type") or "G").strip()
    otype, friendly = TYPE_MAP.get(raw_type, ("other", "Object"))
    pretty = _pretty_name(name)
    common_names = _split_names(row.get("Common names") or row.get("Common_names"))
    common = common_names[0] if common_names else None
    ids = _catalogue_ids(row, pretty, common_names)
    magnitude = _float(row.get("V-Mag") or row.get("B-Mag"))
    angular_size = _float(row.get("MajAx"))
    ident = _object_id(name)
    payload = dict(
        primary_name=pretty,
        common_name=common,
        catalogue_ids=ids,
        object_type=otype,
        friendly_type=friendly,
        ra=ra,
        dec=dec,
        magnitude=magnitude,
        angular_size=angular_size,
        beginner_prior=_beginner_prior(
            object_type=otype,
            magnitude=magnitude,
            angular_size=angular_size,
            common_name=common,
            catalogue_ids=ids,
        ),
        search_text=build_search_text(pretty, common, ids),
        extra={"source": "openngc", "openngc_name": name, "const": row.get("Const")},
    )
    existing = db.get(DeepSkyObject, ident)
    if existing is None:
        db.add(DeepSkyObject(id=ident, **payload))
    else:
        for k, v in payload.items():
            setattr(existing, k, v)
    return ident


def import_openngc_ids(db: Session, paths: list[Path]) -> set[str]:
    keep: set[str] = set()
    n = 0
    for path in paths:
        if not path.exists():
            continue
        reader = _open_reader(path)
        for row in reader:
            ident = _upsert_openngc_row(db, row)
            if ident:
                keep.add(ident)
                n += 1
            if n and n % 500 == 0:
                db.commit()
    db.commit()
    return keep


def import_openngc_files(db: Session, paths: list[Path], *, replace: bool = False) -> int:
    if replace:
        db.execute(delete(DeepSkyObject))
        db.commit()
    return len(import_openngc_ids(db, paths))


def import_openngc(db: Session, folder: Path | None = None) -> int:
    base = folder or catalogue_dir()
    paths = [base / "NGC.csv", base / "addendum.csv"]
    return import_openngc_files(db, paths, replace=False)


if __name__ == "__main__":
    from app.core.db import SessionLocal
    from app.importers.catalogue import import_bright_stars

    db = SessionLocal()
    try:
        print("imported", import_openngc(db), "bright_stars", import_bright_stars(db))
    finally:
        db.close()
