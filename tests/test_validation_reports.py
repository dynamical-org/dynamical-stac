"""Integration test: every production dataset has a published validation report.

Each collection advertises its validation report as an ``about`` link titled
"Validation report", pointing at
``https://dynamical.org/catalog/{id}/validation/``. The website renders that
page from the report the reformatter publishes to the
``dataset-validation-reports`` bucket under the dataset id, so this checks the
bucket rather than the rendered page.

Checking the source rather than the rendered page keeps this test meaningful
for a dataset being added: the website can only render a collection already in
the production catalog, so asserting against the page would fail on exactly the
change that publishes it, and could only pass after the merge it blocks. The
bucket has no such ordering — the report is published before the catalog change
ships. Both failures the rendered page would have caught still surface here,
because the report is keyed by dataset id: a report that was never published
404s, and so does a dataset renamed here without the report being republished
under its new id.

Parametrized over the committed ``stac/`` tree, which is the production
catalog: staging-only items aren't in it (see ``generate._select_items``), so
they're skipped without a separate filter. ``test_stac_drift.py`` guarantees
the committed tree matches what ``generate()`` produces.
"""

from __future__ import annotations

import json
import pathlib
import urllib.error
import urllib.request

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMITTED_STAC = REPO_ROOT / "stac"

_VALIDATION_LINK_TITLE = "Validation report"
_REPORTS_BASE_URL = "https://dataset-validation-reports.dynamical.org"


def _production_collections() -> list[tuple[str, str]]:
    """(id, validation report href) for each committed collection."""
    out: list[tuple[str, str]] = []
    for path in sorted(COMMITTED_STAC.glob("*/collection.json")):
        collection = json.loads(path.read_text())
        hrefs = [
            link["href"]
            for link in collection["links"]
            if link.get("title") == _VALIDATION_LINK_TITLE
        ]
        assert len(hrefs) == 1, (
            f"{path.parent.name} has {len(hrefs)} {_VALIDATION_LINK_TITLE!r} links"
        )
        out.append((collection["id"], hrefs[0]))
    return out


_PRODUCTION_COLLECTIONS = _production_collections()

assert _PRODUCTION_COLLECTIONS, "no committed collections found"


def _fetch(url: str) -> str:
    req = urllib.request.Request(url)  # noqa: S310
    req.add_header("User-Agent", "dynamical-stac-tests")
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        return resp.read().decode("utf-8", errors="replace")


@pytest.mark.integration
@pytest.mark.parametrize(
    ("collection_id", "href"),
    _PRODUCTION_COLLECTIONS,
    ids=[c[0] for c in _PRODUCTION_COLLECTIONS],
)
def test_validation_report_is_published(collection_id: str, href: str) -> None:
    assert href == f"https://dynamical.org/catalog/{collection_id}/validation/"

    report_url = f"{_REPORTS_BASE_URL}/{collection_id}/latest/validation_report.html"
    try:
        html = _fetch(report_url)
    except urllib.error.HTTPError as e:
        pytest.fail(
            f"{report_url} returned {e.code}; the website renders "
            f"{href} from this report, so publish it for {collection_id!r} "
            f"(or republish it under that id if the dataset was renamed)"
        )

    assert '<h2 id="summary">Summary</h2>' in html, (
        f"{report_url} is missing the Summary section"
    )
