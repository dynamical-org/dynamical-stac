from __future__ import annotations

from types import SimpleNamespace

from generate import _select_items


def _item(
    item_id: str, *, staging: bool = False, test: bool = False
) -> SimpleNamespace:
    # _select_items only reads `.staging`/`.test`; a stand-in avoids the full
    # CatalogItem.
    return SimpleNamespace(id=item_id, staging=staging, test=test)


def _ids(
    items: list[SimpleNamespace], *, include_staging: bool, include_test: bool
) -> list[str]:
    selected = _select_items(
        items,  # type: ignore[arg-type]
        include_staging=include_staging,
        include_test=include_test,
    )
    return [item.id for item in selected]


def test_production_excludes_staging_items() -> None:
    items = [_item("a"), _item("b", staging=True)]
    assert _ids(items, include_staging=False, include_test=False) == ["a"]


def test_staging_catalog_includes_staging_items() -> None:
    items = [_item("a"), _item("b", staging=True)]
    assert _ids(items, include_staging=True, include_test=False) == ["a", "b"]


def test_production_excludes_test_items() -> None:
    items = [_item("a"), _item("b", test=True)]
    assert _ids(items, include_staging=False, include_test=False) == ["a"]


def test_staging_catalog_excludes_test_items() -> None:
    items = [_item("a"), _item("b", staging=True), _item("c", test=True)]
    assert _ids(items, include_staging=True, include_test=False) == ["a", "b"]


def test_test_catalog_includes_test_items() -> None:
    items = [_item("a"), _item("b", test=True)]
    assert _ids(items, include_staging=False, include_test=True) == ["a", "b"]


def test_test_catalog_holds_production_staging_and_test_items() -> None:
    items = [_item("a"), _item("b", staging=True), _item("c", test=True)]
    assert _ids(items, include_staging=True, include_test=True) == ["a", "b", "c"]
