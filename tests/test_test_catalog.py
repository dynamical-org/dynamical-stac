"""Integration test: the test catalog renders the GCS fixture collection.

This is the only test that generates with `include_test=True`, so it's the only
one that opens a `gs://` icechunk repository over the network. `generate()`
calls `pystac.Catalog.validate_all()`, so reaching the assertions below also
means the fixture collection passed STAC + extension schema validation.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from generate import generate

_ID = "test-gcs-virtual"
_BUCKET = "dynamical-icechunk-gcs-demo"
_HREF = f"gs://{_BUCKET}/{_ID}/v0.1.0.icechunk/"
_SOURCE_PREFIX = f"gs://{_BUCKET}/{_ID}/source/"
_GCS_CREDENTIALS = {"type": "gcs", "anonymous": True}


@pytest.mark.integration
def test_test_catalog_renders_gcs_fixture_collection(tmp_path: pathlib.Path) -> None:
    generate(
        tmp_path,
        root_href="https://stac-test.dynamical.org",
        include_staging=True,
        include_test=True,
    )

    collection_json = tmp_path / _ID / "collection.json"
    assert collection_json.exists(), (
        f"{_ID}/collection.json missing from the test catalog: "
        f"{sorted(p.name for p in tmp_path.iterdir())}"
    )
    collection = json.loads(collection_json.read_text())

    icechunk_asset = collection["assets"]["icechunk"]
    assert icechunk_asset["href"] == _HREF
    assert icechunk_asset["xarray:storage_options"] == {"token": "anon"}
    assert icechunk_asset["icechunk:virtual_chunk_containers"] == [
        {"url_prefix": _SOURCE_PREFIX, "credentials": _GCS_CREDENTIALS}
    ]

    https_asset = collection["assets"]["icechunk-https"]
    assert https_asset["href"] == (
        f"https://storage.googleapis.com/{_BUCKET}/{_ID}/v0.1.0.icechunk"
    )
    assert "xarray:storage_options" not in https_asset
    assert https_asset["icechunk:virtual_chunk_containers"] == [
        {"url_prefix": _SOURCE_PREFIX, "credentials": _GCS_CREDENTIALS}
    ]

    # The test catalog is a superset: a production item and a staging item are
    # rendered alongside the fixture.
    ids = {p.parent.name for p in tmp_path.glob("*/collection.json")}
    assert {"noaa-gfs-analysis", "ecmwf-aifs-single-forecast-virtual", _ID} <= ids
