from __future__ import annotations

import pystac

from catalog import DYNAMICAL_ORG, UpstreamSource
from models import STAC_EXTENSIONS
from sidecars import collection_agents, collection_readme
from tests.test_models import _valid_input


def _published(**overrides: object) -> pystac.Collection:
    collection = _valid_input(**overrides).to_pystac_collection()
    collection.normalize_hrefs("https://stac.example/test-dataset")
    return collection


def test_collection_declares_the_version_extension() -> None:
    extensions = _valid_input().to_pystac_collection().stac_extensions
    assert extensions == STAC_EXTENSIONS
    assert "https://stac-extensions.github.io/version/v1.2.0/schema.json" in extensions


def test_collection_links_its_sidecars_relatively() -> None:
    links = [
        (link.rel, link.href, link.media_type)
        for link in _valid_input().to_pystac_collection().links
        if link.rel in {"describedby", "agents"}
    ]
    assert links == [
        ("describedby", "./README.md", "text/markdown"),
        ("agents", "./AGENTS.md", "text/markdown"),
    ]


def test_readme_has_title_license_and_provenance() -> None:
    source = UpstreamSource(href="https://example.org/source", title="Upstream")  # type: ignore[arg-type]
    readme = collection_readme(_published(source=source))

    assert readme.startswith("# Test Dataset\n")
    assert "## License\n\nCC-BY-4.0. Test Attribution" in readme
    assert (
        "Produced by [NOAA NWS NCEP](https://www.weather.gov/ncep/). Processed and"
        " hosted by [dynamical.org](https://dynamical.org/)."
    ) in readme
    assert "Source: [Upstream](https://example.org/source)." in readme
    assert "### Section\n\ntest details" in readme


def test_readme_of_dynamical_org_produced_data_has_no_upstream() -> None:
    readme = collection_readme(_published(producer=DYNAMICAL_ORG))

    assert (
        "Produced, processed and hosted by [dynamical.org](https://dynamical.org/)."
    ) in readme
    assert "Source:" not in readme


def test_agents_lists_assets_examples_and_variables() -> None:
    agents = collection_agents(_published())

    assert agents.startswith("# Test Dataset: notes for agents\n")
    assert "| `icechunk` | `s3://test-bucket/test-prefix/` |" in agents
    assert (
        "| `icechunk-https` | `https://test-bucket.s3.us-west-2.amazonaws.com/test-prefix` |"
    ) in agents
    assert '`{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`' in agents
    assert 'ds = dynamical_catalog.open("x", chunks=None)' in agents
    assert "| `temp` | Temperature | K | latitude |" in agents
    assert "| `latitude` | spatial | -90.0 to 90.0 | degree_north |" in agents
