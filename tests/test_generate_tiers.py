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
        output_dir.mkdir(parents=True)
        (output_dir / "catalog.json").write_text(str(kwargs["root_href"]))

    return fake


def test_tiers_are_production_staging_and_test() -> None:
    assert [
        (t.directory, t.include_staging, t.include_test) for t in generate.TIERS
    ] == [
        ("stac", False, False),
        ("stac-staging", True, False),
        ("stac-test", True, True),
    ]
    for tier in generate.TIERS:
        assert tier.root_href == f"https://{tier.directory}.dynamical.org"


def test_generate_tiers_opens_every_store_once_and_ignores_the_environment(
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

    generate.generate_tiers(tmp_path)

    assert loads == [[item.id for item in CATALOG_ITEMS]]
    assert all(call["loaded"] == {"loaded": True} for call in calls)
    for tier in generate.TIERS:
        assert (tmp_path / tier.directory / "catalog.json").read_text() == (
            tier.root_href
        )
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "stac",
        "stac-staging",
        "stac-test",
    ]


def test_generate_tiers_drops_files_a_tier_no_longer_has(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stale = tmp_path / "stac-staging" / "retired-dataset" / "collection.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("{}")
    monkeypatch.setattr(generate, "_load_datasets", lambda items: {})
    monkeypatch.setattr(generate, "generate", _fake_generate())

    generate.generate_tiers(tmp_path)

    assert not stale.exists()


def test_a_failing_tier_leaves_every_committed_tree_untouched(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for tier in generate.TIERS:
        (tmp_path / tier.directory).mkdir()
        (tmp_path / tier.directory / "catalog.json").write_text("committed")
    monkeypatch.setattr(generate, "_load_datasets", lambda items: {})
    monkeypatch.setattr(generate, "generate", _fake_generate(fail_on="stac-test"))

    with pytest.raises(RuntimeError, match="store unreachable"):
        generate.generate_tiers(tmp_path)

    for tier in generate.TIERS:
        assert (tmp_path / tier.directory / "catalog.json").read_text() == "committed"
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "stac",
        "stac-staging",
        "stac-test",
    ]


def test_single_tier_generate_opens_only_that_tiers_stores(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[str] = []

    def stop_after_recording(items: list[CatalogItem]) -> None:
        opened.extend(item.id for item in items)
        raise RuntimeError("recorded")

    monkeypatch.setattr(generate, "_load_datasets", stop_after_recording)
    with pytest.raises(RuntimeError, match="recorded"):
        generate.generate(tmp_path, include_staging=False, include_test=False)

    assert opened == [i.id for i in CATALOG_ITEMS if not (i.staging or i.test)]
