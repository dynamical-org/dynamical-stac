"""Integration test: vertical dimension coordinates follow a consistent CF schema.

Variables on a vertical level live in a ``pressure_level`` or ``model_level``
group. Their dimension coordinate must, across every dataset in the catalog:

* carry ``axis="Z"``;
* be named ``pressure_level`` or ``model_level`` — and nothing else may claim
  ``axis="Z"``; and
* expose the same CF descriptive attributes (``long_name``, ``standard_name``,
  ``units``, ``axis``, ``positive``) wherever the name appears, so a consumer
  sees one consistent contract for vertical levels catalog-wide.

These attributes live in the Zarr coordinate metadata, not in the rendered
STAC (``_dim_entry`` only emits ``axis`` for the spatial x/y dimensions), so we
open the stores directly — hence the ``integration`` mark.

The consistency check compares occurrences against each other rather than a
hardcoded expectation, so it enforces uniformity without pinning the exact
attribute values (which are owned by the reformatters that write the stores).
"""

from __future__ import annotations

import concurrent.futures
from typing import NamedTuple

import pytest

from catalog import CATALOG_ITEMS, CatalogItem
from generate import _open_icechunk

# Dimension-coordinate names that represent a vertical level. Every
# ``axis="Z"`` coordinate must use one of these, and each name must present the
# same CF attributes everywhere it appears.
VERTICAL_DIM_NAMES = frozenset({"pressure_level", "model_level"})

# CF descriptive attributes that must be identical across datasets. Value-derived
# attributes (e.g. ``statistics_approximate``) legitimately vary per dataset and
# are deliberately excluded.
_CF_ATTR_KEYS = ("long_name", "standard_name", "units", "axis", "positive")


class _DimCoord(NamedTuple):
    label: str  # "<collection-id>" or "<collection-id>/<group>"
    name: str
    attrs: dict[str, object]


def _cf_attrs(attrs: dict[str, object]) -> dict[str, object | None]:
    return {key: attrs.get(key) for key in _CF_ATTR_KEYS}


@pytest.fixture(scope="module")
def dimension_coords() -> list[_DimCoord]:
    """Every dimension coordinate across all datasets (root + nested groups)."""

    def load(item: CatalogItem) -> list[_DimCoord]:
        root, subgroups = _open_icechunk(item)
        datasets = [(item.id, root)] + [
            (f"{item.id}/{group}", ds) for group, ds in subgroups.items()
        ]
        return [
            _DimCoord(label, name, dict(ds[name].attrs))
            for label, ds in datasets
            for name in ds.dims
            if name in ds.coords
        ]

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max(1, len(CATALOG_ITEMS))
    ) as executor:
        return [
            coord for coords in executor.map(load, CATALOG_ITEMS) for coord in coords
        ]


@pytest.mark.integration
def test_vertical_dim_coords_have_axis_z(dimension_coords: list[_DimCoord]) -> None:
    offenders = [
        coord
        for coord in dimension_coords
        if coord.name in VERTICAL_DIM_NAMES and coord.attrs.get("axis") != "Z"
    ]
    assert not offenders, (
        "vertical dimension coordinates must carry axis='Z': "
        + ", ".join(
            f"{coord.label}:{coord.name} axis={coord.attrs.get('axis')!r}"
            for coord in offenders
        )
    )


@pytest.mark.integration
def test_axis_z_coords_use_known_vertical_names(
    dimension_coords: list[_DimCoord],
) -> None:
    offenders = [
        coord
        for coord in dimension_coords
        if coord.attrs.get("axis") == "Z" and coord.name not in VERTICAL_DIM_NAMES
    ]
    assert not offenders, (
        "axis='Z' is reserved for pressure_level/model_level dimension "
        "coordinates; rename or reclassify: "
        + ", ".join(f"{coord.label}:{coord.name}" for coord in offenders)
    )


@pytest.mark.integration
@pytest.mark.parametrize("name", sorted(VERTICAL_DIM_NAMES))
def test_vertical_dim_coord_attrs_consistent(
    dimension_coords: list[_DimCoord], name: str
) -> None:
    by_attrs: dict[tuple[tuple[str, object | None], ...], list[str]] = {}
    for coord in dimension_coords:
        if coord.name == name:
            key = tuple(sorted(_cf_attrs(coord.attrs).items()))
            by_attrs.setdefault(key, []).append(coord.label)
    assert len(by_attrs) <= 1, (
        f"{name} exposes inconsistent CF attributes across datasets: "
        + "; ".join(f"{dict(key)} in {labels}" for key, labels in by_attrs.items())
    )
