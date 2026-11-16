"""Published IFS container declarations must match the persisted Icechunk config."""

from __future__ import annotations

import json
from pathlib import Path

import icechunk
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.integration
@pytest.mark.parametrize("days", [6, 15])
@pytest.mark.parametrize("resolution", ["0-1", "0-25"])
def test_ifs_virtual_assets_do_not_advertise_missing_store_containers(
    days: int, resolution: str
) -> None:
    collection_id = f"ecmwf-ifs-ens-forecast-{days}-day-{resolution}-degree-virtual"
    production = json.loads(
        (REPO_ROOT / "stac" / collection_id / "collection.json").read_text()
    )
    storage = icechunk.http_storage(production["assets"]["icechunk-https"]["href"])
    # One anonymous config fetch per product; no manifests or GRIB data reads.
    config = icechunk.Repository.fetch_config(storage)
    assert config is not None
    persisted_prefixes = set(config.virtual_chunk_containers or {})

    for directory in ("stac", "stac-staging", "stac-test"):
        collection = json.loads(
            (REPO_ROOT / directory / collection_id / "collection.json").read_text()
        )
        for asset_name in ("icechunk", "icechunk-https"):
            containers = collection["assets"][asset_name][
                "icechunk:virtual_chunk_containers"
            ]
            declared_prefixes = {container["url_prefix"] for container in containers}
            assert declared_prefixes == persisted_prefixes, (
                f"{directory}/{collection_id} {asset_name}: "
                f"declared {declared_prefixes}, persisted {persisted_prefixes}"
            )
