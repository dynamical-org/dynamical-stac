"""Integration test: run stac-check best-practices linter on the committed catalogs.

Lints the committed trees — what we actually ship to each environment's host — rather
than the `served_catalog` fixture. `test_stac_drift.py` guarantees the
committed trees equal what `generate_environments()` produces, so linting them is
equivalent to linting freshly-generated catalogs.
"""

from __future__ import annotations

import pathlib
import shutil

import pytest

from environments import STAC_ENVIRONMENTS

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
STAC_CHECK_CONFIG = pathlib.Path(__file__).with_name("stac-check.config.yml")


@pytest.mark.integration
@pytest.mark.parametrize(
    "environment_directory",
    sorted({environment.directory for environment in STAC_ENVIRONMENTS}),
)
def test_no_stac_check_best_practice_warnings(
    environment_directory: str, tmp_path: pathlib.Path
) -> None:
    stac_check = pytest.importorskip("stac_check.lint")

    committed = REPO_ROOT / environment_directory
    files = [committed / "catalog.json", *committed.glob("*/collection.json")]

    # Additional roots are served as catalogs, so lint under the standard filename.
    for environment in STAC_ENVIRONMENTS:
        if (
            environment.directory == environment_directory
            and environment.client_versions is not None
        ):
            renamed_root = tmp_path / environment.name / "catalog.json"
            renamed_root.parent.mkdir()
            shutil.copy(committed / environment.root_filename, renamed_root)
            files.append(renamed_root)

    failures: list[str] = []
    for f in files:
        linter = stac_check.Linter(str(f), config_file=str(STAC_CHECK_CONFIG))
        best_practices = linter.create_best_practices_dict()
        if best_practices:
            failures.append(f"{f.name}: {best_practices}")

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
