from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from catalog import AdditionalTerms, CatalogItem
from models import CollectionInput, _dim_entry


def _catalog_item(
    item_id: str = "test-dataset",
    icechunk_href: str = "s3://test-bucket/test-dataset/v0.icechunk/",
) -> CatalogItem:
    return CatalogItem(
        id=item_id,
        model_id="test-model",
        description="A synthetic dataset for unit tests.",
        icechunk_href=icechunk_href,
        icechunk_region="us-west-2",
        zarr_href="https://data.example.com/test-dataset/latest.zarr",  # type: ignore[arg-type]
    )


def _synthetic_dataset(
    dataset_id: str = "test-dataset",
    time_dim: str = "time",
    extra_var_attrs: dict[str, str] | None = None,
    ds_attrs_overrides: dict[str, object] | None = None,
) -> xr.Dataset:
    times = pd.date_range("2020-01-01", periods=3, freq="D").to_numpy()
    lats = np.array([-10.0, 0.0, 10.0])
    lons = np.array([100.0, 110.0, 120.0])
    data = np.zeros((len(times), len(lats), len(lons)), dtype="float32")
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
    return xr.Dataset(
        data_vars={
            "temperature": ((time_dim, "latitude", "longitude"), data, var_attrs)
        },
        coords={time_dim: times, "latitude": lats, "longitude": lons},
        attrs=ds_attrs,
    )


def test_from_dataset_rejects_mismatched_dataset_id() -> None:
    item = _catalog_item(
        item_id="expected-id",
        icechunk_href="s3://test-bucket/expected-id/v0.icechunk/",
    )
    ds = _synthetic_dataset(dataset_id="different-id")
    with pytest.raises(ValueError, match="does not match store dataset_id"):
        CollectionInput.from_dataset(item, ds)


def test_from_dataset_coerces_naive_time_to_utc() -> None:
    item = _catalog_item()
    ds = _synthetic_dataset()
    result = CollectionInput.from_dataset(item, ds)
    assert result.temporal_start.tzinfo is dt.UTC
    assert result.temporal_start == dt.datetime(2020, 1, 1, tzinfo=dt.UTC)


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
            "latitude": lats,
            "longitude": lons,
        },
        attrs={
            "dataset_id": "test-dataset",
            "name": "Test Dataset",
            "description": "desc",
            "license": "CC-BY-4.0",
            "attribution": "Test Attribution",
            "dataset_version": "v0.0.0",
        },
    )
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


def test_from_dataset_uses_catalog_item_description_not_ds_attr() -> None:
    item = _catalog_item()
    ds = _synthetic_dataset(
        ds_attrs_overrides={"description": "this should be ignored"}
    )
    result = CollectionInput.from_dataset(item, ds)
    assert result.description == item.description


def test_from_dataset_propagates_model_id() -> None:
    item = _catalog_item()
    result = CollectionInput.from_dataset(item, _synthetic_dataset())
    assert result.model_id == item.model_id


def test_from_dataset_passes_additional_terms_through() -> None:
    terms = AdditionalTerms(
        href="https://example.org/terms",  # type: ignore[arg-type]
        title="Extra Terms",
    )
    item = CatalogItem(
        id="test-dataset",
        model_id="test-model",
        description="A synthetic dataset for unit tests.",
        icechunk_href="s3://test-bucket/test-dataset/v0.icechunk/",
        icechunk_region="us-west-2",
        zarr_href="https://data.example.com/test-dataset/latest.zarr",  # type: ignore[arg-type]
        additional_terms=terms,
    )
    result = CollectionInput.from_dataset(item, _synthetic_dataset())
    assert result.additional_terms == terms


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
