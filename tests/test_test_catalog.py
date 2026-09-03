"""Integration test: the test catalog renders the fixture collections.

These are the only tests that generate with `include_test=True`, so they're the
only ones that open `gs://` and `az://` icechunk repositories over the network.
`generate()` calls `pystac.Catalog.validate_all()`, so reaching the assertions
below also means the fixture collections passed STAC + extension schema
validation. The catalog is generated once per module — a full `generate()` run
opens every production store too, so it's far too slow to repeat per test.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from generate import generate

_GCS_ID = "test-gcs-virtual"
_GCS_BUCKET = "dynamical-icechunk-gcs-demo"
_GCS_HREF = f"gs://{_GCS_BUCKET}/{_GCS_ID}/v0.1.0.icechunk/"
_GCS_SOURCE_PREFIX = f"gs://{_GCS_BUCKET}/{_GCS_ID}/source/"
_GCS_CREDENTIALS = {"type": "gcs", "anonymous": True}

_AZ_ID = "test-azure-virtual"
_AZ_ACCOUNT = "dynamicalicechunktest"
_AZ_CONTAINER = "dynamical-icechunk-azure-demo"
_AZ_HREF = f"az://{_AZ_CONTAINER}/{_AZ_ID}/v0.1.0.icechunk/"
_AZ_SOURCE_PREFIX = f"az://{_AZ_CONTAINER}/{_AZ_ID}/source/"
_AZ_CREDENTIALS = {"type": "azure", "anonymous": True}


@pytest.fixture(scope="module")
def test_catalog_dir(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    output_dir = tmp_path_factory.mktemp("stac-test")
    generate(
        output_dir,
        root_href="https://stac-test.dynamical.org",
        include_staging=True,
        include_test=True,
    )
    return output_dir


def _collection(output_dir: pathlib.Path, collection_id: str) -> dict[str, object]:
    collection_json = output_dir / collection_id / "collection.json"
    assert collection_json.exists(), (
        f"{collection_id}/collection.json missing from the test catalog: "
        f"{sorted(p.name for p in output_dir.iterdir())}"
    )
    return json.loads(collection_json.read_text())  # type: ignore[no-any-return]


@pytest.mark.integration
def test_test_catalog_renders_gcs_fixture_collection(
    test_catalog_dir: pathlib.Path,
) -> None:
    collection = _collection(test_catalog_dir, _GCS_ID)

    icechunk_asset = collection["assets"]["icechunk"]  # type: ignore[index]
    assert icechunk_asset["href"] == _GCS_HREF
    assert icechunk_asset["xarray:storage_options"] == {"token": "anon"}
    assert icechunk_asset["icechunk:virtual_chunk_containers"] == [
        {"url_prefix": _GCS_SOURCE_PREFIX, "credentials": _GCS_CREDENTIALS}
    ]

    https_asset = collection["assets"]["icechunk-https"]  # type: ignore[index]
    assert https_asset["href"] == (
        f"https://storage.googleapis.com/{_GCS_BUCKET}/{_GCS_ID}/v0.1.0.icechunk"
    )
    assert "xarray:storage_options" not in https_asset
    assert https_asset["icechunk:virtual_chunk_containers"] == [
        {"url_prefix": _GCS_SOURCE_PREFIX, "credentials": _GCS_CREDENTIALS}
    ]


@pytest.mark.integration
def test_test_catalog_renders_azure_fixture_collection(
    test_catalog_dir: pathlib.Path,
) -> None:
    collection = _collection(test_catalog_dir, _AZ_ID)

    icechunk_asset = collection["assets"]["icechunk"]  # type: ignore[index]
    assert icechunk_asset["href"] == _AZ_HREF
    assert icechunk_asset["xarray:storage_options"] == {
        "account_name": _AZ_ACCOUNT,
        "anon": True,
    }
    assert icechunk_asset["icechunk:virtual_chunk_containers"] == [
        {"url_prefix": _AZ_SOURCE_PREFIX, "credentials": _AZ_CREDENTIALS}
    ]

    https_asset = collection["assets"]["icechunk-https"]  # type: ignore[index]
    assert https_asset["href"] == (
        f"https://{_AZ_ACCOUNT}.blob.core.windows.net/"
        f"{_AZ_CONTAINER}/{_AZ_ID}/v0.1.0.icechunk"
    )
    assert "xarray:storage_options" not in https_asset
    assert https_asset["icechunk:virtual_chunk_containers"] == [
        {"url_prefix": _AZ_SOURCE_PREFIX, "credentials": _AZ_CREDENTIALS}
    ]


@pytest.mark.integration
def test_test_catalog_is_a_superset_of_production_and_staging(
    test_catalog_dir: pathlib.Path,
) -> None:
    # The test catalog is a superset: a production item and a staging item are
    # rendered alongside the fixtures.
    ids = {p.parent.name for p in test_catalog_dir.glob("*/collection.json")}
    assert {
        "noaa-gfs-analysis",
        "ecmwf-aifs-single-forecast-virtual",
        _GCS_ID,
        _AZ_ID,
    } <= ids
