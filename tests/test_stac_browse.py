"""Integration test: browse the generated STAC using the standard pystac-client library."""

from __future__ import annotations

import pathlib

import pytest

from catalog import _COLLECTION_IDS


@pytest.mark.integration
def test_browse_with_pystac_client(
    served_catalog: tuple[pathlib.Path, str],
) -> None:
    pystac_client = pytest.importorskip("pystac_client")

    _, root_url = served_catalog
    client = pystac_client.Client.open(f"{root_url}/catalog.json")

    collection_ids = {c.id for c in client.get_collections()}
    assert collection_ids == set(_COLLECTION_IDS)

    for cid in _COLLECTION_IDS:
        col = client.get_collection(cid)
        assert col.title
        assert col.description
        assert col.extent.spatial.bboxes
        assert col.extent.temporal.intervals
        assert "zarr" in col.assets
