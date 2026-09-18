from __future__ import annotations

import concurrent.futures
import json
import os
import pathlib
import tempfile
from typing import NamedTuple

import gribberish.zarr  # noqa: F401 -- registers the GribberishCodec used by virtual datasets
import icechunk
import pystac
import xarray as xr
import zarr

from catalog import CATALOG_ITEMS, LEGACY_CLIENT_RANGES, CatalogItem, url_scheme
from models import CollectionInput

ROOT_HREF = os.environ.get("STAC_ROOT_HREF", "https://stac.dynamical.org")
CATALOG_TITLE = "dynamical.org STAC Catalog"

# Staging items (CatalogItem.staging=True) are unreleased datasets: excluded
# from the production catalog and published only to stac-staging. The staging
# deploy sets STAC_INCLUDE_STAGING=1; everything else (prod, local, tests)
# leaves it unset and gets the production catalog.
INCLUDE_STAGING = os.environ.get("STAC_INCLUDE_STAGING") == "1"

# Test items (CatalogItem.test=True) are synthetic fixtures read by
# dynamical-catalog's integration tests: excluded from production *and* staging,
# published only to stac-test. The test deploy sets STAC_INCLUDE_TEST=1 (plus
# STAC_INCLUDE_STAGING=1, making stac-test a superset of stac-staging).
INCLUDE_TEST = os.environ.get("STAC_INCLUDE_TEST") == "1"


def _select_items(
    items: list[CatalogItem], *, include_staging: bool, include_test: bool
) -> list[CatalogItem]:
    """Filter the catalog down to one tier.

    Production excludes staging and test items; the staging catalog adds the
    staging items; the test catalog adds both.
    """
    return [
        item
        for item in items
        if (include_staging or not item.staging) and (include_test or not item.test)
    ]


def _container_credentials(
    prefix: str,
) -> (
    icechunk.S3Credentials.Anonymous
    | icechunk.GcsCredentials.Anonymous
    | icechunk.AzureCredentials.Anonymous
    | icechunk.Credentials.HttpAccess
):
    """Anonymous virtual chunk container credentials for ``prefix``'s backend."""
    scheme = url_scheme(prefix)
    if scheme == "s3":
        return icechunk.s3_anonymous_credentials()
    if scheme == "az":
        return icechunk.azure_anonymous_credentials()
    if scheme == "https":
        return icechunk.Credentials.HttpAccess()
    return icechunk.gcs_credentials(anonymous=True)


def _storage(item: CatalogItem) -> icechunk.Storage:
    """Anonymous read-only storage for the item's repository, by href scheme."""
    if item.icechunk_scheme == "https":
        # `icechunk_https_href` is the href with any trailing slash stripped,
        # which `http_storage` requires.
        return icechunk.http_storage(base_url=item.icechunk_https_href)
    if item.icechunk_scheme == "gs":
        return icechunk.gcs_storage(
            bucket=item.icechunk_bucket,
            prefix=item.icechunk_prefix,
            anonymous=True,
        )
    if item.icechunk_scheme == "az":
        # Azure's container is the href's netloc; the storage account that owns
        # it is carried separately in `icechunk_account`.
        assert item.icechunk_account is not None  # _account_matches_scheme
        return icechunk.azure_storage(
            account=item.icechunk_account,
            container=item.icechunk_container,
            prefix=item.icechunk_prefix,
            anonymous=True,
        )
    return icechunk.s3_storage(
        bucket=item.icechunk_bucket,
        prefix=item.icechunk_prefix,
        region=item.icechunk_region,
        anonymous=True,
    )


def _open_icechunk(item: CatalogItem) -> tuple[xr.Dataset, dict[str, xr.Dataset]]:
    """Open the store's root group plus any nested child groups.

    Child groups (e.g. the HRRR spatial dataset's ``pressure_level`` /
    ``model_level`` vertical groups) are opened separately and returned keyed by
    group name; ``from_dataset`` flattens their variables into the collection.
    Single-group stores yield an empty dict.
    """
    storage = _storage(item)
    authorize = (
        icechunk.containers_credentials(
            {
                prefix: _container_credentials(prefix)
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


def legacy_root(
    root: dict[str, object], root_filename: str, excluded_ids: set[str]
) -> dict[str, object]:
    """`root` as served to a legacy client range: its own `self`, fewer children.

    The `root` link still names `catalog.json`, and the collections are shared
    rather than copied, so their `root` and `parent` links stay true.
    """
    links = []
    for link in root["links"]:  # type: ignore[attr-defined]
        if link["rel"] == "child":
            if pathlib.PurePosixPath(link["href"]).parent.name not in excluded_ids:
                links.append(link)
        elif link["rel"] == "self":
            href = link["href"].rsplit("/", 1)[0] + f"/{root_filename}"
            links.append({**link, "href": href})
        else:
            links.append(link)
    return {**root, "links": links}


def _write_legacy_roots(output_dir: pathlib.Path, items: list[CatalogItem]) -> None:
    root = json.loads((output_dir / "catalog.json").read_text())
    for legacy_range in LEGACY_CLIENT_RANGES:
        excluded_ids = {
            item.id for item in items if legacy_range.name in item.exclude_from
        }
        legacy = legacy_root(root, legacy_range.root_filename, excluded_ids)
        (output_dir / legacy_range.root_filename).write_text(
            json.dumps(legacy, indent=2)
        )


Loaded = dict[str, tuple[xr.Dataset, dict[str, xr.Dataset]]]


def _load_datasets(items: list[CatalogItem]) -> Loaded:
    """Open every item's store, keyed by item id."""

    def _load(item: CatalogItem) -> tuple[xr.Dataset, dict[str, xr.Dataset]]:
        print(f"{item.id}: opening icechunk store")  # noqa: T201
        ds, subgroups = _open_icechunk(item)
        _verify_read(ds)
        return ds, subgroups

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max(1, len(items))
    ) as executor:
        return dict(
            zip((item.id for item in items), executor.map(_load, items), strict=True)
        )


def generate(
    output_dir: pathlib.Path,
    root_href: str = ROOT_HREF,
    include_staging: bool = INCLUDE_STAGING,
    include_test: bool = INCLUDE_TEST,
    loaded: Loaded | None = None,
) -> None:
    """Write one tier's catalog. `loaded` reuses stores opened for another tier."""
    catalog = pystac.Catalog(
        id="dynamical-org",
        title=CATALOG_TITLE,
        description="Cloud-optimized weather and climate datasets from dynamical.org",
    )

    items = _select_items(
        CATALOG_ITEMS, include_staging=include_staging, include_test=include_test
    )
    if loaded is None:
        loaded = _load_datasets(items)

    for item in items:
        ds, subgroups = loaded[item.id]
        collection_input = CollectionInput.from_dataset(item, ds, subgroups)
        catalog.add_child(collection_input.to_pystac_collection())

    catalog.normalize_hrefs(root_href)
    _set_self_link_titles(catalog)
    catalog.validate_all()
    catalog.save(
        catalog_type=pystac.CatalogType.ABSOLUTE_PUBLISHED,
        dest_href=str(output_dir),
    )
    _write_legacy_roots(output_dir, items)


class Tier(NamedTuple):
    """One published catalog: its committed directory, which is also its R2
    bucket name, and the host baked into every link."""

    directory: str
    root_href: str
    include_staging: bool
    include_test: bool


# Every tier is committed, so a change to any of them is reviewed as a diff and
# each upload workflow ships exactly the tree that was merged.
TIERS = (
    Tier("stac", "https://stac.dynamical.org", False, False),
    Tier("stac-staging", "https://stac-staging.dynamical.org", True, False),
    Tier("stac-test", "https://stac-test.dynamical.org", True, True),
)


def generate_tiers(parent_dir: pathlib.Path) -> None:
    """Write every tier's tree under `parent_dir`, opening each store once.

    Tiers are built beside their destination and swapped in only once all of
    them validated, so a store that fails to open leaves the committed trees
    untouched, and a collection that left a tier leaves its tree too. A failure
    during the swap itself is rolled back (`_swap_in`); a killed process is not,
    and `git checkout` is the recovery for that. The
    caller's STAC_* environment is ignored: each tier is what `TIERS` says.
    """
    loaded = _load_datasets(CATALOG_ITEMS)
    with tempfile.TemporaryDirectory(dir=parent_dir, prefix=".stac-build-") as build:
        for tier in TIERS:
            generate(
                pathlib.Path(build) / tier.directory,
                root_href=tier.root_href,
                include_staging=tier.include_staging,
                include_test=tier.include_test,
                loaded=loaded,
            )
        _swap_in(pathlib.Path(build), parent_dir, [tier.directory for tier in TIERS])


def _swap_in(build: pathlib.Path, parent_dir: pathlib.Path, names: list[str]) -> None:
    """Replace each `parent_dir/name` with `build/name`, or put them all back.

    Both sit on one filesystem, so every step is a rename. The old trees are kept
    inside `build` until every new one is in place; if a rename fails, the new
    trees already installed are moved out again and the old ones restored.
    """
    replaced: list[str] = []
    try:
        for name in names:
            if (parent_dir / name).exists():
                (parent_dir / name).rename(build / f"{name}.old")
            replaced.append(name)
            (build / name).rename(parent_dir / name)
    except BaseException:
        for name in replaced:
            if (parent_dir / name).exists():
                (parent_dir / name).rename(build / f"{name}.failed")
            if (build / f"{name}.old").exists():
                (build / f"{name}.old").rename(parent_dir / name)
        raise
