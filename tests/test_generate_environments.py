from __future__ import annotations

import datetime as dt
import json
import pathlib
from collections.abc import Callable
from typing import Any

import pystac
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


@pytest.mark.parametrize(
    "environment", [environment.name for environment in generate.STAC_ENVIRONMENTS]
)
def test_root_catalog_links_a_png_icon(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, environment: str
) -> None:
    monkeypatch.setattr(generate, "_select_items", lambda *_, **__: [])
    generate.generate(tmp_path, environment=environment, loaded={})

    publication = generate.stac_environment(environment)
    root = json.loads((tmp_path / publication.root_filename).read_text())
    icons = [link for link in root["links"] if link["rel"] == "icon"]
    assert icons == [
        {
            "rel": "icon",
            "href": generate.CATALOG_ICON_URL,
            "type": "image/png",
            "title": "dynamical.org",
        }
    ]


def test_updated_keeps_the_committed_stamp_when_nothing_else_changed(
    tmp_path: pathlib.Path,
) -> None:
    committed = tmp_path / "collection.json"
    committed.write_text(json.dumps({"id": "x", "updated": "2026-01-01T00:00:00Z"}))

    assert generate._updated({"id": "x"}, committed, "2026-10-13T00:00:00Z") == (
        "2026-01-01T00:00:00Z"
    )


@pytest.mark.parametrize(
    "committed_json",
    [
        None,
        {"id": "x"},
        {"id": "y", "updated": "2026-01-01T00:00:00Z"},
    ],
    ids=["new-file", "never-stamped", "changed"],
)
def test_updated_stamps_now_for_new_or_changed_metadata(
    tmp_path: pathlib.Path, committed_json: dict[str, str] | None
) -> None:
    committed = tmp_path / "collection.json"
    if committed_json is not None:
        committed.write_text(json.dumps(committed_json))

    assert generate._updated({"id": "x"}, committed, "2026-10-13T00:00:00Z") == (
        "2026-10-13T00:00:00Z"
    )


def _empty_root(
    output_dir: pathlib.Path, environment: str, now: dt.datetime
) -> dict[str, Any]:
    generate.generate(output_dir, environment=environment, loaded={}, now=now)
    publication = generate.stac_environment(environment)
    return json.loads((output_dir / publication.root_filename).read_text())


@pytest.mark.parametrize(
    "environment", [environment.name for environment in generate.STAC_ENVIRONMENTS]
)
def test_regenerating_an_unchanged_root_keeps_its_updated_stamp(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, environment: str
) -> None:
    monkeypatch.setattr(generate, "_select_items", lambda *_, **__: [])
    first = dt.datetime(2026, 10, 1, 12, 30, tzinfo=dt.UTC)

    assert _empty_root(tmp_path, environment, first)["updated"] == (
        "2026-10-01T12:30:00Z"
    )
    later = first + dt.timedelta(days=3)
    assert _empty_root(tmp_path, environment, later)["updated"] == (
        "2026-10-01T12:30:00Z"
    )


def test_root_updated_is_the_latest_collection_stamp(tmp_path: pathlib.Path) -> None:
    catalog = pystac.Catalog(id="root", description="d")
    for collection_id in ("a", "b"):
        collection = pystac.Collection(
            id=collection_id,
            description="d",
            extent=pystac.Extent(
                pystac.SpatialExtent([[0.0, 0.0, 1.0, 1.0]]),
                pystac.TemporalExtent([[dt.datetime(2020, 1, 1, tzinfo=dt.UTC), None]]),
            ),
        )
        catalog.add_child(collection)
    catalog.normalize_hrefs("https://stac.example")
    a = catalog.get_child("a")
    assert a is not None
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "collection.json").write_text(
        json.dumps({**a.to_dict(), "updated": "2026-03-01T00:00:00Z"})
    )
    (tmp_path / "catalog.json").write_text(
        json.dumps({**catalog.to_dict(), "updated": "2026-01-01T00:00:00Z"})
    )

    generate._stamp_updated(
        catalog,
        generate.stac_environment("production"),
        "https://stac.example",
        tmp_path,
        "2026-10-13T00:00:00Z",
    )

    b = catalog.get_child("b")
    assert b is not None
    assert a.extra_fields["updated"] == "2026-03-01T00:00:00Z"
    assert b.extra_fields["updated"] == "2026-10-13T00:00:00Z"
    assert catalog.extra_fields["updated"] == "2026-10-13T00:00:00Z"


@pytest.mark.parametrize(
    "environment", [environment.name for environment in generate.STAC_ENVIRONMENTS]
)
def test_root_catalog_links_its_sidecars(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, environment: str
) -> None:
    monkeypatch.setattr(generate, "_select_items", lambda *_, **__: [])
    root = _empty_root(tmp_path, environment, dt.datetime.now(dt.UTC))

    sidecars = [
        (link["rel"], link["href"], link["type"])
        for link in root["links"]
        if link["rel"] in {"describedby", "agents"}
    ]
    assert sidecars == [
        ("describedby", "./README.md", "text/markdown"),
        ("agents", "./AGENTS.md", "text/markdown"),
    ]
    assert (tmp_path / "README.md").read_text().startswith("# ")
    assert (tmp_path / "AGENTS.md").read_text().startswith("# ")
