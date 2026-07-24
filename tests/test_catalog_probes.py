from __future__ import annotations

import importlib
import pathlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

# The probe script lives in scripts/ and imports `modal` (a deploy-time tool
# pulled ephemerally in CI, not a project dependency), so stub it to import the
# pure assertion helpers here.
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
sys.modules.setdefault("modal", MagicMock())

catalog_probes: ModuleType = importlib.import_module("catalog_probes")


def _catalog(child_count: int) -> dict[str, object]:
    links: list[dict[str, str]] = [{"rel": "root", "href": "root.json"}]
    links += [
        {"rel": "child", "href": f"c{i}/collection.json"} for i in range(child_count)
    ]
    links.append({"rel": "self", "href": "catalog.json"})
    return {"type": "Catalog", "id": "dynamical-org", "links": links}


def test_check_stac_catalog_healthy() -> None:
    assert catalog_probes.check_stac_catalog(_catalog(12)) == 12


def test_check_stac_catalog_at_minimum() -> None:
    assert (
        catalog_probes.check_stac_catalog(_catalog(catalog_probes.MIN_CHILD_LINKS))
        == catalog_probes.MIN_CHILD_LINKS
    )


def test_check_stac_catalog_too_few_children() -> None:
    with pytest.raises(AssertionError, match="child links"):
        catalog_probes.check_stac_catalog(_catalog(catalog_probes.MIN_CHILD_LINKS - 1))


def test_check_stac_catalog_wrong_type() -> None:
    doc = _catalog(12)
    doc["type"] = "Collection"
    with pytest.raises(AssertionError, match="Catalog"):
        catalog_probes.check_stac_catalog(doc)


def test_check_stac_catalog_no_links() -> None:
    with pytest.raises(AssertionError, match="links"):
        catalog_probes.check_stac_catalog({"type": "Catalog"})


def test_check_stac_catalog_not_an_object() -> None:
    with pytest.raises(AssertionError, match="JSON object"):
        catalog_probes.check_stac_catalog(["not", "a", "catalog"])


def test_check_mcp_tools_non_empty() -> None:
    assert catalog_probes.check_mcp_tools(["search_catalog", "get_dataset_info"]) == 2


def test_check_mcp_tools_empty() -> None:
    with pytest.raises(AssertionError, match="no tools"):
        catalog_probes.check_mcp_tools([])
