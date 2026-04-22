from __future__ import annotations

import pathlib

import pytest

import cli


def test_main_generate_invokes_generate(
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


def test_main_generate_and_upload_uses_shared_tmpdir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generate_paths: list[pathlib.Path] = []
    upload_paths: list[pathlib.Path] = []
    monkeypatch.setattr(cli, "generate", lambda out: generate_paths.append(out))
    monkeypatch.setattr(cli, "upload", lambda d: upload_paths.append(d))

    rc = cli.main(["generate-and-upload"])

    assert rc == 0
    assert len(generate_paths) == 1
    assert generate_paths == upload_paths


def test_main_unknown_command_returns_nonzero() -> None:
    assert cli.main(["bogus"]) == 1
    assert cli.main([]) == 1
