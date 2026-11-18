from __future__ import annotations

import pathlib

import icechunk
import numpy as np
import pytest
import xarray as xr

import generate
from catalog import (
    CatalogItem,
    DatasetExample,
    UpstreamSource,
)
from models import CollectionInput


@pytest.fixture
def native_item() -> CatalogItem:
    # An existing prose id lets description_details resolve without new prose.
    return CatalogItem(
        environments=["test"],
        id="noaa-gfs-analysis",
        icechunk_href="s3://test-bucket/noaa-gfs-analysis/v0.icechunk/",
        icechunk_region="us-west-2",
        model_id="noaa-gfs",
        source=UpstreamSource(href="https://example.com/source", title="Source"),  # type: ignore[arg-type]
        description_summary="Native grid test dataset.",
        reformatter_url="https://example.com/reformatter.py",
        examples=(
            DatasetExample(
                title="Open",
                code='import dynamical_catalog\n\nds = dynamical_catalog.open("noaa-gfs-analysis", chunks=None)',
            ),
        ),
    )


@pytest.fixture
def native_root() -> xr.Dataset:
    inits = np.array(["2026-01-01", "2026-01-02"], dtype="datetime64[ns]")
    leads = np.array([0, 6], dtype="timedelta64[h]")
    ds = xr.Dataset(
        data_vars={
            "temperature": (
                ("init_time", "lead_time", "cell"),
                np.arange(16, dtype="float32").reshape(2, 2, 4),
                {
                    "long_name": "Near-surface temperature",
                    "units": "K",
                    "mesh": "/mesh/mesh",
                    "location": "face",
                },
            ),
        },
        coords={
            "init_time": inits,
            "lead_time": leads,
            "valid_time": (("init_time", "lead_time"), inits[:, None] + leads),
            "cell": (
                "cell",
                np.arange(4, dtype="int32"),
                {"long_name": "Native grid cell index", "units": "1"},
            ),
            "latitude": (
                "cell",
                [45.0, 46.0, 47.0, 48.0],
                {"standard_name": "latitude", "units": "degree_north"},
            ),
            "longitude": (
                "cell",
                [181.0, 182.0, 183.0, 184.0],
                {"standard_name": "longitude", "units": "degree_east"},
            ),
            "spatial_ref": ((), 0),
        },
        attrs={
            "dataset_id": "noaa-gfs-analysis",
            "name": "Native grid test dataset",
            "description": "Synthetic forecast on native triangles.",
            "license": "CC-BY-4.0",
            "attribution": "Test attribution",
            "dataset_version": "v0.0.0",
        },
    )
    ds.temperature.encoding = {
        "chunks": (1, 1, 2),
        "shards": (1, 2, 4),
        "dtype": np.dtype("float32"),
    }
    return ds


@pytest.fixture
def native_mesh() -> xr.Dataset:
    return xr.Dataset(
        data_vars={
            "mesh": (
                (),
                0,
                {
                    "cf_role": "mesh_topology",
                    "topology_dimension": 2,
                    "node_coordinates": "node_longitude node_latitude",
                    "face_node_connectivity": "face_node_connectivity",
                    "face_dimension": "cell",
                    "node_dimension": "node",
                },
            ),
            "node_latitude": (
                "node",
                [44.0, 46.0, 48.0, 44.0, 46.0, 48.0],
                {"standard_name": "latitude", "units": "degree_north"},
            ),
            "node_longitude": (
                "node",
                [180.0, 182.0, 184.0, 182.0, 184.0, 186.0],
                {"standard_name": "longitude", "units": "degree_east"},
            ),
            "face_node_connectivity": (
                ("cell", "max_nodes_per_face"),
                np.array([[0, 1, 3], [1, 4, 3], [1, 2, 4], [2, 5, 4]], dtype="int32"),
                {"cf_role": "face_node_connectivity", "start_index": 0},
            ),
        },
    )


@pytest.mark.parametrize(
    ("mesh_group", "topology_variable"), [("mesh", "mesh"), ("geometry", "topology")]
)
def test_native_mesh_store_generates_without_exposing_topology_as_data(
    *,
    native_item: CatalogItem,
    native_root: xr.Dataset,
    native_mesh: xr.Dataset,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    mesh_group: str,
    topology_variable: str,
) -> None:
    """Real Icechunk discovery must preserve coordinates and skip static topology."""
    storage = icechunk.local_filesystem_storage(str(tmp_path / "repo"))
    repo = icechunk.Repository.create(storage)
    session = repo.writable_session("main")
    native_root.temperature.attrs["mesh"] = f"/{mesh_group}/{topology_variable}"
    native_mesh = native_mesh.rename({"mesh": topology_variable})
    native_root.to_zarr(session.store, mode="w", consolidated=False)
    native_mesh.to_zarr(session.store, group=mesh_group, mode="a", consolidated=False)
    session.commit("Write synthetic native grid")
    monkeypatch.setattr(generate, "_storage", lambda item: storage)

    root, groups = generate._open_icechunk(native_item)
    collection = CollectionInput.from_dataset(
        native_item, root, groups
    ).to_pystac_collection()
    document = collection.to_dict()

    assert set(document["cube:variables"]) == {"temperature"}
    assert set(document["cube:dimensions"]) == {"init_time", "lead_time", "cell"}
    cell = document["cube:dimensions"]["cell"]
    assert cell["type"] == "other"
    assert cell["extent"] == [0, 3]
    assert cell["size"] == 4
    assert cell["description"] == (
        "Native grid cell index, in source order. Cell centres are the "
        "`latitude` and `longitude` coordinates. Cell polygons are in the UGRID "
        f"mesh topology in the `{mesh_group}` group."
    )
    assert document["extent"]["spatial"]["bbox"] == [[-179.0, 45.0, -176.0, 48.0]]
    assert document["dynamical-org:mesh"] == {
        "group": mesh_group,
        "topology_variable": topology_variable,
        "face_dimension": "cell",
        "conventions": "UGRID-1.0",
    }
    links = collection.get_links("describedby")
    assert len(links) == 1
    assert links[0].href == "https://ugrid-conventions.github.io/ugrid-conventions/"
    assert links[0].media_type == "text/html"
    assert links[0].title == (
        f'UGRID 1.0 conventions (mesh topology in the "{mesh_group}" group)'
    )
    validated = collection.validate()
    assert validated
    assert set(collection.stac_extensions) <= set(validated)


@pytest.mark.parametrize("cf_names", [False, True], ids=["literal", "standard-name"])
def test_native_centres_describe_index_without_inventing_topology(
    native_item: CatalogItem, native_root: xr.Dataset, cf_names: bool
) -> None:
    if cf_names:
        native_root = native_root.rename({"latitude": "lat", "longitude": "lon"})
    collection = CollectionInput.from_dataset(
        native_item, native_root
    ).to_pystac_collection()
    document = collection.to_dict()
    cell = document["cube:dimensions"]["cell"]
    assert cell["type"] == "other"
    assert cell["extent"] == [0, 3]
    assert cell["size"] == 4
    assert cell["description"] == (
        "Native grid cell index, in source order. Cell centres are the "
        "`latitude` and `longitude` coordinates."
    )
    assert "dynamical-org:mesh" not in document
    assert not collection.get_links("describedby")


def test_point_set_dimension_gets_no_grid_description(
    native_item: CatalogItem, native_root: xr.Dataset
) -> None:
    # Stations also carry 1-D latitude/longitude, but are not grid cells.
    stations = native_root.rename(cell="station")
    collection = CollectionInput.from_dataset(native_item, stations)
    assert collection.cube_dimensions["station"].description is None


def test_topology_without_face_dimension_is_rejected(
    native_item: CatalogItem, native_root: xr.Dataset, native_mesh: xr.Dataset
) -> None:
    del native_mesh["mesh"].attrs["face_dimension"]
    with pytest.raises(ValueError, match="mesh/mesh has no face_dimension"):
        CollectionInput.from_dataset(native_item, native_root, {"mesh": native_mesh})


def test_multiple_topology_groups_are_rejected_instead_of_silently_choosing_one(
    native_item: CatalogItem, native_root: xr.Dataset, native_mesh: xr.Dataset
) -> None:
    with pytest.raises(ValueError, match=r"[Mm]ore than one.*topology group"):
        CollectionInput.from_dataset(
            native_item, native_root, {"mesh": native_mesh, "second_mesh": native_mesh}
        )
