"""Integration test: each *released* dynamical-catalog version on PyPI must
still open every collection in the locally generated STAC.

`tests/test_catalog_read.py` exercises whatever `dynamical-catalog` version is
installed into the project venv (today: the `icechunk-2` dev branch, per
`[tool.uv.sources]` in pyproject.toml). That misses regressions against
releases still in the wild — the kind introduced when we dropped the `zarr`
asset and stopped emitting `icechunk:storage.{bucket,prefix,region}`, both of
which silently broke 0.3.0 consumers.

This test pins to each target (released PyPI version or tracked git ref) and
runs the full open+read flow against the just-generated STAC, so CI fails the
moment a backwards-incompatible change lands.

Each target is installed into an isolated env via `uv run --with` and the
check runs in a subprocess. When support for a release is dropped, remove the
entry from `SUPPORTED_RELEASES` and the matching `TODO(temporary)` shims in
src/models.py and src/catalog.py together.
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys
import textwrap

import pytest

from catalog import _COLLECTION_IDS

# PyPI releases we contract to support. Each breaking change here is a
# regression and must be fixed before merging.
SUPPORTED_RELEASES = ["0.3.0", "0.4.0"]

# Additional git refs to test against. These are early-warning canaries for
# upstream changes — not a support contract. A failure here should prompt a
# fix (in dynamical-stac or dynamical-catalog) rather than blocking merges.
TRACKED_REFS = ["main"]

_ALL_TARGETS = [*SUPPORTED_RELEASES, *TRACKED_REFS]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
TEST_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "test.yml"
_DYNAMICAL_CATALOG_REPO = "https://github.com/dynamical-org/dynamical-catalog"

_HARNESS = textwrap.dedent(
    """
    import json, math, sys
    import dynamical_catalog
    from dynamical_catalog import _stac

    root_url, collection_ids_json = sys.argv[1], sys.argv[2]
    collection_ids = json.loads(collection_ids_json)

    _stac.STAC_CATALOG_URL = root_url + "/catalog.json"
    _stac.clear_cache()

    for cid in collection_ids:
        ds = dynamical_catalog.open(cid)
        first = next(iter(ds.data_vars))
        da = ds[first]
        value = da.isel({d: 0 for d in da.dims}).load().item()
        assert isinstance(value, (int, float)), f"{cid}.{first} -> {value!r}"
        if isinstance(value, float):
            assert not math.isinf(value), f"{cid}.{first} is inf"
    """
).strip()


def _install_spec(target: str) -> str:
    """Return the requirement string for `uv run --with` given a target.

    Exact PyPI pins for `SUPPORTED_RELEASES`; git-ref installs for anything
    in `TRACKED_REFS`.
    """
    if target in SUPPORTED_RELEASES:
        return f"dynamical-catalog=={target}"
    return f"dynamical-catalog @ git+{_DYNAMICAL_CATALOG_REPO}@{target}"


@pytest.mark.integration
@pytest.mark.parametrize("target", _ALL_TARGETS)
def test_released_dynamical_catalog_opens_every_collection(
    served_catalog: tuple[pathlib.Path, str],
    target: str,
    tmp_path: pathlib.Path,
) -> None:
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv not available; cannot install released dynamical-catalog")

    _, root_url = served_catalog
    harness = tmp_path / "harness.py"
    harness.write_text(_HARNESS)

    subprocess.run(  # noqa: S603
        [
            uv,
            "run",
            "--isolated",
            "--no-project",
            "--quiet",
            "--python",
            f"{sys.version_info.major}.{sys.version_info.minor}",
            "--with",
            _install_spec(target),
            "python",
            str(harness),
            root_url,
            json.dumps(_COLLECTION_IDS),
        ],
        check=True,
    )


def test_compat_matrix_matches_targets() -> None:
    """Guard against the `compat` job matrix in .github/workflows/test.yml
    drifting out of sync with _ALL_TARGETS (SUPPORTED_RELEASES + TRACKED_REFS).

    PyYAML is pulled in transitively by stac-check (dev deps), so we can
    parse the workflow directly rather than regexing.
    """
    yaml = pytest.importorskip("yaml")
    workflow = yaml.safe_load(TEST_WORKFLOW.read_text())
    matrix_targets = workflow["jobs"]["compat"]["strategy"]["matrix"][
        "dynamical-catalog-target"
    ]
    assert matrix_targets == _ALL_TARGETS, (
        f"compat matrix in {TEST_WORKFLOW.relative_to(REPO_ROOT)} "
        f"({matrix_targets}) must match SUPPORTED_RELEASES + TRACKED_REFS "
        f"({_ALL_TARGETS})"
    )


def test_supported_releases_use_exact_pins() -> None:
    """Each entry in SUPPORTED_RELEASES should be a concrete version so the
    compat harness installs exactly that release (no `>=`, no wildcards)."""
    pattern = re.compile(r"^\d+\.\d+\.\d+$")
    bad = [v for v in SUPPORTED_RELEASES if not pattern.match(v)]
    assert not bad, f"Non-exact versions in SUPPORTED_RELEASES: {bad}"


def test_tracked_refs_are_plausible_git_refs() -> None:
    """TRACKED_REFS must be simple branch/tag names — no whitespace, no shell
    metacharacters — since they get interpolated into an install spec and a
    workflow matrix value.
    """
    pattern = re.compile(r"^[A-Za-z0-9._/-]+$")
    bad = [r for r in TRACKED_REFS if not pattern.match(r)]
    assert not bad, f"Suspicious git refs in TRACKED_REFS: {bad}"
