from __future__ import annotations

from app.services.images import images_for, normalize_images


def test_andromeda_resolves_by_object_id_and_messier() -> None:
    by_id = images_for(object_id="ngc-224", catalogue_ids=["NGC 224"])
    by_messier = images_for(object_id="something-else", catalogue_ids=["M31"])
    assert by_id
    assert by_messier
    assert by_id[0]["url"] == by_messier[0]["url"]
    assert "upload.wikimedia.org" in by_id[0]["url"]
    assert by_id[0]["credit"]
    assert len(by_id) >= 2
    labels = {item.get("label") for item in by_id}
    assert "Portrait" in labels
    assert "H-alpha" in labels


def test_planets_and_moon_have_images() -> None:
    jupiter = images_for(object_id="jupiter", catalogue_ids=["Jupiter"])
    moon = images_for(object_id="moon", catalogue_ids=["Moon"])
    assert jupiter
    assert moon
    assert jupiter[0]["url"] != moon[0]["url"]


def test_unknown_object_has_no_images() -> None:
    assert images_for(object_id="ngc-9999", catalogue_ids=["NGC 9999"]) == []


def test_normalize_accepts_single_or_list() -> None:
    one = {"url": "https://example.test/a.jpg", "credit": "A", "license": "CC0", "page": ""}
    assert len(normalize_images(one)) == 1
    assert len(normalize_images([one, one])) == 1
    assert normalize_images(None) == []
