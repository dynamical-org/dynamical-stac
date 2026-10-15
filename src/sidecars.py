"""README.md and AGENTS.md beside every catalog and collection.

The Portolan profile requires both files next to each `catalog.json` and
`collection.json`, linked as `describedby` and `agents`. Everything in them is
rendered from the STAC object they sit beside, so they never say something the
JSON does not.
"""

from __future__ import annotations

import json
from typing import Any

import pystac

PROMPT_URL = "https://dynamical.org/prompt.md"
_PROMPT_LINE = f"Read {PROMPT_URL} for context about working with dynamical.org data."


def sidecar_links() -> list[pystac.Link]:
    """The `describedby` and `agents` links to the files beside an object."""
    return [
        pystac.Link(
            rel="describedby",
            target="./README.md",
            media_type="text/markdown",
            title="README",
        ),
        pystac.Link(
            rel="agents",
            target="./AGENTS.md",
            media_type="text/markdown",
            title="Notes for agents",
        ),
    ]


CATALOG_README = """\
# dynamical.org STAC Catalog

Cloud-optimized weather and climate datasets from dynamical.org. Each child
collection is one dataset, stored as an Icechunk repository of Zarr arrays
that anyone can read without credentials.

## License

Each collection states its license in its `license` field and in its own
README.md.

## Provenance

Most collections reformat data that other organizations produce. Each
collection names its producer first in `providers`, with dynamical.org last as
host, and links the original source with `rel: via` when it is elsewhere.

## Links

- Website: https://dynamical.org/
- Dataset catalog: https://dynamical.org/catalog/
"""

CATALOG_AGENTS = f"""\
# dynamical.org STAC Catalog: notes for agents

{_PROMPT_LINE}

- Each child collection is one dataset. Its AGENTS.md lists the repository
  URLs, dimensions and variables, and its `examples` field holds runnable
  Python.
- With the `dynamical-catalog` package, open a dataset by its collection id:
  `dynamical_catalog.open("<collection id>")`.
- Without it, open the collection's `icechunk-https` asset with
  `icechunk.http_storage` and read it with `xarray.open_zarr`.
- All data is public. No credentials are needed.
"""


def _self_href(collection: pystac.Collection) -> str:
    href = collection.get_self_href()
    assert href is not None  # set by normalize_hrefs before rendering
    return href


def _links(collection: pystac.Collection, rel: str) -> list[pystac.Link]:
    return [link for link in collection.links if link.rel == rel]


def collection_readme(collection: pystac.Collection) -> str:
    """Title, description, license and provenance, as the profile requires."""
    fields = collection.extra_fields
    providers = collection.providers or []
    hosts = [p for p in providers if pystac.ProviderRole.HOST in (p.roles or [])]
    producers = [
        p
        for p in providers
        if pystac.ProviderRole.PRODUCER in (p.roles or []) and p not in hosts
    ]
    lines = [
        f"# {collection.title}",
        "",
        fields["description_summary"],
        "",
        fields["description_model"],
        "",
        "## License",
        "",
        f"{collection.license}. {fields['attribution']}",
        "",
        *(f"- [{link.title}]({link.href})" for link in _links(collection, "license")),
        "",
        "## Provenance",
        "",
    ]
    if producers:
        lines += [
            "Produced by "
            + ", ".join(f"[{p.name}]({p.url})" for p in producers)
            + ". Processed and hosted by "
            + ", ".join(f"[{p.name}]({p.url})" for p in hosts)
            + ".",
        ]
    else:
        lines += [
            "Produced, processed and hosted by "
            + ", ".join(f"[{p.name}]({p.url})" for p in hosts)
            + ".",
        ]
    lines += [
        *(
            f"Source: [{link.title}]({link.href})."
            for link in _links(collection, "via")
        ),
        "",
        "## Details",
        "",
        fields["description_details"],
        "",
        "## Links",
        "",
        f"- STAC collection: {_self_href(collection)}",
        *(f"- {link.title}: {link.href}" for link in _links(collection, "about")),
    ]
    return "\n".join(lines) + "\n"


def _extent(extent: list[Any] | None) -> str:
    if not extent:
        return ""
    return " to ".join("open" if value is None else str(value) for value in extent)


def collection_agents(collection: pystac.Collection) -> str:
    """How to open the dataset, and the dimensions and variables it holds."""
    fields = collection.extra_fields
    lines = [
        f"# {collection.title}: notes for agents",
        "",
        _PROMPT_LINE,
        "",
        f"- Collection id: `{collection.id}`",
        f"- STAC collection: {_self_href(collection)}",
        f"- Dataset version: {fields['version']}",
        "",
        "## Access",
        "",
        "All data is public. No credentials are needed.",
        "",
        "| asset | href |",
        "|---|---|",
        *(f"| `{key}` | `{asset.href}` |" for key, asset in collection.assets.items()),
    ]
    icechunk = collection.assets["icechunk"].extra_fields
    if "xarray:storage_options" in icechunk:
        lines += [
            "",
            (
                "The `icechunk` asset's `xarray:storage_options` are "
                f"`{json.dumps(icechunk['xarray:storage_options'])}`."
            ),
        ]
    containers = icechunk.get("icechunk:virtual_chunk_containers", [])
    if containers:
        lines += [
            "",
            (
                "The repository references chunks in these upstream locations,"
                " which are read anonymously:"
            ),
            "",
            *(f"- `{container['url_prefix']}`" for container in containers),
        ]
    lines += ["", "## Examples"]
    for example in fields["examples"]:
        lines += ["", f"### {example['title']}"]
        for variant in example["variants"]:
            lines += [
                "",
                f"{variant['label']}:",
                "",
                f"```{variant['language']}",
                variant["code"],
                "```",
            ]
    lines += [
        "",
        "## Dimensions",
        "",
        "| name | type | extent | unit |",
        "|---|---|---|---|",
        *(
            f"| `{name}` | {dim['type']} | {_extent(dim.get('extent'))} |"
            f" {dim.get('unit', '')} |"
            for name, dim in fields["cube:dimensions"].items()
        ),
        "",
        "## Variables",
        "",
        "| name | long name | unit | dimensions |",
        "|---|---|---|---|",
        *(
            f"| `{name}` | {var['long_name']} | {var.get('unit', '')} |"
            f" {', '.join(var['dimensions'])} |"
            for name, var in fields["cube:variables"].items()
        ),
    ]
    return "\n".join(lines) + "\n"
