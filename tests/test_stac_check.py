"""Integration test: run stac-check best-practices linter on the generated catalog."""

from __future__ import annotations

import pathlib

import pytest


@pytest.mark.integration
def test_no_stac_check_best_practice_warnings(
    served_catalog: tuple[pathlib.Path, str],
) -> None:
    stac_check = pytest.importorskip("stac_check.lint")

    catalog_dir, _ = served_catalog
    files = [catalog_dir / "catalog.json", *catalog_dir.glob("*/collection.json")]
    assert files, "no STAC files generated"

    failures: list[str] = []
    for f in files:
        linter = stac_check.Linter(str(f))
        best_practices = linter.create_best_practices_dict()
        if best_practices:
            failures.append(f"{f.name}: {best_practices}")

    assert not failures, "stac-check best-practice warnings:\n" + "\n".join(failures)
