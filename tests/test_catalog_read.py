"""Integration tests: open every icechunk in the catalog and verify notebook URLs.

The notebook check covers every URL the catalog declares; a staging item may
declare none at all, and those simply drop out of the parametrization.
"""

from __future__ import annotations

import math
import urllib.error
import urllib.request
from concurrent.futures import Future, ThreadPoolExecutor

import pytest

from catalog import _COLLECTION_IDS, CATALOG_ITEMS

# Every notebook declared by any item — staging items included. Items with no
# notebooks (only possible while staging, see
# `CatalogItem._production_items_have_notebooks`) contribute nothing here, so
# this covers exactly the notebook URLs the catalog actually publishes.
_NOTEBOOK_SLUGS = sorted(
    {notebook.slug for item in CATALOG_ITEMS for notebook in item.notebooks}
)


def _point_value(ds: object, name: str) -> object:
    da = ds[name]  # type: ignore[index]
    return da.isel(dict.fromkeys(da.dims, 0)).load().item()


def _read_collection(
    dynamical_catalog: object, collection_id: str
) -> tuple[str, object]:
    ds = dynamical_catalog.open(collection_id)  # type: ignore[attr-defined]
    first_var = next(iter(ds.data_vars))
    return first_var, _point_value(ds, first_var)


@pytest.fixture(scope="module")
def collection_reads(
    dynamical_catalog_fixture: object,
) -> dict[str, Future[tuple[str, object]]]:
    """Prefetch every module collection read with four workers, even under -k.

    Like URL prefetch, selection still runs all cases when this fixture is used.
    Exceptions stay in futures for the original parametrized tests to report.
    """
    # served_catalog, through dynamical_catalog_fixture, has already read every
    # dataset and resolved its codecs. Warm the client root before threading.
    dynamical_catalog_fixture.list()  # type: ignore[attr-defined]
    with ThreadPoolExecutor(max_workers=4) as executor:
        return {
            collection_id: executor.submit(
                _read_collection, dynamical_catalog_fixture, collection_id
            )
            for collection_id in _COLLECTION_IDS
        }


@pytest.mark.integration
@pytest.mark.parametrize("collection_id", _COLLECTION_IDS)
def test_every_icechunk_opens_and_reads(
    dynamical_catalog_fixture: object,
    collection_id: str,
    collection_reads: dict[str, Future[tuple[str, object]]],
) -> None:
    first_var, value = collection_reads[collection_id].result()
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


def _notebook_url(notebook_slug: str) -> str:
    # Use raw.githubusercontent.com so 404s actually return 404 — the
    # github.com/<repo>/blob/<ref>/<path> page always returns 200 (the SPA
    # renders "Page not found" client-side), which makes it useless for
    # existence checks.
    return (
        "https://raw.githubusercontent.com/dynamical-org/notebooks"
        f"/main/{notebook_slug}.ipynb"
    )


def _notebook_status(url: str) -> int:
    req = urllib.request.Request(url, method="HEAD")  # noqa: S310
    req.add_header("User-Agent", "dynamical-stac-tests")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


@pytest.fixture(scope="module")
def notebook_statuses() -> dict[str, Future[int]]:
    """Prefetch this module's URLs with bounded concurrency, even under -k.

    Keep exceptions in futures so failures remain attached to individual tests.
    Only notebook tests request this fixture; store reads use a separate pool.
    """
    with ThreadPoolExecutor(max_workers=8) as executor:
        return {
            slug: executor.submit(_notebook_status, _notebook_url(slug))
            for slug in _NOTEBOOK_SLUGS
        }


@pytest.mark.integration
@pytest.mark.parametrize("notebook_slug", _NOTEBOOK_SLUGS)
def test_notebook_url_exists(
    notebook_slug: str, notebook_statuses: dict[str, Future[int]]
) -> None:
    url = _notebook_url(notebook_slug)
    status = notebook_statuses[notebook_slug].result()
    assert status == 200, f"{url} returned {status}"
