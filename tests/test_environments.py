from __future__ import annotations

import json
import pathlib

import pytest
from pydantic import ValidationError

from catalog import CATALOG_ITEMS, CatalogItem
from generate import _select_items


@pytest.mark.parametrize("environment", ["production", "staging", "test"])
def test_selection_does_not_imply_other_environments(environment: str) -> None:
    items = [
        CatalogItem.model_validate(
            {**CATALOG_ITEMS[0].model_dump(), "environments": [name]}
        )
        for name in ("production", "staging", "test")
    ]
    assert _select_items(items, environment=environment) == [
        item for item in items if item.environments == (environment,)
    ]


@pytest.mark.parametrize("environments", [[], ["typo"], ["staging", "staging"]])
def test_invalid_environment_lists_are_rejected(environments: list[str]) -> None:
    fields = CATALOG_ITEMS[0].model_dump()
    fields["environments"] = environments
    with pytest.raises(ValidationError):
        CatalogItem.model_validate(fields)


def test_environment_list_is_required() -> None:
    fields = CATALOG_ITEMS[0].model_dump()
    fields.pop("environments", None)
    with pytest.raises(ValidationError, match="environments"):
        CatalogItem.model_validate(fields)


@pytest.mark.parametrize(
    ("environments", "host"),
    [
        (["production"], "stac"),
        (["staging"], "stac-staging"),
        (["test"], "stac-test"),
        (["test", "production"], "stac"),
        (["test", "staging"], "stac-staging"),
    ],
)
def test_example_catalog_url_uses_a_declared_environment(
    environments: list[str], host: str
) -> None:
    fields = {**CATALOG_ITEMS[0].model_dump(), "environments": environments}
    item = CatalogItem.model_validate(fields)
    assert item.catalog_url == f"https://{host}.dynamical.org/catalog.json"


@pytest.mark.parametrize("environments", [["production"], ["test", "production"]])
def test_production_membership_requires_notebooks(environments: list[str]) -> None:
    fields = {
        **CATALOG_ITEMS[0].model_dump(),
        "environments": environments,
        "notebooks": (),
    }
    with pytest.raises(ValidationError, match="must declare at least one notebook"):
        CatalogItem.model_validate(fields)


@pytest.mark.parametrize(
    ("subset_directory", "superset_directory"),
    [("stac", "stac-staging"), ("stac-staging", "stac-test")],
)
def test_published_catalog_memberships_are_nested(
    subset_directory: str, superset_directory: str
) -> None:
    # This is a policy for the published catalogs, not implicit inheritance.
    repo_root = pathlib.Path(__file__).resolve().parents[1]

    def collection_ids(directory: str) -> set[str]:
        root = json.loads((repo_root / directory / "catalog.json").read_text())
        return {
            pathlib.PurePosixPath(link["href"]).parent.name
            for link in root["links"]
            if link["rel"] == "child"
        }

    missing = collection_ids(subset_directory) - collection_ids(superset_directory)
    assert not missing, (
        f"{superset_directory} is missing {subset_directory} collections: {sorted(missing)}"
    )


@pytest.mark.parametrize(
    ("subset", "superset"),
    [("production", "staging"), ("staging", "test")],
)
def test_catalog_item_memberships_follow_publication_policy(
    subset: str, superset: str
) -> None:
    missing = [
        item.id
        for item in CATALOG_ITEMS
        if subset in item.environments and superset not in item.environments
    ]
    assert not missing, f"{subset} items must explicitly list {superset}: {missing}"


def test_environment_membership_is_immutable() -> None:
    item = CatalogItem.model_validate(CATALOG_ITEMS[0].model_dump())
    assert isinstance(item.environments, tuple)
    with pytest.raises(ValidationError, match="frozen"):
        item.environments += ("test",)
