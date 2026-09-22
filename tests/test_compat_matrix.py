from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

import pytest

from scripts.compat_matrix import (
    CANARY_REFS,
    PACKAGE,
    client_read_command,
    fetch_releases,
    safe_id,
)

_SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[1] / "scripts"


@pytest.mark.parametrize(
    "install_spec",
    [
        "dynamical-catalog==0.5.0",
        "dynamical-catalog @ git+https://github.com/dynamical-org/dynamical-catalog@main",
    ],
)
def test_read_command_installs_only_the_selected_client(install_spec: str) -> None:
    command = client_read_command(
        "uv",
        install_spec=install_spec,
        python_version="3.14",
        harness="harness.py",
        catalog_url="https://example.test/catalog.json",
        collection_ids=[],
    )
    assert command.count("--with") == 1
    assert command[command.index("--with") + 1] == install_spec
    assert "--isolated" in command
    assert "--no-project" in command


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
