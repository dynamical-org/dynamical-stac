"""Integration test: committed stac/ must match what generate() produces today."""

from __future__ import annotations

import json
import pathlib

import pytest

from generate import generate

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMITTED_STAC = REPO_ROOT / "stac"


@pytest.mark.integration
def test_committed_stac_matches_generated(tmp_path: pathlib.Path) -> None:
    generate(tmp_path)

    committed_files = {
        p.relative_to(COMMITTED_STAC) for p in COMMITTED_STAC.rglob("*.json")
    }
    generated_files = {p.relative_to(tmp_path) for p in tmp_path.rglob("*.json")}

    missing = generated_files - committed_files
    extra = committed_files - generated_files
    assert not missing, (
        f"Missing from stac/: {sorted(missing)}. Run `scripts/generate`."
    )
    assert not extra, f"Unexpected in stac/: {sorted(extra)}. Run `scripts/generate`."

    mismatches: list[str] = []
    for rel in sorted(committed_files):
        committed = json.loads((COMMITTED_STAC / rel).read_text())
        generated = json.loads((tmp_path / rel).read_text())
        if committed != generated:
            mismatches.append(str(rel))

    assert not mismatches, (
        f"Content drift vs stac/ in: {mismatches}. Run `scripts/generate`."
    )
