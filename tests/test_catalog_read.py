"""Integration tests: open every icechunk in the catalog and verify notebook URLs."""

from __future__ import annotations

import math
import pathlib
import urllib.error
import urllib.request

import pytest

from catalog import _COLLECTION_IDS


def _point_value(ds: object, name: str) -> object:
    da = ds[name]  # type: ignore[index]
    return da.isel(dict.fromkeys(da.dims, 0)).load().item()


@pytest.fixture
def dynamical_catalog_fixture(
    served_catalog: tuple[pathlib.Path, str],
) -> object:
    dynamical_catalog = pytest.importorskip("dynamical_catalog")
    from dynamical_catalog import _stac  # noqa: PLC0415

    _, root_url = served_catalog
    _stac.STAC_CATALOG_URL = f"{root_url}/catalog.json"
    _stac.clear_cache()
    return dynamical_catalog


@pytest.mark.integration
@pytest.mark.parametrize("collection_id", _COLLECTION_IDS)
def test_every_icechunk_opens_and_reads(
    dynamical_catalog_fixture: object,
    collection_id: str,
) -> None:
    ds = dynamical_catalog_fixture.open(collection_id)  # type: ignore[attr-defined]
    first_var = next(iter(ds.data_vars))
    value = _point_value(ds, first_var)
    # NaN is fine (sparse/unobserved cells), but the read must return a number
    assert isinstance(value, float | int), f"{collection_id}.{first_var} -> {value!r}"
    if isinstance(value, float):
        assert not math.isinf(value), f"{collection_id}.{first_var} is inf"


@pytest.mark.integration
def test_noaa_gfs_forecast_temperature_2m_reads(
    dynamical_catalog_fixture: object,
) -> None:
    ds = dynamical_catalog_fixture.open("noaa-gfs-forecast")  # type: ignore[attr-defined]
    assert "temperature_2m" in ds.data_vars
    value = (
        ds.temperature_2m.isel(init_time=0, lead_time=0, latitude=0, longitude=0)
        .load()
        .item()
    )
    assert isinstance(value, float)


@pytest.mark.integration
@pytest.mark.parametrize("collection_id", _COLLECTION_IDS)
def test_notebook_url_exists(collection_id: str) -> None:
    url = f"https://github.com/dynamical-org/notebooks/blob/main/{collection_id}.ipynb"
    req = urllib.request.Request(url, method="HEAD")  # noqa: S310
    req.add_header("User-Agent", "dynamical-stac-tests")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
            status = resp.status
    except urllib.error.HTTPError as e:
        status = e.code
    assert status == 200, f"{url} returned {status}"
