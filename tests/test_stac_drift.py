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
ref's own `stac/`. Files that mismatch there too drifted in the store. Files
whose fresh output equals the base's committed file are just a branch that is
behind the base (only possible locally: CI checks out the PR merged into
`main`). Whatever remains was changed by this branch. On a push to `main`
or the daily schedule, HEAD is the base, so a mismatch reads as store drift
(the usual cause; a stale tree merged past the checks reads the same), and
the workflow opens an issue with that message instead of leaving `main` red
without a reason.

Known limits: the base's generator runs with this branch's environment, so a
dependency bump that changes rendering labels every file as store drift, and
one that breaks the base's generator drops back to the unclassified message.
A file whose store drifted and that this branch also edited is listed under
store drift only, and a dataset that exists only on this branch cannot be
classified as drift. `STAC_INCLUDE_STAGING` / `STAC_INCLUDE_TEST` apply to
both generations, so with either set the committed production tree fails as
store drift on every staging or test collection. Regenerating without them
fixes all of these.
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


def _same_as_base_commit(rel: str, generated: pathlib.Path, base: pathlib.Path) -> bool:
    """True when this tree's fresh output agrees with the base's committed
    tree about `rel`: the same content, or absent from both."""
    ours, theirs = generated / rel, base / "stac" / rel
    if not ours.is_file() and not theirs.is_file():
        return True
    return (
        ours.is_file()
        and theirs.is_file()
        and json.loads(ours.read_text()) == json.loads(theirs.read_text())
    )


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

    try:
        drift = _store_drift(ref, tmp_path)
    except (
        subprocess.CalledProcessError,
        OSError,
        tarfile.TarError,
        ValueError,
    ) as exc:
        pytest.fail(
            f"stac/ does not match generate(), and regenerating from {ref} with "
            f"this branch's environment failed ({exc}), so the cause cannot be "
            f"classified. {_describe('Differences', diff)}. Run `scripts/generate` "
            f"and commit."
        )

    drifted = {kind: set(files) for kind, files in drift.items()}
    store: dict[str, list[str]] = {kind: [] for kind in diff}
    behind: dict[str, list[str]] = {kind: [] for kind in diff}
    branch: dict[str, list[str]] = {kind: [] for kind in diff}
    for kind, files in diff.items():
        for f in files:
            if f in drifted[kind]:
                store[kind].append(f)
            elif _same_as_base_commit(f, tmp_path / "generated", tmp_path / "base"):
                behind[kind].append(f)
            else:
                branch[kind].append(f)

    lines = [
        _describe(
            f"STORE DRIFT (not caused by this branch: {ref}'s own src/ no longer "
            f"reproduces {ref}'s stac/, so a dataset store changed after the last "
            f"regen and main needs a regen commit; a file here may also carry "
            f"this branch's changes)",
            store,
        ),
        _describe(
            f"BEHIND BASE (this tree's fresh output already matches {ref}'s "
            f"committed stac/; merge {ref})",
            behind,
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
