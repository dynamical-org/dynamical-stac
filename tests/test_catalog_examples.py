"""Integration test: every python `examples` snippet in the catalog executes cleanly.

Examples are sourced from `CATALOG_ITEMS` rather than the committed `stac/`
tree so coverage includes staging datasets, whose examples never reach the
production `stac/` output but still ship to stac-staging (and still need to
run). The rendered STAC `examples` field is a verbatim dump of
`CatalogItem.examples` (see `CollectionInput.to_pystac_collection`), so this
exercises exactly the code a consumer sees.
"""

from __future__ import annotations

import ast

import pytest

from catalog import CATALOG_ITEMS


def _collect_python_examples() -> list[tuple[str, str, str]]:
    return [
        (item.id, example.title, example.code)
        for item in CATALOG_ITEMS
        for example in item.examples
        if example.language == "python"
    ]


_PYTHON_EXAMPLES = _collect_python_examples()


def _assert_only_dynamical_catalog_import(code: str) -> None:
    """Gate exec(): every import statement must be exactly `import dynamical_catalog`."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            raise AssertionError(f"disallowed `from` import: {ast.unparse(node)!r}")
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
            if names != ["dynamical_catalog"] or node.names[0].asname is not None:
                raise AssertionError(f"disallowed import: {ast.unparse(node)!r}")


def test_examples_found() -> None:
    # Guard against silently skipping everything if collection breaks.
    assert _PYTHON_EXAMPLES, "no python examples found in CATALOG_ITEMS"


@pytest.mark.integration
@pytest.mark.parametrize(
    ("collection_id", "title", "code"),
    _PYTHON_EXAMPLES,
    ids=[f"{cid}:{title}" for cid, title, _ in _PYTHON_EXAMPLES],
)
def test_example_executes(
    dynamical_catalog_fixture: object,
    collection_id: str,
    title: str,
    code: str,
) -> None:
    _assert_only_dynamical_catalog_import(code)
    # The fixture has already imported `dynamical_catalog` and pointed it at
    # the locally-served catalog (generated with staging included); exec's
    # `import dynamical_catalog` then hits sys.modules and reuses that
    # configured module.
    assert dynamical_catalog_fixture is not None
    globals_ns: dict[str, object] = {"__name__": f"example::{collection_id}"}
    exec(compile(code, f"<example:{collection_id}:{title}>", "exec"), globals_ns)  # noqa: S102
