from __future__ import annotations

import json
import pathlib
import re
import sys

import pydantic
import pytest

from catalog import (
    CATALOG_ITEMS,
    LEGACY_CLIENT_RANGES,
    CatalogItem,
    LegacyClientRange,
    _check_legacy_client_ranges,
    root_filename_for_client,
)
from generate import legacy_root

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMITTED_STAC = REPO_ROOT / "stac"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from compat_matrix import MIN_VERSION, reads_virtual_chunks  # noqa: E402

_ROOT = {
    "type": "Catalog",
    "id": "dynamical-org",
    "links": [
        {"rel": "root", "href": "https://stac.example/catalog.json"},
        {"rel": "child", "href": "https://stac.example/plain/collection.json"},
        {"rel": "child", "href": "https://stac.example/needs-gcs/collection.json"},
        {"rel": "self", "href": "https://stac.example/catalog.json"},
    ],
}


def _hrefs(root: dict[str, object], rel: str) -> list[str]:
    return [link["href"] for link in root["links"] if link["rel"] == rel]  # type: ignore[attr-defined]


def test_legacy_root_drops_only_excluded_children() -> None:
    legacy = legacy_root(_ROOT, "catalog-0.4.0-0.8.0.json", {"needs-gcs"})
    assert _hrefs(legacy, "child") == ["https://stac.example/plain/collection.json"]


def test_legacy_root_names_itself_and_keeps_the_catalog_as_root() -> None:
    legacy = legacy_root(_ROOT, "catalog-0.4.0-0.8.0.json", set())
    assert _hrefs(legacy, "self") == ["https://stac.example/catalog-0.4.0-0.8.0.json"]
    assert _hrefs(legacy, "root") == ["https://stac.example/catalog.json"]
    assert _hrefs(_ROOT, "self") == ["https://stac.example/catalog.json"]


@pytest.mark.parametrize(
    ("client_version", "root_filename"),
    [
        ("0.4.0", "catalog-0.4.0-0.8.0.json"),
        ("0.8.0", "catalog-0.4.0-0.8.0.json"),
        # Never released, but the edge would route it by the same prefix.
        ("0.9.0", "catalog-0.4.0-0.8.0.json"),
        ("1.0.0", "catalog.json"),
        ("10.0.0", "catalog.json"),
    ],
)
def test_root_filename_for_client(client_version: str, root_filename: str) -> None:
    assert root_filename_for_client(client_version) == root_filename


def _range(name: str, prefix: str) -> LegacyClientRange:
    return LegacyClientRange(name=name, user_agent_prefix=prefix, s3_only=False)


@pytest.mark.parametrize(
    ("other_name", "other_prefix", "message"),
    [
        ("0.4.0-0.8.0", "dynamical-catalog/1.0.", "duplicate"),
        ("0.9.0-0.9.9", "dynamical-catalog/0.", "overlapping"),
        ("0.9.0-0.9.9", "dynamical-catalog/0.9.", "overlapping"),
    ],
)
def test_ranges_must_have_distinct_names_and_disjoint_prefixes(
    other_name: str, other_prefix: str, message: str
) -> None:
    first = _range("0.4.0-0.8.0", "dynamical-catalog/0.")
    with pytest.raises(ValueError, match=message):
        _check_legacy_client_ranges((first, _range(other_name, other_prefix)))
    _check_legacy_client_ranges(
        (first, _range("1.0.0-1.0.1", "dynamical-catalog/1.0."))
    )


def _item_fields(**overrides: object) -> dict[str, object]:
    fields = CATALOG_ITEMS[0].model_dump()
    assert fields["icechunk_href"].startswith("s3://")
    return {**fields, **overrides}


def test_exclude_from_rejects_an_unknown_range() -> None:
    with pytest.raises(pydantic.ValidationError, match="unknown legacy client ranges"):
        CatalogItem(**_item_fields(exclude_from=("0.4.0-0.7.0",)))


@pytest.mark.parametrize(
    "prefixes", [("gs://bucket/",), ("s3://bucket/", "https://host/chunks/")]
)
def test_non_s3_container_must_be_excluded_from_s3_only_ranges(
    prefixes: tuple[str, ...],
) -> None:
    fields = _item_fields(virtual_chunk_container_prefixes=prefixes)
    with pytest.raises(pydantic.ValidationError, match="add them to exclude_from"):
        CatalogItem(**fields)
    CatalogItem(**{**fields, "exclude_from": ("0.4.0-0.8.0",)})


def test_non_s3_repository_must_be_excluded_from_s3_only_ranges() -> None:
    item_id = CATALOG_ITEMS[0].id
    fields = _item_fields(
        icechunk_href=f"gs://bucket/{item_id}/v0.1.0.icechunk/", icechunk_region=None
    )
    with pytest.raises(pydantic.ValidationError, match="add them to exclude_from"):
        CatalogItem(**fields)
    CatalogItem(**{**fields, "exclude_from": ("0.4.0-0.8.0",)})


@pytest.mark.parametrize("legacy_range", LEGACY_CLIENT_RANGES, ids=lambda r: r.name)
def test_committed_legacy_root_links_exactly_its_production_items(
    legacy_range: object,
) -> None:
    expected = [
        item.id
        for item in CATALOG_ITEMS
        if not (item.staging or item.test)
        and legacy_range.name not in item.exclude_from  # type: ignore[attr-defined]
    ]
    root = json.loads((COMMITTED_STAC / legacy_range.root_filename).read_text())  # type: ignore[attr-defined]
    child_ids = [
        pathlib.PurePosixPath(href).parent.name for href in _hrefs(root, "child")
    ]
    assert expected
    assert child_ids == expected


def test_range_names_are_safe_in_file_names_and_edge_rules() -> None:
    for legacy_range in LEGACY_CLIENT_RANGES:
        assert re.fullmatch(r"catalog-[0-9.-]+\.json", legacy_range.root_filename)


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("0.4.0", False),
        ("0.5.0", True),
        ("0.10.0", True),
        ("1.0.1", True),
        ("main", True),
    ],
)
def test_only_releases_before_virtual_support_skip_virtual_reads(
    target: str, expected: bool
) -> None:
    assert reads_virtual_chunks(target) is expected


def test_the_floor_is_the_only_release_exempt_from_virtual_reads() -> None:
    # Lowering the floor further must not quietly widen the exemption's reach.
    assert MIN_VERSION == "0.4.0"
