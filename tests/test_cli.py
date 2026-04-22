from __future__ import annotations

import pathlib

import pytest

import cli


def test_main_generate_defaults_to_stac_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[pathlib.Path] = []
    monkeypatch.setattr(cli, "generate", lambda out: calls.append(out))

    rc = cli.main(["generate"])

    assert rc == 0
    assert calls == [cli.DEFAULT_OUTPUT_DIR]


def test_main_generate_accepts_explicit_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    calls: list[pathlib.Path] = []
    monkeypatch.setattr(cli, "generate", lambda out: calls.append(out))

    rc = cli.main(["generate", "--output", str(tmp_path)])

    assert rc == 0
    assert calls == [tmp_path]


def test_main_upload_invokes_upload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    calls: list[pathlib.Path] = []
    monkeypatch.setattr(cli, "upload", lambda d: calls.append(d))

    rc = cli.main(["upload", str(tmp_path)])

    assert rc == 0
    assert calls == [tmp_path]


def test_main_unknown_command_returns_nonzero() -> None:
    assert cli.main(["bogus"]) == 1
    assert cli.main([]) == 1
