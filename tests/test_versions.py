"""Check that icechunk versions in src/data/ match reformatters dataset_version."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

_DATA_DIR = Path(__file__).parent.parent / "src" / "data"


def _stac_icechunk_versions() -> dict[str, str]:
    """Return {dataset_id: version} for STAC collections that have an icechunk asset."""
    versions: dict[str, str] = {}
    for f in sorted(_DATA_DIR.glob("*.json")):
        col = json.loads(f.read_text())
        prefix = (
            col.get("assets", {})
            .get("icechunk", {})
            .get("icechunk:storage", {})
            .get("prefix", "")
        )
        m = re.search(r"/v([^/]+)\.icechunk/", prefix)
        if m:
            versions[col["id"]] = m.group(1)
    return versions


def _reformatters_versions(reformatters_dir: Path) -> dict[str, str]:
    """Return {dataset_id: dataset_version} parsed from reformatters template_config.py files."""
    versions: dict[str, str] = {}
    for f in (reformatters_dir / "src" / "reformatters").rglob("template_config.py"):
        content = f.read_text()
        id_m = re.search(r'dataset_id\s*=\s*"([^"]+)"', content)
        ver_m = re.search(r'dataset_version\s*=\s*"([^"]+)"', content)
        if id_m and ver_m:
            versions[id_m.group(1)] = ver_m.group(1)
    return versions


@pytest.fixture
def reformatters_dir() -> Path:
    path = Path(os.environ.get("REFORMATTERS_DIR", Path(__file__).parents[3] / "reformatters"))
    if not path.exists():
        pytest.skip(f"reformatters not found at {path} — set REFORMATTERS_DIR to run this test")
    return path


def test_stac_versions_match_reformatters(reformatters_dir: Path) -> None:
    stac = _stac_icechunk_versions()
    reformatters = _reformatters_versions(reformatters_dir)

    mismatches: list[str] = []
    checked = 0
    for dataset_id, stac_version in stac.items():
        if dataset_id not in reformatters:
            continue  # dataset renamed or contrib-only; skip
        checked += 1
        ref_version = reformatters[dataset_id]
        if stac_version != ref_version:
            mismatches.append(
                f"  {dataset_id}: STAC has v{stac_version}, reformatters has v{ref_version}"
            )

    assert checked > 0, "No datasets matched between STAC and reformatters"
    assert not mismatches, "Version mismatches:\n" + "\n".join(mismatches)
