"""Integration test: every python open snippet in stac/ executes cleanly.

Each example advertises two variants — a dynamical-catalog snippet and a
library-free pystac + icechunk-over-HTTPS snippet. Both must run against the
live datasets.
"""

from __future__ import annotations

import ast
import json
import pathlib
from collections.abc import Iterator
from concurrent.futures import Future, ThreadPoolExecutor

import pytest

_STAC_DIR = pathlib.Path(__file__).parent.parent / "stac"

# The pystac variant hardcodes the production catalog URL (correct for users);
# rewrite it to the locally-generated catalog so the test exercises the current
# source rather than whatever prod happens to be serving.
_PROD_CATALOG_URL = "https://stac.dynamical.org/catalog.json"

# These examples reduce complete 0.1-degree global ensemble fields. Execute them
# serially in their original tests after the pool has joined to avoid multiplying
# their multi-GiB working sets. Keep the snippets and their reads unchanged.
_SERIAL_COLLECTIONS = {
    "ecmwf-ifs-ens-forecast-15-day-0-1-degree-virtual",
    "ecmwf-ifs-ens-forecast-6-day-0-1-degree-virtual",
}

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


def _exec_example(collection_id: str, label: str, code: str, root_url: str) -> None:
    _assert_allowed_imports(code)
    # The client is already pointed at the local production catalog. Redirect
    # the pystac variant's hardcoded production URL to the same catalog.
    local_code = code.replace(_PROD_CATALOG_URL, f"{root_url}/catalog-production.json")
    globals_ns: dict[str, object] = {"__name__": f"example::{collection_id}"}
    exec(  # noqa: S102
        compile(local_code, f"<example:{collection_id}:{label}>", "exec"),
        globals_ns,
    )


@pytest.fixture(scope="module")
def example_results(
    served_production_catalog: object,
    served_catalog: tuple[pathlib.Path, str],
) -> dict[tuple[str, str, str, str], Future[None]]:
    """Prefetch the smaller examples with two workers, even under -k.

    Like URL prefetch, selection still runs all pooled cases when this fixture is used.
    Exceptions stay in futures for the original parametrized tests to report.
    """
    # served_catalog has opened/read every dataset and resolved its codecs.
    # Warm the client root on the main thread before workers import the client.
    served_production_catalog.list()  # type: ignore[attr-defined]
    _, root_url = served_catalog
    # Joining here finishes all workers before the catalog URL patch tears down.
    with ThreadPoolExecutor(max_workers=2) as executor:
        return {
            (cid, title, label, code): executor.submit(
                _exec_example, cid, label, code, root_url
            )
            for cid, title, label, code in _PYTHON_EXAMPLES
            if cid not in _SERIAL_COLLECTIONS
        }


def test_examples_found() -> None:
    # Guard against silently skipping everything if globbing breaks.
    assert _PYTHON_EXAMPLES, "no python examples found under stac/*/collection.json"
    assert _SERIAL_COLLECTIONS <= {example[0] for example in _PYTHON_EXAMPLES}, (
        "serial example collection IDs must exist in the committed catalog"
    )


@pytest.mark.integration
@pytest.mark.parametrize(
    ("collection_id", "title", "label", "code"),
    _PYTHON_EXAMPLES,
    ids=[f"{cid}:{title}:{label}" for cid, title, label, _ in _PYTHON_EXAMPLES],
)
def test_example_executes(  # noqa: PLR0917
    served_production_catalog: object,
    served_catalog: tuple[pathlib.Path, str],
    collection_id: str,
    title: str,
    label: str,
    code: str,
    example_results: dict[tuple[str, str, str, str], Future[None]],
) -> None:
    _assert_allowed_imports(code)
    assert served_production_catalog is not None
    if collection_id in _SERIAL_COLLECTIONS:
        _, root_url = served_catalog
        _exec_example(collection_id, label, code, root_url)
    else:
        example_results[collection_id, title, label, code].result()


@pytest.fixture(scope="module")
def served_production_catalog(
    served_catalog: tuple[pathlib.Path, str],
) -> Iterator[object]:
    """Examples under stac/ must also work for production-only datasets."""
    dynamical_catalog = pytest.importorskip("dynamical_catalog")
    from dynamical_catalog import _stac  # noqa: PLC0415

    _, root_url = served_catalog
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(_stac, "STAC_CATALOG_URL", f"{root_url}/catalog-production.json")
        _stac.clear_cache()
        try:
            yield dynamical_catalog
        finally:
            _stac.clear_cache()
