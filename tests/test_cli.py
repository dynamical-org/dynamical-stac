from __future__ import annotations

import pathlib

import pytest

import cli


def test_main_generate_writes_every_environment_into_the_repo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[pathlib.Path] = []
    monkeypatch.setattr(cli, "generate_environments", calls.append)

    rc = cli.main(["generate"])

    assert rc == 0
    assert calls == [cli.REPO_ROOT]
    assert (cli.REPO_ROOT / "stac" / "catalog.json").is_file()


def test_main_generate_accepts_explicit_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    calls: list[pathlib.Path] = []
    monkeypatch.setattr(cli, "generate", calls.append)

    rc = cli.main(["generate", "--output", str(tmp_path)])

    assert rc == 0
    assert calls == [tmp_path]


def test_main_upload_invokes_upload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    calls: list[pathlib.Path] = []
    monkeypatch.setattr(cli, "upload", calls.append)

    rc = cli.main(["upload", str(tmp_path)])

    assert rc == 0
    assert calls == [tmp_path]


def test_main_unknown_command_returns_nonzero() -> None:
    assert cli.main(["bogus"]) == 1
    assert cli.main([]) == 1


@pytest.mark.parametrize("name", ["production", "staging", "test"])
@pytest.mark.parametrize("environment_first", [False, True])
def test_main_generate_selects_one_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    name: str,
    environment_first: bool,
) -> None:
    calls: list[tuple[pathlib.Path, str]] = []
    monkeypatch.setattr(
        cli, "generate", lambda out, environment: calls.append((out, environment))
    )
    args = (
        ["--environment", name, "--output", str(tmp_path)]
        if environment_first
        else ["--output", str(tmp_path), "--environment", name]
    )
    assert cli.main(["generate", *args]) == 0
    assert calls == [(tmp_path, name)]


def test_main_rejects_unknown_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[pathlib.Path] = []
    monkeypatch.setattr(cli, "generate", calls.append)
    assert cli.main(["generate", "--output", "out", "--environment", "typo"]) == 1
    assert calls == []
