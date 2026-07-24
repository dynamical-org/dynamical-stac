"""Integration test: every python open snippet in stac/ executes cleanly.

Each example advertises two variants — a dynamical-catalog snippet and a
library-free pystac + icechunk-over-HTTPS snippet. Both must run against the
live datasets.
"""

from __future__ import annotations

import ast
import json
import pathlib

import pytest

_STAC_DIR = pathlib.Path(__file__).parent.parent / "stac"

# The pystac variant hardcodes the production catalog URL (correct for users);
# rewrite it to the locally-generated catalog so the test exercises the current
# source rather than whatever prod happens to be serving.
_PROD_CATALOG_URL = "https://stac.dynamical.org/catalog.json"

# Import forms an example is allowed to use. The dynamical-catalog variant
# imports only dynamical_catalog; the pystac variant imports icechunk/pystac/
# xarray.
_ALLOWED_IMPORTS: set[tuple[str, str | None]] = {
    ("dynamical_catalog", None),
    ("icechunk", None),
    ("pystac", None),
    ("xarray", "xr"),
}


def _collect_python_examples() -> list[tuple[str, str, str, str]]:
    examples: list[tuple[str, str, str, str]] = []
    for collection_json in sorted(_STAC_DIR.glob("*/collection.json")):
        data = json.loads(collection_json.read_text())
        for ex in data.get("examples", []):
            examples.extend(
                (
                    collection_json.parent.name,
                    ex["title"],
                    variant["label"],
                    variant["code"],
                )
                for variant in ex.get("variants", [])
                if variant.get("language") == "python"
            )
    return examples


_PYTHON_EXAMPLES = _collect_python_examples()


def _assert_allowed_imports(code: str) -> None:
    """Gate exec(): every import must be on the allowlist; no `from` imports."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            raise AssertionError(f"disallowed `from` import: {ast.unparse(node)!r}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if (alias.name, alias.asname) not in _ALLOWED_IMPORTS:
                    raise AssertionError(f"disallowed import: {ast.unparse(node)!r}")


def test_examples_found() -> None:
    # Guard against silently skipping everything if globbing breaks.
    assert _PYTHON_EXAMPLES, "no python examples found under stac/*/collection.json"


@pytest.mark.integration
@pytest.mark.parametrize(
    ("collection_id", "title", "label", "code"),
    _PYTHON_EXAMPLES,
    ids=[f"{cid}:{title}:{label}" for cid, title, label, _ in _PYTHON_EXAMPLES],
)
def test_example_executes(
    dynamical_catalog_fixture: object,
    served_catalog: tuple[pathlib.Path, str],
    collection_id: str,
    title: str,
    label: str,
    code: str,
) -> None:
    _assert_allowed_imports(code)
    # The dynamical_catalog fixture has already imported the library and pointed
    # it at the locally-served catalog; exec's `import dynamical_catalog` then
    # hits sys.modules and reuses that configured module. The pystac variant
    # reads the same catalog directly, so redirect its hardcoded prod URL too.
    assert dynamical_catalog_fixture is not None
    _, root_url = served_catalog
    local_code = code.replace(_PROD_CATALOG_URL, f"{root_url}/catalog.json")
    globals_ns: dict[str, object] = {"__name__": f"example::{collection_id}"}
    exec(  # noqa: S102
        compile(local_code, f"<example:{collection_id}:{label}>", "exec"),
        globals_ns,
    )
