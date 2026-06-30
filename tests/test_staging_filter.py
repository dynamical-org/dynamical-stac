from __future__ import annotations

from types import SimpleNamespace

from generate import _select_items


def _item(item_id: str, *, staging: bool) -> SimpleNamespace:
    # _select_items only reads `.staging`; a stand-in avoids the full CatalogItem.
    return SimpleNamespace(id=item_id, staging=staging)


def test_production_excludes_staging_items() -> None:
    items = [_item("a", staging=False), _item("b", staging=True)]
    assert [i.id for i in _select_items(items, include_staging=False)] == ["a"]


def test_staging_catalog_includes_staging_items() -> None:
    items = [_item("a", staging=False), _item("b", staging=True)]
    assert [i.id for i in _select_items(items, include_staging=True)] == ["a", "b"]
