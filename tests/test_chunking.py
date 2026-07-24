from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from catalog import CatalogItem, DatasetExample, DatasetNotebook
from models import (
    Chunking,
    CollectionInput,
    _build_chunking,
    _coord_length,
    _human_bytes,
    _human_timedelta,
)

_TEST_ID = "noaa-gfs-analysis"


def _catalog_item() -> CatalogItem:
    return CatalogItem(
        id=_TEST_ID,
        icechunk_href=f"s3://test-bucket/{_TEST_ID}/v0.icechunk/",
        icechunk_region="us-west-2",
        model_id="noaa-gfs",
        description_summary="test summary",
        reformatter_url="https://example.com/reformatter.py",
        examples=(
            DatasetExample(
                title="Example",
                code='import dynamical_catalog\n\nds = dynamical_catalog.open("x", chunks=None)',
            ),
        ),
        notebooks=(DatasetNotebook(slug=_TEST_ID, title="Quickstart"),),
    )


def _chunked_dataset(
    chunks: tuple[int, ...] = (1, 2, 2),
    shards: tuple[int, ...] | None = (2, 2, 2),
    n_vars: int = 1,
    second_var_chunks: tuple[int, ...] | None = None,
) -> xr.Dataset:
    """Synthetic dataset carrying zarr-style chunk/shard encoding."""
    times = pd.date_range("2020-01-01", periods=4, freq="h").to_numpy()
    lats = np.array([10.0, 9.75, 9.5, 9.25])  # descending, 0.25° step
    lons = np.array([0.0, 0.25, 0.5, 0.75])
    shape = (len(times), len(lats), len(lons))
    dims = ("time", "latitude", "longitude")
    lats_attrs = {"units": "degree_north"}
    lons_attrs = {"units": "degree_east"}

    data_vars: dict[str, object] = {}
    for i in range(n_vars):
        c = second_var_chunks if (i == 1 and second_var_chunks) else chunks
        da = xr.DataArray(
            np.zeros(shape, dtype="float32"),
            dims=dims,
            attrs={"long_name": f"Var {i}"},
        )
        da.encoding = {"chunks": c, "shards": shards, "dtype": np.dtype("float32")}
        data_vars[f"var{i}"] = da

    ds = xr.Dataset(
        data_vars=data_vars,
        coords={
            "time": times,
            "latitude": ("latitude", lats, lats_attrs),
            "longitude": ("longitude", lons, lons_attrs),
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
    return ds


def test_human_bytes_scales_units() -> None:
    assert _human_bytes(512) == "512.0 B"
    assert _human_bytes(1024) == "1.0 KiB"
    assert _human_bytes(6 * 1024 * 1024) == "6.0 MiB"


def test_human_timedelta_prefers_days_then_hours() -> None:
    assert _human_timedelta(pd.Timedelta(days=60)) == "60 days"
    assert _human_timedelta(pd.Timedelta(days=1)) == "1 day"
    assert _human_timedelta(pd.Timedelta(hours=105)) == "105 hours"
    assert _human_timedelta(pd.Timedelta(hours=1)) == "1 hour"


def test_coord_length_degrees_uses_absolute_span_for_descending_lat() -> None:
    ds = _chunked_dataset()
    # 4 cells of 0.25° -> full dimension, extended by one cell width -> 1.0°
    assert _coord_length(ds, "latitude", 4) == "1°"
    # 2 cells -> 0.5°, sign-independent
    assert _coord_length(ds, "latitude", 2) == "0.5°"


def test_coord_length_temporal_in_hours() -> None:
    ds = _chunked_dataset()
    assert _coord_length(ds, "time", 2) == "2 hours"


def test_coord_length_meters_promote_to_km() -> None:
    xs = np.arange(0.0, 3000.0 * 5, 3000.0)
    coord = xr.DataArray(xs, dims="x", name="x", attrs={"units": "m"})
    ds = xr.Dataset(coords={"x": coord})
    assert _coord_length(ds, "x", 3) == "9 km"


def test_coord_length_none_for_dimensionless_axis() -> None:
    members = np.arange(5)
    coord = xr.DataArray(
        members, dims="ensemble_member", name="ensemble_member", attrs={"units": "1"}
    )
    ds = xr.Dataset(coords={"ensemble_member": coord})
    assert _coord_length(ds, "ensemble_member", 3) is None


def test_build_chunking_computes_grids_and_sizes() -> None:
    ds = _chunked_dataset(chunks=(1, 2, 2), shards=(2, 4, 4))
    chunking = _build_chunking(ds)
    assert isinstance(chunking, Chunking)
    assert chunking.dtype == "float32"
    assert chunking.chunk.shape == [1, 2, 2]
    # 1*2*2 float32 = 16 bytes
    assert chunking.chunk.uncompressed_size_bytes == 16
    assert chunking.chunk.lengths == {
        "time": "1 hour",
        "latitude": "0.5°",
        "longitude": "0.5°",
    }
    assert chunking.shard.shape == [2, 4, 4]
    assert chunking.shard.uncompressed_size_bytes == 2 * 4 * 4 * 4


def test_build_chunking_returns_none_without_encoding() -> None:
    ds = _chunked_dataset()
    for name in ds.data_vars:
        ds[name].encoding = {}
    assert _build_chunking(ds) is None


def test_build_chunking_raises_on_non_uniform_variables() -> None:
    ds = _chunked_dataset(n_vars=2, second_var_chunks=(2, 2, 2))
    with pytest.raises(ValueError, match="non-uniform chunk/shard"):
        _build_chunking(ds)


def test_from_dataset_populates_variable_chunks_and_collection_chunking() -> None:
    result = CollectionInput.from_dataset(_catalog_item(), _chunked_dataset())
    variable = result.cube_variables["var0"]
    assert variable.chunks == [1, 2, 2]
    assert variable.shards == [2, 2, 2]
    assert result.chunking is not None

    fields = result.to_pystac_collection().extra_fields
    assert fields["dynamical-org:chunking"]["chunk"]["shape"] == [1, 2, 2]
    assert fields["cube:variables"]["var0"]["chunks"] == [1, 2, 2]


def test_from_dataset_raises_without_encoding_when_prose_needs_table() -> None:
    # The dataset prose references the chunk/shard table, so a store with no
    # chunk/shard encoding (nothing to render) must fail loudly rather than
    # ship a page with a dangling table.
    ds = _chunked_dataset()
    for name in ds.data_vars:
        ds[name].encoding = {}
    with pytest.raises(ValueError, match="no chunk/shard encoding"):
        CollectionInput.from_dataset(_catalog_item(), ds)


def test_coord_length_tildes_non_uniform_span() -> None:
    # 3-hourly for the first stretch, then 6-hourly: the first n cells span a
    # different duration than the last n, so the reported span is approximate.
    times = pd.to_datetime(
        ["2020-01-01T00", "2020-01-01T03", "2020-01-01T06", "2020-01-01T12"]
    ).to_numpy()
    coord = xr.DataArray(times, dims="lead_time", name="lead_time")
    ds = xr.Dataset(coords={"lead_time": coord})
    assert _coord_length(ds, "lead_time", 2) == "~6 hours"


def test_coord_length_raises_on_unhandled_spatial_units() -> None:
    coord = xr.DataArray(
        np.array([0.0, 1.0, 2.0]),
        dims="latitude",
        name="latitude",
        attrs={"units": "bananas"},
    )
    ds = xr.Dataset(coords={"latitude": coord})
    with pytest.raises(ValueError, match="unhandled coord units"):
        _coord_length(ds, "latitude", 2)


def test_chunking_as_markdown_table_is_transposed() -> None:
    chunking = _build_chunking(_chunked_dataset(chunks=(1, 2, 2), shards=(2, 4, 4)))
    assert chunking is not None
    assert chunking.as_markdown_table() == (
        "| dimension | chunk | shard |\n"
        "|---|---|---|\n"
        "| time | 1 (1 hour) | 2 (2 hours) |\n"
        "| latitude | 2 (0.5°) | 4 (1°) |\n"
        "| longitude | 2 (0.5°) | 4 (1°) |\n"
        "| **uncompressed** | 16.0 B | 128.0 B |"
    )


def test_build_chunking_unsharded_omits_shard() -> None:
    # A store with chunks but no shards (e.g. a virtual dataset) yields a
    # chunk-only summary rather than being dropped entirely.
    chunking = _build_chunking(_chunked_dataset(chunks=(1, 2, 2), shards=None))
    assert chunking is not None
    assert chunking.chunk.shape == [1, 2, 2]
    assert chunking.shard is None


def test_chunking_as_markdown_table_unsharded_drops_shard_column() -> None:
    chunking = _build_chunking(_chunked_dataset(chunks=(1, 2, 2), shards=None))
    assert chunking is not None
    assert chunking.as_markdown_table() == (
        "| dimension | chunk |\n"
        "|---|---|\n"
        "| time | 1 (1 hour) |\n"
        "| latitude | 2 (0.5°) |\n"
        "| longitude | 2 (0.5°) |\n"
        "| **uncompressed** | 16.0 B |"
    )


def test_from_dataset_unsharded_omits_shard_key_in_stac() -> None:
    result = CollectionInput.from_dataset(
        _catalog_item(), _chunked_dataset(shards=None)
    )
    assert result.chunking is not None
    assert result.chunking.shard is None

    chunking_field = result.to_pystac_collection().extra_fields[
        "dynamical-org:chunking"
    ]
    assert "shard" not in chunking_field
    assert chunking_field["chunk"]["shape"] == [1, 2, 2]
