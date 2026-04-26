"""Integration test: every link/href in the committed STAC tree resolves,
and the link graph reaches exactly the set of files on disk.

What this catches that the other tests miss:

* `test_stac_drift.py` checks committed-vs-regenerated equality but won't
  notice if both sides agree on a broken link.
* `test_stac_check.py` runs best-practice rules but does not verify that
  every `href` actually points somewhere real.
* `test_stac_browse.py` opens via pystac-client (which silently tolerates
  missing children) and only asserts collection IDs are present.
* `test_stac_schema_validation.py` validates each file's *shape* but not
  its *references*.

A 404'd `child` link, a `self` link that doesn't match its own filename,
or an orphaned committed `collection.json` with no parent link will cause
a generic STAC client (rust-stac, go-stac, QGIS) to either silently skip
the dataset or hard-error. Catch it here.
"""

from __future__ import annotations

import json
import pathlib
from collections import deque

import pystac
import pytest

from catalog import _COLLECTION_IDS
from generate import ROOT_HREF

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMITTED_STAC = REPO_ROOT / "stac"

# The committed tree uses ABSOLUTE_PUBLISHED hrefs (see generate.py:67), so
# every href under the public base URL maps 1:1 onto a path inside `stac/`.
_PUBLIC_BASE = ROOT_HREF.rstrip("/") + "/"

# Link rels whose targets must live inside our published tree. Other rels
# (`license`, `about`, `example`, etc.) point at external sites; we don't
# probe those over the network here — `tests/test_catalog_read.py` already
# HEADs notebook URLs.
_INTERNAL_LINK_RELS = frozenset({"root", "self", "parent", "child", "item"})


def _public_url_to_local_path(href: str) -> pathlib.Path | None:
    """Map a publication URL back to its committed file.

    Returns None if `href` does not point inside our published tree (e.g.
    license/about/example links to external domains).
    """
    if not href.startswith(_PUBLIC_BASE):
        return None
    relative = href[len(_PUBLIC_BASE) :]
    return COMMITTED_STAC / relative


def _all_committed_files() -> set[pathlib.Path]:
    return set(COMMITTED_STAC.rglob("*.json"))


# --- Round-trip pystac parse + traversal ----------------------------------


@pytest.mark.integration
def test_pystac_round_trip_walks_every_collection() -> None:
    """`pystac.read_file()` followed by `get_children()` reaches every
    declared collection. This is the most common Python STAC client usage
    pattern; if it can't traverse the tree, neither can downstream tools
    that build on pystac (pystac-client, stactools, odc-stac).
    """
    catalog = pystac.read_file(str(COMMITTED_STAC / "catalog.json"))
    assert isinstance(catalog, pystac.Catalog)

    children = list(catalog.get_children())
    reached = {c.id for c in children}
    assert reached == set(_COLLECTION_IDS), (
        f"pystac traversal mismatch. Expected {sorted(_COLLECTION_IDS)}, "
        f"got {sorted(reached)}."
    )

    # Each child must in turn be a fully-formed Collection — not a stub.
    for child in children:
        assert isinstance(child, pystac.Collection)
        assert child.title, f"{child.id}: missing title after pystac round-trip"
        assert child.extent.spatial.bboxes, f"{child.id}: missing spatial extent"
        assert child.extent.temporal.intervals, f"{child.id}: missing temporal extent"
        assert "icechunk" in child.assets, f"{child.id}: missing icechunk asset"


# --- Link-by-link integrity ------------------------------------------------

_STAC_FILES = sorted(COMMITTED_STAC.rglob("*.json"))


@pytest.mark.integration
@pytest.mark.parametrize(
    "json_path",
    _STAC_FILES,
    ids=[str(p.relative_to(COMMITTED_STAC)) for p in _STAC_FILES],
)
def test_internal_links_resolve_to_committed_files(
    json_path: pathlib.Path,
) -> None:
    """Every internal-rel link (root/self/parent/child/item) whose href
    falls under the public base URL maps to a file we actually committed.

    This catches: stale child links after a collection is removed, typoed
    hrefs, missing regeneration after an id change.
    """
    obj = json.loads(json_path.read_text())
    broken: list[str] = []
    for link in obj.get("links", []):
        rel = link.get("rel")
        if rel not in _INTERNAL_LINK_RELS:
            continue
        href = link.get("href", "")
        target = _public_url_to_local_path(href)
        # rel=root/self/parent/child/item that escapes our publication tree
        # is a bug — the catalog should not be cross-linking to a different
        # STAC root.
        assert target is not None, (
            f"{json_path.relative_to(COMMITTED_STAC)}: rel={rel} "
            f"href={href!r} is not under {_PUBLIC_BASE!r}"
        )
        if not target.is_file():
            broken.append(f"rel={rel} href={href} -> {target} (missing)")

    assert not broken, (
        f"{json_path.relative_to(COMMITTED_STAC)} has dangling links:\n  "
        + "\n  ".join(broken)
    )


@pytest.mark.integration
@pytest.mark.parametrize(
    "json_path",
    _STAC_FILES,
    ids=[str(p.relative_to(COMMITTED_STAC)) for p in _STAC_FILES],
)
def test_self_link_matches_file_location(json_path: pathlib.Path) -> None:
    """The `self` link's href, mapped back through the public base URL,
    must point at the file containing it.

    A mismatch means the file got renamed/moved without regenerating —
    clients that trust `self` (notably pystac-client and many JS browsers)
    will follow it to a 404.
    """
    obj = json.loads(json_path.read_text())
    self_links = [link for link in obj.get("links", []) if link.get("rel") == "self"]
    assert len(self_links) == 1, (
        f"{json_path.relative_to(COMMITTED_STAC)}: expected exactly one "
        f"rel=self link, found {len(self_links)}"
    )
    href = self_links[0]["href"]
    target = _public_url_to_local_path(href)
    assert target is not None, (
        f"{json_path.relative_to(COMMITTED_STAC)}: self href {href!r} "
        f"is not under {_PUBLIC_BASE!r}"
    )
    assert target.resolve() == json_path.resolve(), (
        f"{json_path.relative_to(COMMITTED_STAC)}: self link points at "
        f"{target.relative_to(COMMITTED_STAC)}, not at itself"
    )


@pytest.mark.integration
@pytest.mark.parametrize(
    "json_path",
    _STAC_FILES,
    ids=[str(p.relative_to(COMMITTED_STAC)) for p in _STAC_FILES],
)
def test_root_link_points_to_catalog(json_path: pathlib.Path) -> None:
    """Every file declares the same `rel=root` href, pointing at the
    top-level catalog. STAC clients use this to discover the catalog from
    any single item; if it diverges, deep-linking breaks.
    """
    obj = json.loads(json_path.read_text())
    root_links = [link for link in obj.get("links", []) if link.get("rel") == "root"]
    assert len(root_links) == 1, (
        f"{json_path.relative_to(COMMITTED_STAC)}: expected exactly one "
        f"rel=root link, found {len(root_links)}"
    )
    expected = f"{_PUBLIC_BASE}catalog.json"
    assert root_links[0]["href"] == expected, (
        f"{json_path.relative_to(COMMITTED_STAC)}: root href "
        f"{root_links[0]['href']!r} != {expected!r}"
    )


# --- Whole-graph reachability ---------------------------------------------


@pytest.mark.integration
def test_link_graph_reaches_every_committed_file() -> None:
    """BFS from `catalog.json` via `child`+`item` links must reach every
    *.json file in `stac/`, and every reached file must exist on disk.

    Detects two failure modes a generic STAC reader can't recover from:
      * Orphaned files: committed but no parent links to them. A reader
        starting from the root catalog will never see them, so users won't
        either — silent loss.
      * Phantom children: a `child`/`item` link whose target was never
        committed. The reader 404s and either skips the entry or aborts.
    """
    on_disk = {p.resolve() for p in _all_committed_files()}
    queue: deque[pathlib.Path] = deque([(COMMITTED_STAC / "catalog.json").resolve()])
    seen: set[pathlib.Path] = set()
    missing: list[str] = []

    while queue:
        path = queue.popleft()
        if path in seen:
            continue
        seen.add(path)
        if not path.is_file():
            missing.append(str(path.relative_to(COMMITTED_STAC)))
            continue
        obj = json.loads(path.read_text())
        for link in obj.get("links", []):
            if link.get("rel") not in {"child", "item"}:
                continue
            target = _public_url_to_local_path(link.get("href", ""))
            if target is None:
                continue
            queue.append(target.resolve())

    assert not missing, (
        f"child/item links point to files not in the committed tree: {missing}"
    )

    orphans = on_disk - seen
    assert not orphans, (
        "files in stac/ are unreachable from catalog.json via child/item "
        f"links: {sorted(p.relative_to(COMMITTED_STAC) for p in orphans)}"
    )
