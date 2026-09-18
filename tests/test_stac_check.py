"""Integration test: run stac-check best-practices linter on the committed catalogs.

Lints the committed trees — what we actually ship to each tier's host — rather
than the `served_catalog` fixture. `test_stac_drift.py` guarantees the
committed trees equal what `generate_tiers()` produces, so linting them is
equivalent to linting freshly-generated catalogs.
"""

from __future__ import annotations

import pathlib
import shutil

import pytest

from catalog import LEGACY_CLIENT_RANGES
from generate import TIERS

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
STAC_CHECK_CONFIG = pathlib.Path(__file__).with_name("stac-check.config.yml")


@pytest.mark.integration
@pytest.mark.parametrize("tier_directory", [tier.directory for tier in TIERS])
def test_no_stac_check_best_practice_warnings(
    tier_directory: str, tmp_path: pathlib.Path
) -> None:
    stac_check = pytest.importorskip("stac_check.lint")

    committed = REPO_ROOT / tier_directory
    files = {
        "catalog.json": committed / "catalog.json",
        **{
            str(f.relative_to(committed)): f
            for f in committed.glob("*/collection.json")
        },
    }
    # stac-check wants a catalog's file to be named `catalog.json`. A legacy root
    # is served under that name, so lint it under that name.
    for legacy_range in LEGACY_CLIENT_RANGES:
        served_as = tmp_path / legacy_range.name / "catalog.json"
        served_as.parent.mkdir()
        shutil.copy(committed / legacy_range.root_filename, served_as)
        files[legacy_range.root_filename] = served_as

    failures: list[str] = []
    for name, f in files.items():
        linter = stac_check.Linter(str(f), config_file=str(STAC_CHECK_CONFIG))
        best_practices = linter.create_best_practices_dict()
        if best_practices:
            failures.append(f"{name}: {best_practices}")

    assert not failures, "stac-check best-practice warnings:\n" + "\n".join(failures)


@pytest.mark.integration
def test_stac_check_config_only_disables_bloated_links() -> None:
    """The override keeps every other best-practice rule at its packaged default,
    so a new warning class cannot be silenced by widening this file."""
    stac_check = pytest.importorskip("stac_check.lint")

    default = stac_check.Linter.parse_config()
    ours = stac_check.Linter.parse_config(str(STAC_CHECK_CONFIG))

    assert ours["linting"]["bloated_links"] is False
    assert {k: v for k, v in ours["linting"].items() if k != "bloated_links"} == {
        k: v for k, v in default["linting"].items() if k != "bloated_links"
    }
    assert ours["settings"] == default["settings"]
    assert ours["geometry_validation"] == default["geometry_validation"]
