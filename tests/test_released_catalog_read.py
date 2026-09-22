"""Integration test: every supported `dynamical-catalog` release on PyPI
must open and read every collection in its production environment, while the
`main` canary must open
the staging-inclusive locally generated STAC.

`tests/test_catalog_read.py` exercises whatever `dynamical-catalog` is
installed into the project venv via the in-process
`dynamical_catalog_fixture`. That misses regressions against releases
still in the wild — the kind introduced when we dropped the `zarr` asset
and stopped emitting `icechunk:storage.{bucket,prefix,region}`, both of
which silently broke 0.3.0 consumers.

Each target is installed by itself into an isolated env via `uv run --with`;
the harness does not supplement the client's declared dependencies. The check
runs in a subprocess so it can't share import state with the project venv.
Released versions read the production-only root because staging may
exercise a contract that has not shipped yet; canary refs read every staging
collection so that new contract is proven before release. The full `open + read
first variable` flow runs against the just-generated STAC.

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

from catalog import CATALOG_ITEMS
from environments import environment_for_client

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = REPO_ROOT / "scripts"

# Single source of truth for the compat target set, shared with
# .github/workflows/test.yml's `discover` job.
sys.path.insert(0, str(_SCRIPTS_DIR))
from compat_matrix import (  # noqa: E402
    PACKAGE,
    build_targets,
    client_read_command,
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


def _catalog_filename(target: str) -> str:
    if re.fullmatch(r"\d+\.\d+\.\d+", target):
        return f"production/{environment_for_client(target).root_filename}"
    return "catalog.json"


_HARNESS = textwrap.dedent(
    """
    import json, math, sys
    import dynamical_catalog
    from dynamical_catalog import _stac

    catalog_url, collection_ids_json = sys.argv[1], sys.argv[2]
    collection_ids = json.loads(collection_ids_json)

    _stac.STAC_CATALOG_URL = catalog_url
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

    catalog_dir, root_url = served_catalog
    environment = (
        environment_for_client(target).name
        if re.fullmatch(r"\d+\.\d+\.\d+", target)
        else "staging"
    )
    # Read only the collections explicitly assigned to this environment.
    collection_ids = [
        item.id for item in CATALOG_ITEMS if environment in item.environments
    ]
    root = json.loads((catalog_dir / _catalog_filename(target)).read_text())
    assert sorted(
        pathlib.PurePosixPath(link["href"]).parent.name
        for link in root["links"]
        if link["rel"] == "child"
    ) == sorted(collection_ids)
    assert collection_ids
    harness = tmp_path / "harness.py"
    harness.write_text(_HARNESS)

    subprocess.run(  # noqa: S603
        client_read_command(
            uv,
            install_spec=_install_spec(target),
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}",
            harness=str(harness),
            catalog_url=f"{root_url}/{_catalog_filename(target)}",
            collection_ids=collection_ids,
        ),
        check=True,
    )
