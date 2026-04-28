"""Integration test: every committed STAC document must pass JSON Schema
validation against the official STAC 1.1.0 spec *and* every extension it
declares.

`pystac.Catalog.validate_all()` runs during `generate()` (src/generate.py),
but nothing asserts the *committed* `stac/` tree — what we actually ship —
still validates today. A drift between schema versions, a stale committed
file, or a hand-edit that omits a required field would slip through every
existing test (test_stac_drift.py compares JSON equality, test_stac_check.py
only flags best-practice warnings, test_stac_browse.py only checks pystac-
client can navigate the catalog).

This test is the contract: every JSON file under `stac/` validates against
the full set of schemas pystac claims it should, including every URI listed
in `stac_extensions`. If a generic STAC client (pystac, rust-stac, go-stac,
QGIS) refuses to read a file, this test should already have caught it.
"""

from __future__ import annotations

import pathlib

import pystac
import pystac.errors
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMITTED_STAC = REPO_ROOT / "stac"

_STAC_FILES = sorted(COMMITTED_STAC.rglob("*.json"))


@pytest.mark.integration
@pytest.mark.parametrize(
    "json_path",
    _STAC_FILES,
    ids=[str(p.relative_to(COMMITTED_STAC)) for p in _STAC_FILES],
)
def test_committed_stac_validates_against_schemas(json_path: pathlib.Path) -> None:
    """Each STAC file passes pystac's JSON Schema validation, including
    every schema URI it declares in `stac_extensions`."""
    obj = pystac.read_file(str(json_path))
    try:
        validated = obj.validate()
    except pystac.errors.STACValidationError as e:
        pytest.fail(f"{json_path.relative_to(REPO_ROOT)} failed schema validation: {e}")

    # Core spec must always be among the validated schemas.
    assert validated, f"{json_path.relative_to(REPO_ROOT)}: no schemas validated"

    # Every declared extension must have actually been validated, not silently
    # skipped (pystac will skip a schema URI it cannot fetch). A typo or a
    # 404'd extension URI would otherwise reach production unnoticed.
    declared = set(getattr(obj, "stac_extensions", None) or [])
    missing = declared - set(validated)
    assert not missing, (
        f"{json_path.relative_to(REPO_ROOT)} declares extensions that pystac "
        f"did not validate: {sorted(missing)}. Either the schema URI is wrong "
        f"or the schema is unreachable."
    )


@pytest.mark.integration
def test_committed_catalog_validate_all_recursively() -> None:
    """`Catalog.validate_all()` walks every child/item and validates each.

    This mirrors what `generate()` does at build time but runs against the
    committed tree, so it catches drift between what was generated last and
    what's actually shipped — the case where the committed `stac/` is stale
    relative to the schemas available today.
    """
    catalog = pystac.read_file(str(COMMITTED_STAC / "catalog.json"))
    assert isinstance(catalog, pystac.Catalog)
    catalog.make_all_asset_hrefs_absolute()
    try:
        catalog.validate_all()
    except pystac.errors.STACValidationError as e:
        pytest.fail(f"catalog.validate_all() failed: {e}")
