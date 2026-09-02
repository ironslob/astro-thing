from __future__ import annotations

from app.services.portraits import portrait_for


def test_andromeda_resolves_by_object_id_and_messier() -> None:
    by_id = portrait_for(object_id="ngc-224", catalogue_ids=["NGC 224"])
    by_messier = portrait_for(object_id="something-else", catalogue_ids=["M31"])
    assert by_id is not None
    assert by_messier is not None
    assert by_id["url"] == by_messier["url"]
    assert "upload.wikimedia.org" in by_id["url"]
    assert by_id["credit"]
    assert by_id["license"]
    assert by_id["page"].startswith("https://commons.wikimedia.org/")


def test_planets_and_moon_have_portraits() -> None:
    jupiter = portrait_for(object_id="jupiter", catalogue_ids=["Jupiter"])
    moon = portrait_for(object_id="moon", catalogue_ids=["Moon"])
    assert jupiter is not None
    assert moon is not None
    assert jupiter["url"] != moon["url"]


def test_unknown_object_has_no_portrait() -> None:
    assert portrait_for(object_id="ngc-9999", catalogue_ids=["NGC 9999"]) is None
