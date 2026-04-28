#!/usr/bin/env python3
"""Build the GitHub Actions matrix for the `compat` job: every non-yanked
stable `dynamical-catalog` release on PyPI (>= MIN_VERSION) plus the `main`
canary branch.

Two callers:

* `tests/test_released_catalog_read.py` imports the helpers below to
  parametrize its compat test against the same set of targets.
* `.github/workflows/test.yml`'s `discover` job runs this script and pipes
  `matrix=…` into `$GITHUB_OUTPUT` so the `compat` job's matrix is built
  fresh on every run — no manual maintenance when a new release ships, and
  no chance of test/workflow drift.

Stdlib-only on purpose: the workflow can run it with a bare Python without
`uv sync`, keeping the discover step ~1s instead of 30s+.

Maintenance:
* Bump `MIN_VERSION` to drop support for an old release without yanking
  it on PyPI. Versions below the floor are silently excluded.
* Add long-lived non-PyPI git refs to `CANARY_REFS` (allow-failure: true).
* PyPI releases at or above `MIN_VERSION` are non-blocking by default —
  see `_RELEASE_ALLOW_FAILURE` if a specific release ever needs to be
  treated as a canary instead.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request

PACKAGE = "dynamical-catalog"

# Drop releases older than this. Bump when we stop guaranteeing backwards
# compatibility for an older `dynamical-catalog` (e.g. when its consumers
# are extinct in the wild). 0.5.0 is the current floor — that's the first
# release we officially announced as a supported access method.
MIN_VERSION = "0.5.0"

# Long-lived non-PyPI refs to also exercise. `main` catches breakage in
# unreleased dynamical-catalog before it ships to users — but it's a canary,
# not a support contract, so it can fail without blocking PRs.
CANARY_REFS = ["main"]

# Releases that should be tested but allowed to fail (e.g. a known-broken
# legacy release we still want signal on but won't block merges for). Empty
# by default — every PyPI release at or above MIN_VERSION is treated as a
# support contract.
_RELEASE_ALLOW_FAILURE: frozenset[str] = frozenset()

_STABLE_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
_PYPI_TIMEOUT_SECONDS = 15


def _version_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.split("."))


def fetch_releases(package: str = PACKAGE, min_version: str = MIN_VERSION) -> list[str]:
    """Return PyPI stable releases >= `min_version`, sorted ascending,
    excluding pre-releases and fully-yanked versions.
    """
    url = f"https://pypi.org/pypi/{package}/json"
    with urllib.request.urlopen(url, timeout=_PYPI_TIMEOUT_SECONDS) as resp:  # noqa: S310
        data = json.loads(resp.read())

    floor = _version_tuple(min_version)
    out: list[str] = []
    for version, files in data["releases"].items():
        if not _STABLE_VERSION_RE.match(version):
            continue  # skip 0.5.0a1, 0.5.0rc1, dev releases, etc.
        # PyPI returns an empty file list when every distribution has been
        # removed; if some are yanked but others aren't, treat as available
        # (matches `pip install` behaviour).
        if not files or all(f.get("yanked") for f in files):
            continue
        if _version_tuple(version) < floor:
            continue
        out.append(version)
    return sorted(out, key=_version_tuple)


def safe_id(target: str) -> str:
    """A pytest parametrize id and GHA matrix key safe for `-k` filters
    and shell interpolation: alphanumerics + underscore only.

    `0.5.0` -> `0_5_0`; `main` -> `main`; `release/foo` -> `release_foo`.
    """
    return re.sub(r"[^A-Za-z0-9_]", "_", target)


def build_targets() -> list[dict[str, object]]:
    """The full target list (PyPI releases + canary refs) with metadata."""
    releases = fetch_releases()
    return [
        *(
            {
                "target": v,
                "id": safe_id(v),
                "allow-failure": v in _RELEASE_ALLOW_FAILURE,
            }
            for v in releases
        ),
        *({"target": r, "id": safe_id(r), "allow-failure": True} for r in CANARY_REFS),
    ]


def main() -> None:
    matrix = {"include": build_targets()}
    sys.stdout.write(f"matrix={json.dumps(matrix)}\n")


if __name__ == "__main__":
    main()
