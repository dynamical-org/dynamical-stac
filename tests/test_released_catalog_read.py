"""Integration test: every supported `dynamical-catalog` release on PyPI
(plus the `main` canary) must still open every collection in the locally
generated STAC.

`tests/test_catalog_read.py` exercises whatever `dynamical-catalog` is
installed into the project venv via the in-process
`dynamical_catalog_fixture`. That misses regressions against releases
still in the wild — the kind introduced when we dropped the `zarr` asset
and stopped emitting `icechunk:storage.{bucket,prefix,region}`, both of
which silently broke 0.3.0 consumers.

Each target is installed into an isolated env via `uv run --with` and the
check runs in a subprocess so it can't share import state with the
project venv. The full `open + read first variable` flow runs against
the just-generated STAC, so CI fails the moment a backwards-incompatible
change lands.

The set of targets is built fresh on every run by
`scripts/compat_matrix.py`, which queries PyPI for non-yanked stable
releases >= MIN_VERSION and appends every entry in CANARY_REFS. There is
no manual list of releases here or in the workflow — when a new release
is published, the next CI run picks it up automatically.

When backwards compatibility for an old release is no longer worth it,
bump `MIN_VERSION` in `scripts/compat_matrix.py` (and yank that release
on PyPI for downstream clarity). When a still-shipped release gains a
known-broken bug we want to track but not block on, add it to
`_RELEASE_ALLOW_FAILURE` in the same script.
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

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = REPO_ROOT / "scripts"

# Single source of truth for the compat target set, shared with
# .github/workflows/test.yml's `discover` job.
sys.path.insert(0, str(_SCRIPTS_DIR))
from compat_matrix import (  # noqa: E402
    CANARY_REFS,
    PACKAGE,
    build_targets,
    fetch_releases,
    safe_id,
)

_DYNAMICAL_CATALOG_REPO = "https://github.com/dynamical-org/dynamical-catalog"

# Resolve targets at module import (collection time) so each one becomes
# its own pytest parametrize id. PyPI is hit once; the result is reused
# inside this process. If PyPI is unreachable, collection fails loudly —
# silently dropping coverage of every released version would be worse.
_TARGETS = build_targets()


def _install_spec(target: str) -> str:
    """Return the requirement string for `uv run --with` given a target.

    A pure semver string installs the matching PyPI release; anything
    else (e.g. `main`, a branch name, a tag) installs from git.
    """
    if re.fullmatch(r"\d+\.\d+\.\d+", target):
        return f"{PACKAGE}=={target}"
    return f"{PACKAGE} @ git+{_DYNAMICAL_CATALOG_REPO}@{target}"


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


@pytest.mark.integration
@pytest.mark.parametrize(
    "target",
    [pytest.param(t["target"], id=t["id"]) for t in _TARGETS],
)
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


# --- Sanity guards on the discovered target set ---------------------------


def test_pypi_discovery_returns_at_least_one_release() -> None:
    """PyPI fetch + version filtering must yield at least one supported
    release. A zero-length result almost certainly means PyPI changed its
    response shape, MIN_VERSION crept above every published version, or
    every release got yanked — any of which silently disables the
    *entire* compat job.
    """
    releases = fetch_releases()
    assert releases, (
        f"No PyPI releases of {PACKAGE} matched the filter; "
        f"compat job would run only against canary refs."
    )


def test_canary_refs_are_plausible_git_refs() -> None:
    """CANARY_REFS get interpolated into a `pip install … @ git+…@<ref>`
    spec and a workflow matrix value, so simple branch/tag names only —
    no whitespace, no shell metacharacters.
    """
    pattern = re.compile(r"^[A-Za-z0-9._/-]+$")
    bad = [r for r in CANARY_REFS if not pattern.match(r)]
    assert not bad, f"Suspicious git refs in CANARY_REFS: {bad}"


def test_compat_matrix_script_is_executable_with_bare_python() -> None:
    """The workflow's `discover` job runs `scripts/compat_matrix.py` with
    a bare Python (no `uv sync`). If it ever grows a third-party import,
    that job will fail. Re-run the script in a clean subprocess via the
    current interpreter and assert it emits a parseable matrix=… line.
    """
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SCRIPTS_DIR / "compat_matrix.py")],
        check=True,
        capture_output=True,
        text=True,
    )
    line = result.stdout.strip()
    assert line.startswith("matrix="), f"unexpected output: {line!r}"
    matrix = json.loads(line[len("matrix=") :])
    entries = matrix.get("include")
    assert entries, f"matrix has no entries: {matrix!r}"
    # Every entry must carry the three keys the workflow consumes.
    for entry in entries:
        assert {"target", "id", "allow-failure"} <= entry.keys(), entry
        assert entry["id"] == safe_id(entry["target"])
