"""Integration test: run stac-check best-practices linter on the committed catalog.

Lints the committed `stac/` tree — the production catalog we actually ship to
stac.dynamical.org — rather than the `served_catalog` fixture, which now
includes staging items. `test_stac_drift.py` guarantees the committed tree
equals what `generate()` produces, so linting it is equivalent to linting a
freshly-generated production catalog, and it keeps this prod contract separate
from the staging-inclusive fixture.
"""

from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMITTED_STAC = REPO_ROOT / "stac"


@pytest.mark.integration
def test_no_stac_check_best_practice_warnings() -> None:
    stac_check = pytest.importorskip("stac_check.lint")

    files = [
        COMMITTED_STAC / "catalog.json",
        *COMMITTED_STAC.glob("*/collection.json"),
    ]
    assert files, "no committed STAC files found"

    failures: list[str] = []
    for f in files:
        linter = stac_check.Linter(str(f))
        best_practices = linter.create_best_practices_dict()
        if best_practices:
            failures.append(f"{f.name}: {best_practices}")

    assert not failures, "stac-check best-practice warnings:\n" + "\n".join(failures)
