from __future__ import annotations

import pathlib
import urllib.error
import urllib.request

import icechunk
import pystac
import xarray as xr

from catalog import CATALOG_ITEMS, CatalogItem
from models import CollectionInput

ROOT_HREF = "https://stac.dynamical.org"
CATALOG_TITLE = "Dynamical.org STAC Catalog"


def _open_icechunk(item: CatalogItem) -> xr.Dataset:
    storage = icechunk.s3_storage(
        bucket=item.icechunk_bucket,
        prefix=item.icechunk_prefix,
        region=item.icechunk_region,
        anonymous=True,
    )
    repo = icechunk.Repository.open(storage)
    session = repo.readonly_session("main")
    return xr.open_zarr(session.store, consolidated=False, decode_timedelta=True)


def _verify_zarr_url(url: str) -> None:
    manifest_url = url.rstrip("/") + "/zarr.json"
    req = urllib.request.Request(
        manifest_url,
        method="HEAD",
        headers={"User-Agent": "dynamical-stac-generate/0.1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status >= 400:
                raise RuntimeError(f"{manifest_url} returned HTTP {resp.status}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to reach zarr URL {manifest_url}: {e}") from e


def _verify_read(ds: xr.Dataset) -> None:
    first_var = next(iter(ds.data_vars))
    sel = {name: 0 for name in ds[first_var].dims}
    value = ds[first_var].isel(sel).load().values
    assert value.size == 1, f"Expected scalar from {first_var}, got shape {value.shape}"


def _set_self_link_titles(catalog: pystac.Catalog) -> None:
    """Populate the `title` on each object's self link (pystac leaves it blank)."""
    for obj in (catalog, *catalog.get_children()):
        for link in obj.links:
            if link.rel == "self" and obj.title:
                link.title = obj.title


def generate(output_dir: pathlib.Path, root_href: str = ROOT_HREF) -> None:
    catalog = pystac.Catalog(
        id="dynamical-org",
        title=CATALOG_TITLE,
        description="Cloud-optimized weather and climate datasets from dynamical.org",
    )
    for item in CATALOG_ITEMS:
        print(f"{item.id}: opening icechunk store")
        ds = _open_icechunk(item)
        _verify_read(ds)
        print(f"{item.id}: verifying zarr URL")
        _verify_zarr_url(str(item.zarr_href))
        collection_input = CollectionInput.from_dataset(item, ds)
        catalog.add_child(collection_input.to_pystac_collection())

    catalog.normalize_hrefs(root_href)
    _set_self_link_titles(catalog)
    catalog.validate_all()
    catalog.save(
        catalog_type=pystac.CatalogType.ABSOLUTE_PUBLISHED,
        dest_href=str(output_dir),
    )
