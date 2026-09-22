from __future__ import annotations

import json
import pathlib

import pytest
from pydantic import ValidationError

from catalog import CATALOG_ITEMS
from environments import (
    PRODUCTION,
    ClientVersionRange,
    _check_environments,
    environment_for_client,
    stac_environment,
)


@pytest.mark.parametrize(
    ("client", "filename"),
    [
        ("0.4.0", "catalog_0.4.0-0.5.0.json"),
        ("0.5.0", "catalog_0.4.0-0.5.0.json"),
        ("0.6.0", "catalog.json"),
        ("0.7.0", "catalog_0.7.0-0.8.0.json"),
        ("0.8.0", "catalog_0.7.0-0.8.0.json"),
        ("0.8.1", "catalog.json"),
        ("0.10.0", "catalog.json"),
        ("1.0.1", "catalog.json"),
    ],
)
def test_client_selects_numeric_range(client: str, filename: str) -> None:
    environment = environment_for_client(client)
    assert environment.directory == "stac"
    assert environment.catalog_url == f"https://stac.dynamical.org/{filename}"


def test_range_name_is_derived_from_normalized_versions() -> None:
    versions = ClientVersionRange(min_version="v0.7.0", max_version="0.8.0")
    assert versions.name == "0.7.0-0.8.0"
    assert versions.contains("0.8.0")
    assert not versions.contains("0.10.0")


@pytest.mark.parametrize(
    ("minimum", "maximum"),
    [("bogus", "0.8.0"), ("0.8.0", "0.5.0")],
)
def test_invalid_version_bounds_are_rejected(minimum: str, maximum: str) -> None:
    with pytest.raises(ValidationError):
        ClientVersionRange(min_version=minimum, max_version=maximum)


@pytest.mark.parametrize("name", ["0.4.0-0.5.0", "0.7.0-0.8.0"])
def test_legacy_membership_is_explicit_and_production_only(name: str) -> None:
    environment = stac_environment(name)
    assert environment.description
    assert environment.directory == "stac"
    items = [item for item in CATALOG_ITEMS if name in item.environments]
    assert items
    assert all("production" in item.environments for item in items)
    if name == "0.4.0-0.5.0":
        assert all(not item.virtual_chunk_container_prefixes for item in items)
    for directory in ("stac-staging", "stac-test"):
        assert not (
            pathlib.Path(__file__).parents[1] / directory / environment.root_filename
        ).exists()


def test_plain_0_5_excludes_virtual_collections_requiring_an_optional_codec() -> None:
    materialized_name = environment_for_client("0.5.0").name
    virtual_name = environment_for_client("0.7.0").name
    selected = {
        environment: {
            item.id for item in CATALOG_ITEMS if environment in item.environments
        }
        for environment in (materialized_name, virtual_name)
    }
    s3_virtual_ids = {
        "noaa-hrrr-analysis-virtual",
        "noaa-hrrr-forecast-18-hour-virtual",
        "noaa-hrrr-forecast-48-hour-virtual",
    }

    assert len(selected[materialized_name]) == 16
    assert selected[materialized_name].isdisjoint(s3_virtual_ids)
    assert s3_virtual_ids <= selected[virtual_name]
    assert "ecmwf-aifs-single-forecast-virtual" not in (
        selected[materialized_name] | selected[virtual_name]
    )


@pytest.mark.parametrize(
    ("first", "second"),
    [
        (("0.4.0", "0.5.0"), ("0.5.0", "0.8.0")),
        (("0.4.0", "0.8.0"), ("0.5.0", "0.7.0")),
    ],
)
def test_overlapping_client_ranges_are_rejected(
    first: tuple[str, str], second: tuple[str, str]
) -> None:
    environments = tuple(
        PRODUCTION.for_client_range(
            min_version=low, max_version=high, description="test"
        )
        for low, high in (first, second)
    )
    with pytest.raises(ValueError, match="overlapping"):
        _check_environments(environments)


def test_duplicate_environment_outputs_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        _check_environments((PRODUCTION, PRODUCTION))


@pytest.mark.parametrize("name", ["0.4.0-0.5.0", "0.7.0-0.8.0"])
def test_committed_legacy_root_links_exactly_its_explicit_items(name: str) -> None:
    environment = stac_environment(name)
    repo_root = pathlib.Path(__file__).parents[1]
    root = json.loads((repo_root / "stac" / environment.root_filename).read_text())
    children = [link for link in root["links"] if link["rel"] == "child"]
    assert {link["href"] for link in children} == {
        f"https://stac.dynamical.org/{item.id}/collection.json"
        for item in CATALOG_ITEMS
        if name in item.environments
    }
    assert (
        next(link["href"] for link in root["links"] if link["rel"] == "self")
        == environment.catalog_url
    )
    assert (
        next(link["href"] for link in root["links"] if link["rel"] == "root")
        == PRODUCTION.catalog_url
    )
