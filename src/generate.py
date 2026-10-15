from __future__ import annotations

import concurrent.futures
import datetime as dt
import json
import os
import pathlib
import tempfile
from typing import Any

import gribberish.zarr  # noqa: F401 -- registers the GribberishCodec used by virtual datasets
import icechunk
import pystac
import xarray as xr
import zarr

from catalog import CATALOG_ITEMS, CatalogItem, url_scheme
from environments import STAC_ENVIRONMENTS, StacEnvironment, stac_environment
from models import CollectionInput
from sidecars import (
    CATALOG_AGENTS,
    CATALOG_README,
    collection_agents,
    collection_readme,
    sidecar_links,
)

CATALOG_TITLE = "dynamical.org STAC Catalog"
# The registry and STAC Browser show it beside the catalog; stac-js rejects SVG.
CATALOG_ICON_URL = (
    "https://assets.dynamical.org/identity/logo/icon/icon-padded-256-on-white.png"
)


def _select_items(items: list[CatalogItem], *, environment: str) -> list[CatalogItem]:
    """Select only items explicitly published in this environment."""
    return [item for item in items if environment in item.environments]


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


Loaded = dict[str, tuple[xr.Dataset, dict[str, xr.Dataset]]]


def _updated(document: dict[str, Any], committed: pathlib.Path, now: str) -> str:
    """The committed file's `updated` if nothing else in `document` changed, else `now`.

    Portolan mirrors record their last sync from the source in `updated`. A
    regeneration syncs something only when the metadata it writes differs, so an
    unchanged file keeps its stamp and the committed trees stay reproducible.
    """
    try:
        previous = json.loads(committed.read_text())
    except FileNotFoundError:
        return now
    stamp = previous.pop("updated", None)
    return stamp if stamp is not None and previous == document else now


def _root_document(
    catalog: pystac.Catalog, publication: StacEnvironment, root_href: str
) -> dict[str, Any]:
    root = catalog.to_dict()
    if publication.client_versions is not None:
        # Versioned roots are served from their own filename.
        for link in root["links"]:
            if link["rel"] == "self":
                link["href"] = f"{root_href}/{publication.root_filename}"
    return root


def _stamp_updated(
    catalog: pystac.Catalog,
    publication: StacEnvironment,
    root_href: str,
    previous_dir: pathlib.Path,
    now: str,
) -> None:
    """Set `updated` on each collection, and on the root as the latest of them."""
    stamps = []
    for child in catalog.get_children():
        stamp = _updated(
            child.to_dict(), previous_dir / child.id / "collection.json", now
        )
        child.extra_fields["updated"] = stamp
        stamps.append(stamp)
    own = _updated(
        _root_document(catalog, publication, root_href),
        previous_dir / publication.root_filename,
        now,
    )
    # One RFC 3339 format throughout, so the latest sorts last.
    catalog.extra_fields["updated"] = max([own, *stamps])


def _write_sidecars(
    catalog: pystac.Catalog, output_dir: pathlib.Path, *, collections: bool
) -> None:
    (output_dir / "README.md").write_text(CATALOG_README)
    (output_dir / "AGENTS.md").write_text(CATALOG_AGENTS)
    if not collections:
        return
    for child in catalog.get_children():
        assert isinstance(child, pystac.Collection)
        (output_dir / child.id / "README.md").write_text(collection_readme(child))
        (output_dir / child.id / "AGENTS.md").write_text(collection_agents(child))


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
    root_href: str | None = None,
    environment: str = "production",
    loaded: Loaded | None = None,
    *,
    previous_dir: pathlib.Path | None = None,
    now: dt.datetime | None = None,
) -> None:
    """Write one environment's catalog, optionally reusing loaded stores.

    `updated` stamps come from the files in `previous_dir` (default
    `output_dir`) where nothing else changed, and are `now` elsewhere.
    """
    publication = stac_environment(environment)
    if root_href is None:
        root_href = os.environ.get("STAC_ROOT_HREF", publication.root_href)
    if now is None:
        now = dt.datetime.now(dt.UTC)
    catalog = pystac.Catalog(
        id="dynamical-org",
        title=CATALOG_TITLE,
        description="Cloud-optimized weather and climate datasets from dynamical.org",
    )
    catalog.add_link(
        pystac.Link(
            rel="icon",
            target=CATALOG_ICON_URL,
            media_type="image/png",
            title="dynamical.org",
        )
    )
    for link in sidecar_links():
        catalog.add_link(link)

    items = _select_items(CATALOG_ITEMS, environment=environment)
    if loaded is None:
        loaded = _load_datasets(items)

    for item in items:
        ds, subgroups = loaded[item.id]
        collection_input = CollectionInput.from_dataset(item, ds, subgroups)
        catalog.add_child(collection_input.to_pystac_collection())

    catalog.normalize_hrefs(root_href)
    _set_self_link_titles(catalog)
    _stamp_updated(
        catalog,
        publication,
        root_href,
        output_dir if previous_dir is None else previous_dir,
        now.astimezone(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    catalog.validate_all()
    if publication.client_versions is None:
        catalog.save(
            catalog_type=pystac.CatalogType.ABSOLUTE_PUBLISHED,
            dest_href=str(output_dir),
        )
    else:
        # Versioned environments publish an additional root only. Their child
        # links reuse canonical production collections; never rewrite the leaves.
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / publication.root_filename).write_text(
            json.dumps(_root_document(catalog, publication, root_href), indent=2)
        )
    _write_sidecars(
        catalog, output_dir, collections=publication.client_versions is None
    )


def generate_environments(
    parent_dir: pathlib.Path, previous_parent: pathlib.Path | None = None
) -> None:
    """Write every environment's tree under `parent_dir`, opening each store once.

    Catalogs are built beside their destination and swapped in only once all of
    them validated, so a store that fails to open leaves the committed trees
    untouched, and a collection that left an environment leaves its tree too.
    A failure during the swap itself is rolled back (`_swap_in`); a killed
    process is not, and `git checkout` is the recovery for that. The caller's
    STAC_* environment is ignored: publications use `STAC_ENVIRONMENTS`.
    Unchanged files keep the `updated` stamps of the trees under
    `previous_parent` (default `parent_dir`); every other stamp is one shared now.
    """
    loaded = _load_datasets(CATALOG_ITEMS)
    now = dt.datetime.now(dt.UTC)
    if previous_parent is None:
        previous_parent = parent_dir
    with tempfile.TemporaryDirectory(dir=parent_dir, prefix=".stac-build-") as build:
        for environment in STAC_ENVIRONMENTS:
            generate(
                pathlib.Path(build) / environment.directory,
                root_href=environment.root_href,
                environment=environment.name,
                loaded=loaded,
                previous_dir=previous_parent / environment.directory,
                now=now,
            )
        _swap_in(
            pathlib.Path(build),
            parent_dir,
            list(
                dict.fromkeys(
                    environment.directory for environment in STAC_ENVIRONMENTS
                )
            ),
        )


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
