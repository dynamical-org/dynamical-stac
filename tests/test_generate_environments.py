from __future__ import annotations

import pathlib
from collections.abc import Callable
from typing import Any

import pytest

import generate
from catalog import CATALOG_ITEMS, CatalogItem


def _fake_generate(fail_on: str | None = None) -> Callable[..., None]:
    def fake(output_dir: pathlib.Path, **kwargs: object) -> None:
        if output_dir.name == fail_on:
            raise RuntimeError("store unreachable")
        output_dir.mkdir(parents=True, exist_ok=True)
        (
            output_dir
            / generate.stac_environment(str(kwargs["environment"])).root_filename
        ).write_text(str(kwargs["root_href"]))

    return fake


def test_environments_include_production_client_ranges() -> None:
    assert [(t.directory, t.name) for t in generate.STAC_ENVIRONMENTS] == [
        ("stac", "production"),
        ("stac-staging", "staging"),
        ("stac-test", "test"),
        ("stac", "0.4.0-0.5.0"),
        ("stac", "0.7.0-0.8.0"),
    ]
    for environment in generate.STAC_ENVIRONMENTS:
        assert environment.root_href == f"https://{environment.directory}.dynamical.org"


def test_generate_environments_opens_every_store_once_and_ignores_the_environment(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    loads: list[list[str]] = []
    calls: list[dict[str, Any]] = []
    monkeypatch.setenv("STAC_ROOT_HREF", "https://elsewhere.example")
    monkeypatch.setattr(
        generate,
        "_load_datasets",
        lambda items: loads.append([i.id for i in items]) or {"loaded": True},
    )
    fake = _fake_generate()
    monkeypatch.setattr(
        generate, "generate", lambda out, **kw: (calls.append(kw), fake(out, **kw))
    )

    generate.generate_environments(tmp_path)

    assert loads == [[item.id for item in CATALOG_ITEMS]]
    assert all(call["loaded"] == {"loaded": True} for call in calls)
    assert [call["environment"] for call in calls] == [
        environment.name for environment in generate.STAC_ENVIRONMENTS
    ]
    for environment in generate.STAC_ENVIRONMENTS:
        assert (
            tmp_path / environment.directory / environment.root_filename
        ).read_text() == (environment.root_href)
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "stac",
        "stac-staging",
        "stac-test",
    ]


def test_generate_environments_drops_files_an_environment_no_longer_has(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stale = tmp_path / "stac-staging" / "retired-dataset" / "collection.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("{}")
    monkeypatch.setattr(generate, "_load_datasets", lambda items: {})
    monkeypatch.setattr(generate, "generate", _fake_generate())

    generate.generate_environments(tmp_path)

    assert not stale.exists()


def test_a_failing_environment_leaves_every_committed_tree_untouched(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for environment in generate.STAC_ENVIRONMENTS:
        (tmp_path / environment.directory).mkdir(exist_ok=True)
        (tmp_path / environment.directory / environment.root_filename).write_text(
            "committed"
        )
    monkeypatch.setattr(generate, "_load_datasets", lambda items: {})
    monkeypatch.setattr(generate, "generate", _fake_generate(fail_on="stac-test"))

    with pytest.raises(RuntimeError, match="store unreachable"):
        generate.generate_environments(tmp_path)

    for environment in generate.STAC_ENVIRONMENTS:
        assert (
            tmp_path / environment.directory / environment.root_filename
        ).read_text() == "committed"
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "stac",
        "stac-staging",
        "stac-test",
    ]


@pytest.mark.parametrize(
    "environment", [environment.name for environment in generate.STAC_ENVIRONMENTS]
)
def test_single_environment_generate_opens_only_that_environments_stores(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, environment: str
) -> None:
    opened: list[str] = []

    def stop_after_recording(items: list[CatalogItem]) -> None:
        opened.extend(item.id for item in items)
        raise RuntimeError("recorded")

    monkeypatch.setattr(generate, "_load_datasets", stop_after_recording)
    with pytest.raises(RuntimeError, match="recorded"):
        generate.generate(tmp_path, environment=environment)

    assert opened == [i.id for i in CATALOG_ITEMS if environment in i.environments]


def test_a_failure_while_swapping_restores_every_tree(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for environment in generate.STAC_ENVIRONMENTS:
        (tmp_path / environment.directory).mkdir(exist_ok=True)
        (tmp_path / environment.directory / environment.root_filename).write_text(
            "committed"
        )
    monkeypatch.setattr(generate, "_load_datasets", lambda items: {})
    monkeypatch.setattr(generate, "generate", _fake_generate())

    real_rename = pathlib.Path.rename
    installs: list[str] = []

    def rename_failing_on_second_install(
        src: pathlib.Path, dst: pathlib.Path
    ) -> pathlib.Path:
        installing = dst.parent == tmp_path and src.name == dst.name
        if installing:
            installs.append(dst.name)
            if len(installs) == 2:
                raise OSError("disk trouble")
        return real_rename(src, dst)

    monkeypatch.setattr(pathlib.Path, "rename", rename_failing_on_second_install)

    with pytest.raises(OSError, match="disk trouble"):
        generate.generate_environments(tmp_path)

    assert installs == ["stac", "stac-staging"]
    for environment in generate.STAC_ENVIRONMENTS:
        assert (
            tmp_path / environment.directory / environment.root_filename
        ).read_text() == "committed"
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "stac",
        "stac-staging",
        "stac-test",
    ]
