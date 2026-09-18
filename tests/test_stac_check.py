"""Integration test: run stac-check best-practices linter on the committed catalog.

Lints the committed `stac/` tree — the production catalog we actually ship to
stac.dynamical.org — rather than the `served_catalog` fixture, which
includes staging items. `test_stac_drift.py` guarantees the committed tree
equals what `generate()` produces, so linting it is equivalent to linting a
freshly-generated production catalog, and it keeps this prod contract separate
from the staging-inclusive fixture.
"""

from __future__ import annotations

import pathlib
import shutil

import pytest

from catalog import LEGACY_CLIENT_RANGES

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMITTED_STAC = REPO_ROOT / "stac"
STAC_CHECK_CONFIG = pathlib.Path(__file__).with_name("stac-check.config.yml")


@pytest.mark.integration
def test_no_stac_check_best_practice_warnings(tmp_path: pathlib.Path) -> None:
    stac_check = pytest.importorskip("stac_check.lint")

    files = {
        "catalog.json": COMMITTED_STAC / "catalog.json",
        **{
            str(f.relative_to(COMMITTED_STAC)): f
            for f in COMMITTED_STAC.glob("*/collection.json")
        },
    }
    # stac-check wants a catalog's file to be named `catalog.json`. A legacy root
    # is served under that name, so lint it under that name.
    for legacy_range in LEGACY_CLIENT_RANGES:
        served_as = tmp_path / legacy_range.name / "catalog.json"
        served_as.parent.mkdir()
        shutil.copy(COMMITTED_STAC / legacy_range.root_filename, served_as)
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
