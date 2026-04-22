from __future__ import annotations

import datetime as dt

import numpy as np
import pydantic
import pytest
import xarray as xr

from catalog import AdditionalTerms, CatalogItem, DatasetLicense
from models import CollectionInput, CubeDimension, CubeVariable, _dim_entry


def _valid_input(**overrides: object) -> CollectionInput:
    defaults: dict[str, object] = {
        "id": "test-dataset",
        "name": "Test Dataset",
        "description": "A test dataset",
        "license": "CC-BY-4.0",
        "bbox": (-180.0, -90.0, 180.0, 90.0),
        "temporal_start": dt.datetime(2020, 1, 1, tzinfo=dt.UTC),
        "cube_dimensions": {
            "latitude": CubeDimension(
                type="spatial",
                axis="y",
                extent=[-90.0, 90.0],
                unit="degree_north",
                size=721,
            ),
        },
        "cube_variables": {
            "temp": CubeVariable(
                dimensions=["latitude"], unit="K", long_name="Temperature"
            ),
        },
        "icechunk_href": "s3://test-bucket/test-prefix/",
        "icechunk_region": "us-west-2",
        "zarr_href": "https://data.example.com/test-dataset/latest.zarr",
        "attribution": "Test Attribution",
        "version": "v0.0.0",
    }
    defaults.update(overrides)
    return CollectionInput(**defaults)  # type: ignore[arg-type]


def test_colab_url_is_derived_from_github_url() -> None:
    c = _valid_input(id="my-dataset")
    assert (
        c.github_notebook_url
        == "https://github.com/dynamical-org/notebooks/blob/main/my-dataset.ipynb"
    )
    assert (
        c.colab_notebook_url
        == "https://colab.research.google.com/github/dynamical-org/notebooks/blob/main/my-dataset.ipynb"
    )
    assert c.colab_notebook_url == c.github_notebook_url.replace(
        "https://github.com/", "https://colab.research.google.com/github/"
    )


def test_about_url_and_icechunk_href() -> None:
    c = _valid_input(id="ds", icechunk_href="s3://b/p/")
    assert c.about_url == "https://dynamical.org/catalog/ds/"
    assert c.icechunk_href == "s3://b/p/"


def test_catalog_item_derives_bucket_and_prefix_from_href() -> None:
    item = CatalogItem(
        id="ds",
        icechunk_href="s3://dynamical-noaa-gfs/ds/v1.0.icechunk/",
        icechunk_region="us-west-2",
        zarr_href="https://data.example.com/ds/latest.zarr",  # type: ignore[arg-type]
    )
    assert item.icechunk_bucket == "dynamical-noaa-gfs"
    assert item.icechunk_prefix == "ds/v1.0.icechunk/"


def test_catalog_item_rejects_non_s3_icechunk_href() -> None:
    with pytest.raises(pydantic.ValidationError):
        CatalogItem(
            id="ds",
            icechunk_href="https://not-s3/ds/",
            icechunk_region="us-west-2",
            zarr_href="https://data.example.com/ds/latest.zarr",  # type: ignore[arg-type]
        )


def test_bbox_validation_rejects_out_of_range() -> None:
    with pytest.raises(pydantic.ValidationError):
        _valid_input(bbox=(-181.0, -90.0, 180.0, 90.0))
    with pytest.raises(pydantic.ValidationError):
        _valid_input(bbox=(0.0, 90.0, 0.0, -90.0))


def test_temporal_start_rejects_naive_datetime() -> None:
    with pytest.raises(pydantic.ValidationError):
        _valid_input(temporal_start=dt.datetime(2020, 1, 1))


def test_temporal_start_normalizes_to_utc() -> None:
    tz = dt.timezone(dt.timedelta(hours=5))
    c = _valid_input(temporal_start=dt.datetime(2020, 1, 1, 12, tzinfo=tz))
    assert c.temporal_start.tzinfo is dt.UTC
    assert c.temporal_start.hour == 7


def test_model_is_frozen() -> None:
    c = _valid_input()
    with pytest.raises(pydantic.ValidationError):
        c.id = "changed"  # type: ignore[misc]


def test_license_accepts_enum_and_string() -> None:
    assert _valid_input(license=DatasetLicense.CC_BY_4_0).license == "CC-BY-4.0"
    assert _valid_input(license="CC-BY-4.0").license == DatasetLicense.CC_BY_4_0


def test_license_rejects_unknown_value() -> None:
    with pytest.raises(pydantic.ValidationError):
        _valid_input(license="MIT")


def test_cube_variable_accepts_short_name_and_comment() -> None:
    v = CubeVariable(
        dimensions=["time"],
        unit="K",
        long_name="Temperature",
        standard_name="air_temperature",
        short_name="2t",
        comment="averaged",
    )
    assert v.short_name == "2t"
    assert v.comment == "averaged"
    assert v.standard_name == "air_temperature"


def test_dim_entry_temporal_extent_is_open_ended() -> None:
    times = np.array(["2021-05-01", "2022-01-01", "2023-06-15"], dtype="datetime64[ns]")
    coord = xr.DataArray(times, dims="time", name="time")
    d = _dim_entry("time", coord)
    assert d.type == "temporal"
    assert d.extent == ["2021-05-01T00:00:00Z", None]
    assert d.size is None


def test_dim_entry_timedelta_extent_in_seconds() -> None:
    leads = np.array([0, 3600, 86400], dtype="timedelta64[s]").astype("timedelta64[ns]")
    coord = xr.DataArray(leads, dims="lead_time", name="lead_time")
    d = _dim_entry("lead_time", coord)
    assert d.type == "other"
    assert d.extent == [0, 86400]
    assert d.unit == "seconds"


@pytest.mark.parametrize(
    "extent",
    [
        ["2020-01-01T00:00:00Z", "2020-12-31T00:00:00Z"],
        [-90.0, 90.0],
        [0, 86400],
        [None, None],
    ],
)
def test_cube_dimension_extent_accepts_supported_shapes(
    extent: list[object],
) -> None:
    d = CubeDimension(type="other", extent=extent, size=2)  # type: ignore[arg-type]
    assert d.extent == extent


def test_cube_dimension_extent_rejects_mixed_types() -> None:
    with pytest.raises(pydantic.ValidationError):
        CubeDimension(type="other", extent=[1, "a"], size=2)  # type: ignore[list-item]


def test_collection_input_renders_license_link_only_without_terms() -> None:
    collection = _valid_input().to_pystac_collection()
    license_links = [link for link in collection.links if link.rel == "license"]
    assert len(license_links) == 1


def test_collection_input_renders_additional_terms_as_extra_license_link() -> None:
    terms = AdditionalTerms(
        href="https://example.org/terms",  # type: ignore[arg-type]
        title="Extra Terms",
    )
    collection = _valid_input(additional_terms=terms).to_pystac_collection()
    license_links = [link for link in collection.links if link.rel == "license"]
    assert len(license_links) == 2
    assert any(link.title == "Extra Terms" for link in license_links)


def test_additional_terms_rejects_empty_title() -> None:
    with pytest.raises(pydantic.ValidationError):
        AdditionalTerms(href="https://example.org/terms", title="")  # type: ignore[arg-type]
