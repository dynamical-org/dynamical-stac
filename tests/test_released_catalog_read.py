"""Integration test: each *released* dynamical-catalog version on PyPI must
still open every collection in the locally generated STAC.

`tests/test_catalog_read.py` exercises whatever `dynamical-catalog` version is
installed into the project venv (today: the `icechunk-2` dev branch, per
`[tool.uv.sources]` in pyproject.toml). That misses regressions against
releases still in the wild — the kind introduced when we dropped the `zarr`
asset and stopped emitting `icechunk:storage.{bucket,prefix,region}`, both of
which silently broke 0.3.0 consumers.

This test pins to each real PyPI release and runs the full open+read flow
against the just-generated STAC, so the CI fails the moment a backwards-
incompatible change lands.

Each version is installed into an isolated env via `uv run --with` and the
check runs in a subprocess. When support for a release is dropped, remove the
entry from `SUPPORTED_RELEASES` and the matching `TODO(temporary)` shims in
src/models.py and src/catalog.py together.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import textwrap

import pytest

from catalog import _COLLECTION_IDS

SUPPORTED_RELEASES = ["0.3.0"]

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
@pytest.mark.parametrize("release", SUPPORTED_RELEASES)
def test_released_dynamical_catalog_opens_every_collection(
    served_catalog: tuple[pathlib.Path, str],
    release: str,
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
            f"dynamical-catalog=={release}",
            "python",
            str(harness),
            root_url,
            json.dumps(_COLLECTION_IDS),
        ],
        check=True,
    )
