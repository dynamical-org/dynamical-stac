from __future__ import annotations

import pathlib

import icechunk
import pystac
import xarray as xr

from catalog import CATALOG_ITEMS, CatalogItem
from models import CollectionInput

ROOT_HREF = "https://stac.dynamical.org"
CATALOG_TITLE = "dynamical.org STAC Catalog"


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


def _verify_read(ds: xr.Dataset) -> None:
    first_var = next(iter(ds.data_vars))
    sel = dict.fromkeys(ds[first_var].dims, 0)
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
        print(f"{item.id}: opening icechunk store")  # noqa: T201
        ds = _open_icechunk(item)
        _verify_read(ds)
        collection_input = CollectionInput.from_dataset(item, ds)
        catalog.add_child(collection_input.to_pystac_collection())

    catalog.normalize_hrefs(root_href)
    _set_self_link_titles(catalog)
    catalog.validate_all()
    catalog.save(
        catalog_type=pystac.CatalogType.ABSOLUTE_PUBLISHED,
        dest_href=str(output_dir),
    )
