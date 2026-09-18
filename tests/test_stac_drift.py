"""Integration test: committed stac/ must match what generate() produces today.

A mismatch has two possible causes, and they need different responses:

* **Store drift.** A dataset's Icechunk store changed after the last
  `scripts/generate` (a reformatters deploy renamed a variable, added an
  attribute comment, extended an extent). Nothing in this repo is wrong; the
  committed tree is stale and needs a regen commit. This is also the only way
  `main` itself can go red, since every PR proves its own tree matches the
  stores at the time it ran.
* **An unregenerated change.** This branch edited `src/` (a `CatalogItem`,
  prose, the generator) and did not run `scripts/generate`, so the rendered
  catalog no longer matches the committed one.

To tell them apart, a mismatch triggers a second generation from the base
ref's `src/` (default `origin/main`; `STAC_DRIFT_BASE_REF` overrides it,
`STAC_DRIFT_NO_BASE=1` skips the classification) compared against the base
ref's own `stac/`. Files that mismatch there too drifted in the store;
whatever remains was changed by this branch. On a push to `main`, HEAD is the
base, so every mismatch is store drift, and the workflow opens an issue with
that message instead of leaving `main` red without a reason.
"""

from __future__ import annotations

import io
import json
import os
import pathlib
import subprocess
import sys
import tarfile

import pytest

from generate import generate

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMITTED_STAC = REPO_ROOT / "stac"

_DEFAULT_BASE_REF = "origin/main"


def _compare(committed: pathlib.Path, generated: pathlib.Path) -> dict[str, list[str]]:
    """Files present on one side only, plus files whose JSON differs."""
    committed_files = {p.relative_to(committed) for p in committed.rglob("*.json")}
    generated_files = {p.relative_to(generated) for p in generated.rglob("*.json")}
    mismatches = [
        str(rel)
        for rel in sorted(committed_files & generated_files)
        if json.loads((committed / rel).read_text())
        != json.loads((generated / rel).read_text())
    ]
    return {
        "missing": sorted(str(p) for p in generated_files - committed_files),
        "extra": sorted(str(p) for p in committed_files - generated_files),
        "mismatch": mismatches,
    }


def _base_ref() -> str | None:
    """The ref to classify drift against, or None to skip classification."""
    if os.environ.get("STAC_DRIFT_NO_BASE"):
        return None
    ref = os.environ.get("STAC_DRIFT_BASE_REF", _DEFAULT_BASE_REF)
    ok = subprocess.run(  # noqa: S603
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],  # noqa: S607
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    return ref if ok.returncode == 0 else None


def _store_drift(ref: str, workdir: pathlib.Path) -> dict[str, list[str]]:
    """Regenerate from `ref`'s src/ and compare with `ref`'s committed stac/.

    Anything that differs there changed in a store, not on this branch.
    """
    archive = subprocess.run(  # noqa: S603
        ["git", "archive", "--format=tar", ref, "src", "stac"],  # noqa: S607
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
    )
    base = workdir / "base"
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
        tar.extractall(base, filter="data")
    generated = workdir / "base-generated"
    subprocess.run(  # noqa: S603
        [
            sys.executable,
            str(base / "src" / "__main__.py"),
            "generate",
            "--output",
            str(generated),
        ],
        cwd=base,
        check=True,
    )
    return _compare(base / "stac", generated)


def _describe(label: str, diff: dict[str, list[str]]) -> str:
    parts = [f"{kind} {files}" for kind, files in diff.items() if files]
    return f"{label}: {'; '.join(parts)}" if parts else ""


@pytest.mark.integration
def test_committed_stac_matches_generated(tmp_path: pathlib.Path) -> None:
    generate(tmp_path / "generated")
    diff = _compare(COMMITTED_STAC, tmp_path / "generated")
    if not any(diff.values()):
        return

    ref = _base_ref()
    if ref is None:
        pytest.fail(
            f"stac/ does not match generate() and no base ref is available to "
            f"say why. {_describe('Differences', diff)}. Run `scripts/generate` "
            f"and commit."
        )

    drift = _store_drift(ref, tmp_path)
    drifted = {kind: set(files) for kind, files in drift.items()}
    store = {
        kind: [f for f in files if f in drifted[kind]] for kind, files in diff.items()
    }
    branch = {
        kind: [f for f in files if f not in drifted[kind]]
        for kind, files in diff.items()
    }

    lines = [
        _describe(
            f"STORE DRIFT (not caused by this branch: {ref}'s own src/ no longer "
            f"reproduces {ref}'s stac/, so a dataset store changed after the last "
            f"regen and main needs a regen commit)",
            store,
        ),
        _describe(
            "UNREGENERATED CHANGE (this branch's src/ renders differently from "
            "its committed stac/)",
            branch,
        ),
    ]
    pytest.fail(
        "stac/ does not match generate(). Run `scripts/generate` and commit "
        "the result.\n" + "\n".join(line for line in lines if line)
    )
