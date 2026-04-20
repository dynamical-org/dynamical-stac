from __future__ import annotations

import pathlib

import pystac

from datasets import load_collections

ROOT_HREF = "https://stac.dynamical.org"


def generate(output_dir: pathlib.Path, root_href: str = ROOT_HREF) -> None:
    catalog = pystac.Catalog(
        id="dynamical-org",
        description="Cloud-optimized weather and climate datasets from dynamical.org",
    )
    for collection in load_collections():
        catalog.add_child(collection)

    catalog.normalize_hrefs(root_href)
    catalog.validate_all()
    catalog.save(
        catalog_type=pystac.CatalogType.ABSOLUTE_PUBLISHED,
        dest_href=str(output_dir),
    )
