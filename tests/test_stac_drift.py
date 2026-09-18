"""Integration test: every committed tier must match what generate_tiers() produces today."""

from __future__ import annotations

import json
import pathlib

import pytest

from generate import TIERS, generate_tiers

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def generated(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    parent_dir = tmp_path_factory.mktemp("tiers")
    generate_tiers(parent_dir)
    return parent_dir


@pytest.mark.integration
@pytest.mark.parametrize("tier_directory", [tier.directory for tier in TIERS])
def test_committed_stac_matches_generated(
    generated: pathlib.Path, tier_directory: str
) -> None:
    committed_dir = REPO_ROOT / tier_directory
    generated_dir = generated / tier_directory

    committed_files = {
        p.relative_to(committed_dir) for p in committed_dir.rglob("*.json")
    }
    generated_files = {
        p.relative_to(generated_dir) for p in generated_dir.rglob("*.json")
    }

    missing = generated_files - committed_files
    extra = committed_files - generated_files
    assert not missing, (
        f"Missing from {tier_directory}/: {sorted(missing)}. Run `scripts/generate`."
    )
    assert not extra, (
        f"Unexpected in {tier_directory}/: {sorted(extra)}. Run `scripts/generate`."
    )

    mismatches: list[str] = []
    for rel in sorted(committed_files):
        committed = json.loads((committed_dir / rel).read_text())
        generated_json = json.loads((generated_dir / rel).read_text())
        if committed != generated_json:
            mismatches.append(str(rel))

    assert not mismatches, (
        f"Content drift vs {tier_directory}/ in: {mismatches}. Run `scripts/generate`."
    )
