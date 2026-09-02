from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base
from app.importers.openngc import _beginner_prior, _object_id, import_openngc_files
from app.importers.search_text import build_search_text
from app.models.catalogue import DeepSkyObject
from app.services.catalogue import search_catalogue

HEADER = (
    "Name;Type;RA;Dec;Const;MajAx;MinAx;PosAng;B-Mag;V-Mag;J-Mag;H-Mag;K-Mag;SurfBr;"
    "Hubble;Pax;Pm-RA;Pm-Dec;RadVel;Redshift;Cstar U-Mag;Cstar B-Mag;Cstar V-Mag;"
    "M;NGC;IC;Cstar Names;Identifiers;Common names;NED notes;OpenNGC notes;Sources\n"
)
ANDROMEDA = (
    "NGC0224;G;00:42:44.35;+41:16:08.6;And;177.83;69.66;35;4.29;3.44;2.09;1.28;0.98;"
    "23.63;Sb;6.0000;;;-300;-0.001000;;;;031;;;;"
    "2MASX J00424433+4116074,IRAS 00400+4059;Andromeda Galaxy;;;note\n"
)
PLEIADES = (
    "Mel022;OCl;03:47:28.6;+24:06:19;Tau;150.00;150.00;90;;1.20;;;;;;7.3640;19.997;"
    "-45.548;7;0.000022;;;;045;;;;MWSC 0305;Pleiades;;;note\n"
)


def test_object_id_normalises_ngc() -> None:
    assert _object_id("NGC0224") == "ngc-224"
    assert _object_id("Mel022") == "mel-22"


def test_search_text_includes_common_name_and_ids() -> None:
    text = build_search_text("NGC 224", "Andromeda Galaxy", ["M31", "NGC 224"])
    assert "andromeda" in text
    assert "m31" in text


def test_beginner_prior_boosts_messier() -> None:
    prior = _beginner_prior(
        object_type="galaxy",
        magnitude=3.4,
        angular_size=190,
        common_name="Andromeda Galaxy",
        catalogue_ids=["NGC 224", "M31"],
    )
    assert prior >= 55


def test_import_tiny_csv_and_search(tmp_path: Path) -> None:
    csv_path = tmp_path / "fixture.csv"
    csv_path.write_text(HEADER + ANDROMEDA + PLEIADES)
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    n = import_openngc_files(db, [csv_path])
    assert n == 2
    andromeda = db.get(DeepSkyObject, "ngc-224")
    assert andromeda is not None
    assert andromeda.common_name == "Andromeda Galaxy"
    assert "M31" in andromeda.catalogue_ids
    hits = search_catalogue(db, "Andromeda")
    andromeda = next(h for h in hits if h["id"] == "ngc-224")
    assert andromeda["image"] is not None
    assert "upload.wikimedia.org" in andromeda["image"]["url"]
    pleiades = search_catalogue(db, "Pleiades")
    assert any(h["id"] == "mel-22" for h in pleiades)
    planets = search_catalogue(db, "Venus")
    venus = next(h for h in planets if h["id"] == "venus")
    assert venus["image"] is not None
    db.close()
