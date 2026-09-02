from __future__ import annotations

from pathlib import Path

DATA_CANDIDATES = [
    Path("/data/catalogue"),
    Path(__file__).resolve().parents[3] / "data" / "catalogue",
]

BUNDLE_FILES = ("NGC.csv", "addendum.csv", "bright_stars.json", "images.json")
CATALOGUE_META_ID = "bundle"
REFRESH_USER_AGENT = "AstroWindow/1.0 (https://github.com/ironslob/astro-thing; catalogue refresh)"
DEFAULT_OPENNGC_NGC_URL = (
    "https://raw.githubusercontent.com/mattiaverga/OpenNGC/master/database_files/NGC.csv"
)
DEFAULT_OPENNGC_ADDENDUM_URL = (
    "https://raw.githubusercontent.com/mattiaverga/OpenNGC/master/database_files/addendum.csv"
)


def repo_catalogue_dir() -> Path:
    """Catalogue files in this repo (writable on the host / in CI)."""
    return Path(__file__).resolve().parents[3] / "data" / "catalogue"


def catalogue_dir() -> Path:
    for path in DATA_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("catalogue data directory not found")


def resolve_catalogue_dir(folder: Path | None = None) -> Path:
    if folder is not None:
        return folder
    repo = repo_catalogue_dir()
    if repo.exists():
        return repo
    return catalogue_dir()
