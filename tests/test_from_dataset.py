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
    icechunk_region: str | None = "us-west-2",
    virtual_chunk_container_prefixes: tuple[str, ...] = (),
) -> CatalogItem:
    return CatalogItem(
        id=item_id,
        icechunk_href=icechunk_href,
        icechunk_region=icechunk_region,  # type: ignore[arg-type]
        virtual_chunk_container_prefixes=virtual_chunk_container_prefixes,
        model_id="noaa-gfs",
        description_summary="test summary",
        reformatter_url="https://example.com/reformatter.py",
        examples=(
            DatasetExample(
                title="Example",
                code='import dynamical_catalog\n\nds = dynamical_catalog.open("x", chunks=None)',
            ),
        ),
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


def test_from_dataset_uses_cf_standard_names_for_geographic_xy_bbox() -> None:
    ds = _synthetic_dataset().rename({"latitude": "y", "longitude": "x"})
    ds["y"].attrs.update(standard_name="latitude", units="degree_north")
    ds["x"].attrs.update(standard_name="longitude", units="degree_east")

    result = CollectionInput.from_dataset(_catalog_item(), ds)

    assert result.bbox == (100.0, -10.0, 120.0, 10.0)


def test_from_dataset_prefers_literal_latitude_over_standard_name() -> None:
    ds = _synthetic_dataset()
    # A decoy coordinate claiming to be latitude must not displace the real one.
    ds = ds.assign_coords(row=("latitude", np.arange(3) * 1000.0))
    ds["row"].attrs["standard_name"] = "latitude"

    result = CollectionInput.from_dataset(_catalog_item(), ds)

    assert result.bbox == (100.0, -10.0, 120.0, 10.0)


def test_from_dataset_rejects_ambiguous_standard_name_coords() -> None:
    ds = _synthetic_dataset().rename({"latitude": "y", "longitude": "x"})
    ds["y"].attrs["standard_name"] = "latitude"
    ds["x"].attrs["standard_name"] = "longitude"
    ds = ds.assign_coords(y2=("y", np.arange(3) * 1000.0))
    ds["y2"].attrs["standard_name"] = "latitude"

    with pytest.raises(ValueError, match="several coordinates with standard_name"):
        CollectionInput.from_dataset(_catalog_item(), ds)


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
        examples=(
            DatasetExample(
                title="Example",
                code='import dynamical_catalog\n\nds = dynamical_catalog.open("x", chunks=None)',
            ),
        ),
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


def _https_asset(item: CatalogItem) -> dict[str, object]:
    collection = CollectionInput.from_dataset(item, _synthetic_dataset())
    return collection.to_pystac_collection().to_dict()["assets"]["icechunk-https"]


def test_icechunk_https_asset_uses_region_in_domain() -> None:
    item = _catalog_item(
        icechunk_href=f"s3://dynamical-noaa-gfs/{_TEST_ID}/v0.icechunk/"
    )
    asset = _https_asset(item)
    assert asset["href"] == (
        f"https://dynamical-noaa-gfs.s3.us-west-2.amazonaws.com/{_TEST_ID}/v0.icechunk"
    )
    # http_storage takes no region/anon config, so no storage_options.
    assert "xarray:storage_options" not in asset


def test_icechunk_https_asset_advertises_virtual_chunk_containers() -> None:
    item = _catalog_item(virtual_chunk_container_prefixes=("s3://noaa-hrrr-bdp-pds/",))
    asset = _https_asset(item)
    assert asset["icechunk:virtual_chunk_containers"] == [
        {
            "url_prefix": "s3://noaa-hrrr-bdp-pds/",
            "credentials": {"type": "s3", "anonymous": True},
        }
    ]


def test_https_repository_and_chunk_container_need_no_storage_options() -> None:
    item = _catalog_item(
        icechunk_href=f"https://data.example.org/{_TEST_ID}/v0.icechunk/",
        icechunk_region=None,
        virtual_chunk_container_prefixes=("https://chunks.example.org/data/",),
    )
    collection = CollectionInput.from_dataset(item, _synthetic_dataset())
    assets = collection.to_pystac_collection().to_dict()["assets"]

    assert assets["icechunk"]["href"] == (
        f"https://data.example.org/{_TEST_ID}/v0.icechunk/"
    )
    assert "xarray:storage_options" not in assets["icechunk"]
    assert assets["icechunk"]["icechunk:virtual_chunk_containers"] == [
        {
            "url_prefix": "https://chunks.example.org/data/",
            "credentials": {"type": "http"},
        }
    ]
    pystac_code = collection.to_pystac_collection().to_dict()["examples"][0][
        "variants"
    ][1]["code"]
    assert '"https://chunks.example.org/data/": icechunk.Credentials.HttpAccess()' in (
        pystac_code
    )


def test_catalog_item_rejects_unsupported_virtual_chunk_container_prefix() -> None:
    with pytest.raises(
        ValueError, match=r"must be an s3://, gs://, az:// or https:// URL"
    ):
        _catalog_item(virtual_chunk_container_prefixes=("ftp://nope/",))


# --- gs:// backend --------------------------------------------------------

_GCS_ID = "test-gcs-virtual"
_GCS_BUCKET = "dynamical-icechunk-gcs-demo"
_GCS_HREF = f"gs://{_GCS_BUCKET}/{_GCS_ID}/v0.1.0.icechunk/"
_GCS_SOURCE_PREFIX = f"gs://{_GCS_BUCKET}/{_GCS_ID}/source/"


def _gcs_catalog_item() -> CatalogItem:
    """The `test-gcs-virtual` fixture item, shaped like `CATALOG_ITEMS`' entry."""
    return CatalogItem(
        id=_GCS_ID,
        icechunk_href=_GCS_HREF,
        virtual_chunk_container_prefixes=(_GCS_SOURCE_PREFIX,),
        model_id="dynamical-test",
        description_summary="test summary",
        reformatter_url="https://github.com/dynamical-org/dynamical-catalog",
        examples=(
            DatasetExample(
                title="Read the array",
                code=(
                    "import dynamical_catalog\n\n"
                    f'ds = dynamical_catalog.open("{_GCS_ID}", chunks=None)\n'
                    'ds["temperature_2m"].isel(time=0)'
                ),
            ),
        ),
        notebooks=(),
        test=True,
    )


def _gcs_fixture_dataset() -> xr.Dataset:
    """In-memory twin of the GCS fixture store's root group.

    Mirrors the attrs, dims and chunk encoding the real repository carries so
    these assertions hold without opening it over the network.
    """
    times = pd.date_range("2026-01-01", periods=2, freq="6h").to_numpy()
    lats = np.array([37.0, 38.0, 39.0])
    lons = np.array([-109.0, -108.0, -107.0, -106.0])
    data = np.zeros((2, 3, 4), dtype="float32")
    ds = xr.Dataset(
        data_vars={
            "temperature_2m": (
                ("time", "latitude", "longitude"),
                data,
                {"units": "degC", "long_name": "2 metre temperature"},
            ),
        },
        coords={
            "time": times,
            "latitude": (
                "latitude",
                lats,
                {"standard_name": "latitude", "units": "degrees_north"},
            ),
            "longitude": (
                "longitude",
                lons,
                {"standard_name": "longitude", "units": "degrees_east"},
            ),
        },
        attrs={
            "dataset_id": _GCS_ID,
            "name": "Test GCS virtual",
            "description": (
                "Synthetic fixture on Google Cloud Storage with one virtual "
                "chunk, for testing anonymous GCS reads."
            ),
            "license": "CC-BY-4.0",
            "attribution": "dynamical.org",
            "dataset_version": "0.1.0",
            "spatial_domain": "3x4 grid over Colorado",
            "spatial_resolution": "1 degree",
            "time_domain": "2026-01-01T00 to 2026-01-01T06",
            "time_resolution": "6 hours",
        },
    )
    # Chunk encoding but no shards, matching the fixture store.
    ds["temperature_2m"].encoding = {
        "chunks": (2, 3, 4),
        "dtype": np.dtype("float32"),
    }
    return ds


def _gcs_collection_dict() -> dict[str, object]:
    collection = CollectionInput.from_dataset(
        _gcs_catalog_item(), _gcs_fixture_dataset()
    )
    return collection.to_pystac_collection().to_dict()


def test_gcs_icechunk_asset_uses_anonymous_gcsfs_token() -> None:
    asset = _gcs_collection_dict()["assets"]["icechunk"]  # type: ignore[index]
    assert asset["href"] == _GCS_HREF
    assert asset["xarray:storage_options"] == {"token": "anon"}


def test_gcs_icechunk_asset_advertises_gcs_virtual_chunk_container() -> None:
    asset = _gcs_collection_dict()["assets"]["icechunk"]  # type: ignore[index]
    assert asset["icechunk:virtual_chunk_containers"] == [
        {
            "url_prefix": _GCS_SOURCE_PREFIX,
            "credentials": {"type": "gcs", "anonymous": True},
        }
    ]


def test_gcs_icechunk_https_asset_uses_storage_googleapis_host() -> None:
    asset = _gcs_collection_dict()["assets"]["icechunk-https"]  # type: ignore[index]
    assert asset["href"] == (
        f"https://storage.googleapis.com/{_GCS_BUCKET}/{_GCS_ID}/v0.1.0.icechunk"
    )
    # http_storage takes no region/anon config, so no storage_options.
    assert "xarray:storage_options" not in asset
    assert asset["icechunk:virtual_chunk_containers"] == [
        {
            "url_prefix": _GCS_SOURCE_PREFIX,
            "credentials": {"type": "gcs", "anonymous": True},
        }
    ]


def test_gcs_pystac_example_authorizes_anonymous_gcs_credentials() -> None:
    examples = _gcs_collection_dict()["examples"]
    pystac_variant = examples[0]["variants"][1]  # type: ignore[index]
    assert pystac_variant["label"] == "pystac + icechunk"
    assert (
        f'"{_GCS_SOURCE_PREFIX}": icechunk.gcs_credentials(anonymous=True)'
        in pystac_variant["code"]
    )


def test_gcs_collection_renders_unsharded_chunking_summary() -> None:
    collection = _gcs_collection_dict()
    chunking = collection["dynamical-org:chunking"]
    assert chunking["chunk"]["shape"] == [2, 3, 4]  # type: ignore[index]
    assert "shard" not in chunking  # type: ignore[operator]
    # The prose's {{ chunking_unsharded }} fragment renders a chunk-only table.
    details = collection["description_details"]
    assert "| dimension | chunk |" in details  # type: ignore[operator]
    assert "shard" not in details  # type: ignore[operator]


# --- az:// backend --------------------------------------------------------

_AZ_ID = "test-azure-virtual"
_AZ_ACCOUNT = "dynamicalicechunktest"
_AZ_CONTAINER = "dynamical-icechunk-azure-demo"
_AZ_HREF = f"az://{_AZ_CONTAINER}/{_AZ_ID}/v0.1.0.icechunk/"
_AZ_SOURCE_PREFIX = f"az://{_AZ_CONTAINER}/{_AZ_ID}/source/"
_AZ_CREDENTIALS = {"type": "azure", "anonymous": True}


def _azure_catalog_item() -> CatalogItem:
    """The `test-azure-virtual` fixture item, shaped like `CATALOG_ITEMS`' entry."""
    return CatalogItem(
        id=_AZ_ID,
        icechunk_href=_AZ_HREF,
        icechunk_account=_AZ_ACCOUNT,
        virtual_chunk_container_prefixes=(_AZ_SOURCE_PREFIX,),
        model_id="dynamical-test",
        description_summary="test summary",
        reformatter_url="https://github.com/dynamical-org/dynamical-catalog",
        examples=(
            DatasetExample(
                title="Read the array",
                code=(
                    "import dynamical_catalog\n\n"
                    f'ds = dynamical_catalog.open("{_AZ_ID}", chunks=None)\n'
                    'ds["temperature_2m"].isel(time=0)'
                ),
            ),
        ),
        notebooks=(),
        test=True,
    )


def _azure_fixture_dataset() -> xr.Dataset:
    """In-memory twin of the Azure fixture store's root group.

    Mirrors the attrs, dims and chunk encoding the real repository carries so
    these assertions hold without opening it over the network.
    """
    times = pd.date_range("2026-01-01", periods=2, freq="6h").to_numpy()
    lats = np.array([40.0, 41.0, 42.0])
    lons = np.array([-105.0, -104.0, -103.0, -102.0])
    data = np.zeros((2, 3, 4), dtype="float32")
    ds = xr.Dataset(
        data_vars={
            "temperature_2m": (
                ("time", "latitude", "longitude"),
                data,
                {"units": "degC", "long_name": "2 metre temperature"},
            ),
        },
        coords={
            "time": times,
            "latitude": (
                "latitude",
                lats,
                {"standard_name": "latitude", "units": "degrees_north"},
            ),
            "longitude": (
                "longitude",
                lons,
                {"standard_name": "longitude", "units": "degrees_east"},
            ),
        },
        attrs={
            "dataset_id": _AZ_ID,
            "name": "Test Azure virtual",
            "description": (
                "Synthetic fixture on Azure Blob Storage with one virtual "
                "chunk, for testing anonymous Azure reads."
            ),
            "license": "CC-BY-4.0",
            "attribution": "dynamical.org",
            "dataset_version": "0.1.0",
            "spatial_domain": "3x4 grid over Colorado",
            "spatial_resolution": "1 degree",
            "time_domain": "2026-01-01T00 to 2026-01-01T06",
            "time_resolution": "6 hours",
        },
    )
    # Chunk encoding but no shards, matching the fixture store.
    ds["temperature_2m"].encoding = {
        "chunks": (2, 3, 4),
        "dtype": np.dtype("float32"),
    }
    return ds


def _azure_collection_dict() -> dict[str, object]:
    collection = CollectionInput.from_dataset(
        _azure_catalog_item(), _azure_fixture_dataset()
    )
    return collection.to_pystac_collection().to_dict()


def test_azure_icechunk_asset_uses_anonymous_adlfs_account() -> None:
    asset = _azure_collection_dict()["assets"]["icechunk"]  # type: ignore[index]
    assert asset["href"] == _AZ_HREF
    assert asset["xarray:storage_options"] == {
        "account_name": _AZ_ACCOUNT,
        "anon": True,
    }


def test_azure_icechunk_asset_advertises_azure_virtual_chunk_container() -> None:
    asset = _azure_collection_dict()["assets"]["icechunk"]  # type: ignore[index]
    assert asset["icechunk:virtual_chunk_containers"] == [
        {"url_prefix": _AZ_SOURCE_PREFIX, "credentials": _AZ_CREDENTIALS}
    ]


def test_azure_icechunk_https_asset_uses_blob_core_windows_host() -> None:
    asset = _azure_collection_dict()["assets"]["icechunk-https"]  # type: ignore[index]
    assert asset["href"] == (
        f"https://{_AZ_ACCOUNT}.blob.core.windows.net/"
        f"{_AZ_CONTAINER}/{_AZ_ID}/v0.1.0.icechunk"
    )
    # http_storage takes no region/anon config, so no storage_options.
    assert "xarray:storage_options" not in asset
    assert asset["icechunk:virtual_chunk_containers"] == [
        {"url_prefix": _AZ_SOURCE_PREFIX, "credentials": _AZ_CREDENTIALS}
    ]


def test_azure_pystac_example_authorizes_anonymous_azure_credentials() -> None:
    examples = _azure_collection_dict()["examples"]
    pystac_variant = examples[0]["variants"][1]  # type: ignore[index]
    assert pystac_variant["label"] == "pystac + icechunk"
    assert (
        f'"{_AZ_SOURCE_PREFIX}": icechunk.azure_anonymous_credentials()'
        in pystac_variant["code"]
    )


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
