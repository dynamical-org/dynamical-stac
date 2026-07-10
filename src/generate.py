from __future__ import annotations

import concurrent.futures
import os
import pathlib

import gribberish.zarr  # noqa: F401 -- registers the GribberishCodec used by virtual datasets
import icechunk
import pystac
import xarray as xr
import zarr

from catalog import CATALOG_ITEMS, CatalogItem
from models import CollectionInput

ROOT_HREF = os.environ.get("STAC_ROOT_HREF", "https://stac.dynamical.org")
CATALOG_TITLE = "dynamical.org STAC Catalog"

# Staging items (CatalogItem.staging=True) are unreleased datasets: excluded
# from the production catalog and published only to stac-staging. The staging
# deploy sets STAC_INCLUDE_STAGING=1; everything else (prod, local, tests)
# leaves it unset and gets the production catalog.
INCLUDE_STAGING = os.environ.get("STAC_INCLUDE_STAGING") == "1"


def _select_items(
    items: list[CatalogItem], *, include_staging: bool
) -> list[CatalogItem]:
    """Production excludes staging items; the staging catalog includes them."""
    return [item for item in items if include_staging or not item.staging]


def _open_icechunk(item: CatalogItem) -> tuple[xr.Dataset, dict[str, xr.Dataset]]:
    """Open the store's root group plus any nested child groups.

    The root dataset is opened exactly as before, so existing single-group
    collections regenerate byte-for-byte. Child groups (e.g. the HRRR spatial
    dataset's ``pressure_level`` / ``model_level`` vertical groups) are opened
    separately and returned keyed by group name; ``from_dataset`` flattens their
    variables into the collection. Single-group stores yield an empty dict.
    """
    storage = icechunk.s3_storage(
        bucket=item.icechunk_bucket,
        prefix=item.icechunk_prefix,
        region=item.icechunk_region,
        anonymous=True,
    )
    authorize = (
        icechunk.containers_credentials(
            {
                prefix: icechunk.s3_anonymous_credentials()
                for prefix in item.virtual_chunk_container_prefixes
            }
        )
        if item.virtual_chunk_container_prefixes
        else None
    )
    repo = icechunk.Repository.open(storage, authorize_virtual_chunk_access=authorize)
    session = repo.readonly_session("main")
    store = session.store
    root = xr.open_zarr(store, consolidated=False, decode_timedelta=True)
    child_names = [name for name, _ in zarr.open_group(store, mode="r").groups()]
    subgroups = {
        name: xr.open_zarr(store, group=name, consolidated=False, decode_timedelta=True)
        for name in child_names
    }
    return root, subgroups


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


def generate(
    output_dir: pathlib.Path,
    root_href: str = ROOT_HREF,
    include_staging: bool = INCLUDE_STAGING,
) -> None:
    catalog = pystac.Catalog(
        id="dynamical-org",
        title=CATALOG_TITLE,
        description="Cloud-optimized weather and climate datasets from dynamical.org",
    )

    items = _select_items(CATALOG_ITEMS, include_staging=include_staging)

    def _load(
        item: CatalogItem,
    ) -> tuple[CatalogItem, xr.Dataset, dict[str, xr.Dataset]]:
        print(f"{item.id}: opening icechunk store")  # noqa: T201
        ds, subgroups = _open_icechunk(item)
        _verify_read(ds)
        return item, ds, subgroups

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max(1, len(items))
    ) as executor:
        for item, ds, subgroups in executor.map(_load, items):
            collection_input = CollectionInput.from_dataset(item, ds, subgroups)
            catalog.add_child(collection_input.to_pystac_collection())

    catalog.normalize_hrefs(root_href)
    _set_self_link_titles(catalog)
    catalog.validate_all()
    catalog.save(
        catalog_type=pystac.CatalogType.ABSOLUTE_PUBLISHED,
        dest_href=str(output_dir),
    )
