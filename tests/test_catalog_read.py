"""Integration test: use dynamical-catalog to open a dataset from the generated STAC and read a value."""

from __future__ import annotations

import pathlib

import pytest


@pytest.mark.integration
def test_open_and_read_via_dynamical_catalog(
    served_catalog: tuple[pathlib.Path, str],
) -> None:
    dynamical_catalog = pytest.importorskip("dynamical_catalog")
    from dynamical_catalog import _stac  # noqa: PLC0415

    _, root_url = served_catalog
    _stac.STAC_CATALOG_URL = f"{root_url}/catalog.json"
    _stac.clear_cache()

    ds = dynamical_catalog.open("noaa-gfs-forecast")

    assert "temperature_2m" in ds.data_vars
    value = (
        ds.temperature_2m.isel(init_time=0, lead_time=0, latitude=0, longitude=0)
        .load()
        .item()
    )
    assert isinstance(value, float)
