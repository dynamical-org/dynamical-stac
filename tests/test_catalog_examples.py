"""Integration test: every python `examples` code block in stac/ executes cleanly."""

from __future__ import annotations

import ast
import json
import pathlib

import pytest

_STAC_DIR = pathlib.Path(__file__).parent.parent / "stac"


def _collect_python_examples() -> list[tuple[str, str, str]]:
    examples: list[tuple[str, str, str]] = []
    for collection_json in sorted(_STAC_DIR.glob("*/collection.json")):
        data = json.loads(collection_json.read_text())
        examples.extend(
            (collection_json.parent.name, ex["title"], ex["code"])
            for ex in data.get("examples", [])
            if ex.get("language") == "python"
        )
    return examples


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
    # Guard against silently skipping everything if globbing breaks.
    assert _PYTHON_EXAMPLES, "no python examples found under stac/*/collection.json"


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
    # the locally-served catalog; exec's `import dynamical_catalog` then hits
    # sys.modules and reuses that configured module.
    assert dynamical_catalog_fixture is not None
    globals_ns: dict[str, object] = {"__name__": f"example::{collection_id}"}
    exec(compile(code, f"<example:{collection_id}:{title}>", "exec"), globals_ns)  # noqa: S102
