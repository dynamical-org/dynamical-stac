from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from catalog import AdditionalTerms, CatalogItem, DatasetExample, DatasetNotebook
from models import CollectionInput, _dim_entry

# Use a real id so ``CatalogItem.description_details`` can resolve the
# matching ``prose/datasets/{id}.md`` fixture; the tests here don't inspect
# description content so the specific id doesn't matter.
_TEST_ID = "noaa-gfs-analysis"


def _catalog_item(
    item_id: str = _TEST_ID,
    icechunk_href: str = f"s3://test-bucket/{_TEST_ID}/v0.icechunk/",
    virtual_chunk_container_prefixes: tuple[str, ...] = (),
) -> CatalogItem:
    return CatalogItem(
        id=item_id,
        icechunk_href=icechunk_href,
        icechunk_region="us-west-2",
        virtual_chunk_container_prefixes=virtual_chunk_container_prefixes,
        model_id="noaa-gfs",
        description_summary="test summary",
        reformatter_url="https://example.com/reformatter.py",
        examples=(DatasetExample(title="Example", code="import xarray"),),
        notebooks=(DatasetNotebook(slug=item_id, title="Quickstart"),),
    )


def _synthetic_dataset(
    dataset_id: str = _TEST_ID,
    time_dim: str = "time",
    extra_var_attrs: dict[str, str] | None = None,
    ds_attrs_overrides: dict[str, object] | None = None,
) -> xr.Dataset:
    times = pd.date_range("2020-01-01", periods=3, freq="D").to_numpy()
    lats = np.array([-10.0, 0.0, 10.0])
    lons = np.array([100.0, 110.0, 120.0])
    shape = (len(times), len(lats), len(lons))
    data = np.zeros(shape, dtype="float32")
    var_attrs = {"units": "K", "long_name": "Near-surface temperature"}
    if extra_var_attrs:
        var_attrs.update(extra_var_attrs)
    ds_attrs: dict[str, object] = {
        "dataset_id": dataset_id,
        "name": "Test Dataset",
        "description": "A synthetic dataset for unit tests.",
        "license": "CC-BY-4.0",
        "attribution": "Test Attribution",
        "dataset_version": "v0.0.0",
    }
    if ds_attrs_overrides:
        ds_attrs.update(ds_attrs_overrides)
    ds = xr.Dataset(
        data_vars={
            "temperature": ((time_dim, "latitude", "longitude"), data, var_attrs)
        },
        coords={
            time_dim: times,
            "latitude": ("latitude", lats, {"units": "degree_north"}),
            "longitude": ("longitude", lons, {"units": "degree_east"}),
        },
        attrs=ds_attrs,
    )
    ds["temperature"].encoding = {
        "chunks": (1, len(lats), len(lons)),
        "shards": shape,
        "dtype": np.dtype("float32"),
    }
    return ds


def test_from_dataset_rejects_mismatched_dataset_id() -> None:
    item = _catalog_item()
    ds = _synthetic_dataset(dataset_id="different-id")
    with pytest.raises(ValueError, match="does not match store dataset_id"):
        CollectionInput.from_dataset(item, ds)


def test_from_dataset_coerces_naive_time_to_utc() -> None:
    item = _catalog_item()
    ds = _synthetic_dataset()
    result = CollectionInput.from_dataset(item, ds)
    assert result.temporal_start.tzinfo is dt.UTC
    assert result.temporal_start == dt.datetime(2020, 1, 1, tzinfo=dt.UTC)


def _synthetic_subgroup() -> xr.Dataset:
    """A nested-group dataset: same axes as the root plus a vertical ``level``."""
    times = pd.date_range("2020-01-01", periods=3, freq="D").to_numpy()
    lats = np.array([-10.0, 0.0, 10.0])
    lons = np.array([100.0, 110.0, 120.0])
    levels = np.array([1000, 500, 250], dtype="int64")
    data = np.zeros((len(times), len(lats), len(lons), len(levels)), dtype="float32")
    return xr.Dataset(
        data_vars={
            "temperature": (
                ("time", "latitude", "longitude", "level"),
                data,
                {"units": "K", "long_name": "Temperature on levels"},
            ),
        },
        coords={
            "time": times,
            "latitude": ("latitude", lats, {"units": "degree_north"}),
            "longitude": ("longitude", lons, {"units": "degree_east"}),
            "level": (
                "level",
                levels,
                {"units": "hPa", "standard_name": "air_pressure"},
            ),
        },
    )


def test_from_dataset_flattens_subgroups_with_slash_keys() -> None:
    item = _catalog_item()
    root = _synthetic_dataset()
    result = CollectionInput.from_dataset(
        item, root, {"pressure_level": _synthetic_subgroup()}
    )
    # The group's new vertical dimension is folded into cube:dimensions.
    assert "level" in result.cube_dimensions
    assert result.cube_dimensions["level"].size == 3
    assert result.cube_dimensions["level"].unit == "hPa"
    # The root variable keeps its bare name; the group variable of the same name
    # is disambiguated by a slash-prefixed key rather than colliding.
    assert "temperature" in result.cube_variables
    assert "pressure_level/temperature" in result.cube_variables
    grouped = result.cube_variables["pressure_level/temperature"]
    assert grouped.dimensions == ["time", "latitude", "longitude", "level"]


def test_from_dataset_empty_subgroups_matches_no_subgroups() -> None:
    item = _catalog_item()
    root = _synthetic_dataset()
    without = CollectionInput.from_dataset(item, root)
    empty = CollectionInput.from_dataset(item, root, {})
    assert without.cube_variables == empty.cube_variables
    assert without.cube_dimensions == empty.cube_dimensions


def test_from_dataset_prefers_init_time_over_time() -> None:
    item = _catalog_item()
    times = pd.date_range("2021-06-01", periods=2, freq="D").to_numpy()
    inits = pd.date_range("2022-06-01", periods=2, freq="D").to_numpy()
    lats = np.array([0.0, 1.0])
    lons = np.array([0.0, 1.0])
    data = np.zeros((2, 2, 2, 2), dtype="float32")
    ds = xr.Dataset(
        data_vars={
            "t": (
                ("init_time", "time", "latitude", "longitude"),
                data,
                {"long_name": "Temperature"},
            ),
        },
        coords={
            "init_time": inits,
            "time": times,
            "latitude": ("latitude", lats, {"units": "degree_north"}),
            "longitude": ("longitude", lons, {"units": "degree_east"}),
        },
        attrs={
            "dataset_id": _TEST_ID,
            "name": "Test Dataset",
            "description": "desc",
            "license": "CC-BY-4.0",
            "attribution": "Test Attribution",
            "dataset_version": "v0.0.0",
        },
    )
    ds["t"].encoding = {
        "chunks": (1, 1, 2, 2),
        "shards": (2, 2, 2, 2),
        "dtype": np.dtype("float32"),
    }
    result = CollectionInput.from_dataset(item, ds)
    assert result.temporal_start.year == 2022


def test_from_dataset_falls_back_from_units_to_unit() -> None:
    item = _catalog_item()
    ds = _synthetic_dataset(extra_var_attrs={"units": "", "unit": "m/s"})
    result = CollectionInput.from_dataset(item, ds)
    assert result.cube_variables["temperature"].unit == "m/s"


def test_from_dataset_populates_long_name_and_standard_name() -> None:
    item = _catalog_item()
    ds = _synthetic_dataset(
        extra_var_attrs={"standard_name": "air_temperature"},
    )
    variable = CollectionInput.from_dataset(item, ds).cube_variables["temperature"]
    assert variable.long_name == "Near-surface temperature"
    assert variable.standard_name == "air_temperature"


def test_from_dataset_standard_name_is_optional() -> None:
    item = _catalog_item()
    ds = _synthetic_dataset()
    variable = CollectionInput.from_dataset(item, ds).cube_variables["temperature"]
    assert variable.long_name == "Near-surface temperature"
    assert variable.standard_name is None


def test_from_dataset_requires_long_name() -> None:
    item = _catalog_item()
    ds = _synthetic_dataset(extra_var_attrs={"long_name": ""})
    with pytest.raises((KeyError, ValueError)):
        CollectionInput.from_dataset(item, ds)


def test_from_dataset_requires_attribution() -> None:
    item = _catalog_item()
    ds = _synthetic_dataset()
    del ds.attrs["attribution"]
    with pytest.raises(KeyError):
        CollectionInput.from_dataset(item, ds)


def test_from_dataset_requires_dataset_version() -> None:
    item = _catalog_item()
    ds = _synthetic_dataset()
    del ds.attrs["dataset_version"]
    with pytest.raises(KeyError):
        CollectionInput.from_dataset(item, ds)


def test_from_dataset_passes_additional_terms_through() -> None:
    terms = AdditionalTerms(
        href="https://example.org/terms",  # type: ignore[arg-type]
        title="Extra Terms",
    )
    item = CatalogItem(
        id=_TEST_ID,
        icechunk_href=f"s3://test-bucket/{_TEST_ID}/v0.icechunk/",
        icechunk_region="us-west-2",
        additional_terms=terms,
        model_id="noaa-gfs",
        description_summary="test summary",
        reformatter_url="https://example.com/reformatter.py",
        examples=(DatasetExample(title="Example", code="import xarray"),),
        notebooks=(DatasetNotebook(slug=_TEST_ID, title="Quickstart"),),
    )
    result = CollectionInput.from_dataset(item, _synthetic_dataset())
    assert result.additional_terms == terms


def _icechunk_asset(item: CatalogItem) -> dict[str, object]:
    collection = CollectionInput.from_dataset(item, _synthetic_dataset())
    return collection.to_pystac_collection().to_dict()["assets"]["icechunk"]


def test_icechunk_asset_advertises_virtual_chunk_containers() -> None:
    item = _catalog_item(virtual_chunk_container_prefixes=("s3://noaa-hrrr-bdp-pds/",))
    asset = _icechunk_asset(item)
    assert asset["icechunk:virtual_chunk_containers"] == [
        {
            "url_prefix": "s3://noaa-hrrr-bdp-pds/",
            "credentials": {"type": "s3", "anonymous": True},
        }
    ]


def test_icechunk_asset_omits_virtual_chunk_containers_by_default() -> None:
    asset = _icechunk_asset(_catalog_item())
    assert "icechunk:virtual_chunk_containers" not in asset


def test_catalog_item_rejects_non_s3_virtual_chunk_container_prefix() -> None:
    with pytest.raises(ValueError, match="must be s3://"):
        _catalog_item(virtual_chunk_container_prefixes=("gs://nope/",))


def test_dim_entry_latitude_extent_uses_degree_north() -> None:
    lats = np.array([-45.0, 0.0, 45.0])
    d = _dim_entry("latitude", xr.DataArray(lats, dims="latitude", name="latitude"))
    assert d.type == "spatial"
    assert d.axis == "y"
    assert d.extent == [-45.0, 45.0]
    assert d.unit == "degree_north"


def test_dim_entry_longitude_extent_uses_degree_east() -> None:
    lons = np.array([100.0, 110.0, 120.0])
    d = _dim_entry("longitude", xr.DataArray(lons, dims="longitude", name="longitude"))
    assert d.type == "spatial"
    assert d.axis == "x"
    assert d.unit == "degree_east"


def test_dim_entry_xy_defaults_to_meters() -> None:
    xs = np.array([0.0, 1000.0, 2000.0])
    d = _dim_entry("x", xr.DataArray(xs, dims="x", name="x"))
    assert d.type == "spatial"
    assert d.axis == "x"
    assert d.unit == "m"


def test_dim_entry_unknown_coord_falls_back_to_none() -> None:
    labels = np.array(["a", "b", "c"], dtype=object)
    d = _dim_entry(
        "member",
        xr.DataArray(labels, dims="member", name="member", attrs={"units": ""}),
    )
    assert d.type == "other"
    assert d.extent == [None, None]
