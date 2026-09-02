from __future__ import annotations

import json
from pathlib import Path

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base
from app.importers.fetch_openngc import fetch_openngc
from app.importers.image_overlay import skip_image, update_overlay, wikipedia_portrait
from app.importers.refresh import run_refresh
from app.importers.sync import catalogue_digest, sync_from_files
from app.models.catalogue import DeepSkyObject

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
NAMED_NEBULA = (
    "NGC7000;HII;20:59:17.1;+44:31:44;Cyg;120.00;100.00;;;;;;;"
    ";;;;;;;;;;;;North America Nebula;;;note\n"
)
STAR = {
    "id": "star-vega",
    "primary_name": "Vega",
    "common_name": "Vega",
    "catalogue_ids": ["Vega"],
    "object_type": "star",
    "friendly_type": "Star",
    "ra": 279.23,
    "dec": 38.78,
    "magnitude": 0.03,
    "angular_size": None,
    "beginner_prior": 90,
    "metadata": {"source": "bsc"},
}
PORTRAIT = {
    "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/example.jpg/960px-example.jpg",
    "credit": "Test Credit",
    "license": "CC0",
    "page": "https://commons.wikimedia.org/wiki/File:example.jpg",
    "label": "Portrait",
}
EXTRA = {
    **PORTRAIT,
    "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/halpha.jpg/960px-halpha.jpg",
    "label": "H-alpha",
}


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _bundle(folder: Path, csv: str, images: dict | None = None) -> None:
    (folder / "NGC.csv").write_text(HEADER + csv)
    (folder / "addendum.csv").write_text(HEADER)
    (folder / "bright_stars.json").write_text(json.dumps([STAR]))
    (folder / "images.json").write_text(
        json.dumps(
            {
                "source": "test",
                "retrieved": "2026-09-02",
                "bodies": (
                    images if images is not None else {"m31": [PORTRAIT, EXTRA], "m45": [PORTRAIT]}
                ),
                "aliases": {},
            },
            indent=2,
        )
        + "\n"
    )


def test_sync_imports_prunes_and_skips_unchanged_digest(tmp_path: Path) -> None:
    _bundle(tmp_path, ANDROMEDA + PLEIADES)
    db = _session()
    first = sync_from_files(db, tmp_path)
    assert first.skipped is False
    assert first.imported == 2
    assert first.stars == 1
    andromeda = db.get(DeepSkyObject, "ngc-224")
    assert andromeda is not None
    assert andromeda.common_name == "Andromeda Galaxy"
    assert len(andromeda.images) == 2
    assert db.get(DeepSkyObject, "star-vega") is not None

    db.add(
        DeepSkyObject(
            id="ngc-9999",
            primary_name="NGC 9999",
            common_name=None,
            catalogue_ids=["NGC 9999"],
            object_type="galaxy",
            friendly_type="Galaxy",
            ra=1.0,
            dec=1.0,
            magnitude=12.0,
            angular_size=1.0,
            beginner_prior=10,
            search_text="ngc 9999",
            extra={"source": "openngc"},
        )
    )
    db.commit()
    assert db.get(DeepSkyObject, "ngc-9999") is not None

    _bundle(tmp_path, ANDROMEDA)
    second = sync_from_files(db, tmp_path)
    assert second.skipped is False
    assert second.pruned >= 2
    assert db.get(DeepSkyObject, "ngc-224") is not None
    assert db.get(DeepSkyObject, "mel-22") is None
    assert db.get(DeepSkyObject, "ngc-9999") is None
    assert db.get(DeepSkyObject, "star-vega") is not None

    andromeda = db.get(DeepSkyObject, "ngc-224")
    andromeda.magnitude = 99.0
    db.commit()
    third = sync_from_files(db, tmp_path)
    assert third.skipped is True
    assert db.get(DeepSkyObject, "ngc-224").magnitude == 99.0

    csv = (tmp_path / "NGC.csv").read_text().replace("3.44", "3.50")
    (tmp_path / "NGC.csv").write_text(csv)
    fourth = sync_from_files(db, tmp_path)
    assert fourth.skipped is False
    assert db.get(DeepSkyObject, "ngc-224").magnitude == 3.5
    db.close()


def test_digest_changes_when_images_change(tmp_path: Path) -> None:
    _bundle(tmp_path, ANDROMEDA)
    first = catalogue_digest(tmp_path)
    payload = json.loads((tmp_path / "images.json").read_text())
    payload["bodies"]["m31"].append(
        {**PORTRAIT, "label": "Wide field", "url": PORTRAIT["url"] + "2"}
    )
    (tmp_path / "images.json").write_text(json.dumps(payload))
    assert catalogue_digest(tmp_path) != first


def test_fetch_openngc_writes_csvs(tmp_path: Path) -> None:
    ngc = HEADER + ANDROMEDA
    addendum = HEADER + PLEIADES

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url).endswith("NGC.csv"):
            return httpx.Response(200, text=ngc)
        if str(request.url).endswith("addendum.csv"):
            return httpx.Response(200, text=addendum)
        return httpx.Response(404, text="missing")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    changed = fetch_openngc(
        tmp_path,
        ngc_url="https://example.test/NGC.csv",
        addendum_url="https://example.test/addendum.csv",
        client=client,
    )
    assert changed == {"NGC.csv": True, "addendum.csv": True}
    assert "Andromeda Galaxy" in (tmp_path / "NGC.csv").read_text()
    again = fetch_openngc(
        tmp_path,
        ngc_url="https://example.test/NGC.csv",
        addendum_url="https://example.test/addendum.csv",
        client=client,
    )
    assert again == {"NGC.csv": False, "addendum.csv": False}


def test_skip_constellation_maps() -> None:
    assert skip_image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/Andromeda_constellation_map.svg/960px.png",
        "Andromeda_constellation_map.svg",
    )
    assert not skip_image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Andromeda_Galaxy.jpg/960px-Andromeda_Galaxy.jpg",
        "Andromeda_Galaxy.jpg",
    )


def test_fill_missing_portraits_preserves_extras(tmp_path: Path) -> None:
    _bundle(tmp_path, ANDROMEDA + NAMED_NEBULA, images={"m31": [PORTRAIT, EXTRA]})

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "en.wikipedia.org" in url:
            return httpx.Response(
                200,
                json={
                    "query": {
                        "pages": [
                            {
                                "title": "North America Nebula",
                                "thumbnail": {
                                    "source": (
                                        "https://upload.wikimedia.org/wikipedia/commons/thumb/"
                                        "n/na/North_America_Nebula.jpg/960px-North_America_Nebula.jpg"
                                    )
                                },
                                "pageimage": "North_America_Nebula.jpg",
                            }
                        ]
                    }
                },
            )
        if "commons.wikimedia.org" in url:
            return httpx.Response(
                200,
                json={
                    "query": {
                        "pages": [
                            {
                                "imageinfo": [
                                    {
                                        "mime": "image/jpeg",
                                        "extmetadata": {
                                            "Artist": {"value": "<b>Test Photographer</b>"},
                                            "LicenseShortName": {"value": "CC BY 4.0"},
                                            "DescriptionUrl": {
                                                "value": "https://commons.wikimedia.org/wiki/File:North_America_Nebula.jpg"
                                            },
                                        },
                                    }
                                ]
                            }
                        ]
                    }
                },
            )
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = update_overlay(tmp_path, fill_missing=True, client=client, sleep_s=0)
    assert result["filled"] == 1
    assert result["aliases"] >= 1
    overlay = json.loads((tmp_path / "images.json").read_text())
    assert overlay["aliases"]["ngc-224"] == "m31"
    assert overlay["bodies"]["m31"][0]["label"] == "Portrait"
    assert overlay["bodies"]["m31"][1]["label"] == "H-alpha"
    north = overlay["bodies"]["ngc-7000"][0]
    assert "North_America_Nebula.jpg" in north["url"]
    assert north["credit"] == "Test Photographer"
    assert north["label"] == "Portrait"


def test_wikipedia_portrait_skips_svg() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "en.wikipedia.org" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "query": {
                        "pages": [
                            {
                                "thumbnail": {
                                    "source": "https://upload.wikimedia.org/wikipedia/commons/Cygnus_constellation_map.svg"
                                },
                                "pageimage": "Cygnus_constellation_map.svg",
                            }
                        ]
                    }
                },
            )
        return httpx.Response(200, json={"query": {"pages": []}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    assert wikipedia_portrait(["North America Nebula"], client=client) is None


def test_run_refresh_fetch_only_does_not_open_db(tmp_path: Path, monkeypatch) -> None:
    def boom(*_args, **_kwargs):
        raise AssertionError("database should not be opened")

    monkeypatch.setattr("app.importers.refresh.sync_from_files", boom)
    ngc = HEADER + ANDROMEDA

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=ngc)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    (tmp_path / "images.json").write_text(json.dumps({"bodies": {}, "aliases": {}}))
    result = run_refresh(
        tmp_path,
        fetch=True,
        fill_images=False,
        apply_db=False,
        client=client,
        sleep_s=0,
    )
    assert result["fetched"]["NGC.csv"] is True
    assert (tmp_path / "NGC.csv").exists()
