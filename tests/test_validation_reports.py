"""Integration test: every production dataset has a live validation report.

Each collection advertises its validation report as an ``about`` link titled
"Validation report", pointing at
``https://dynamical.org/catalog/{id}/validation/``. That page is rendered by
the website from the reformatter's validation output, so the link can go stale
independently of this repo — a dataset renamed here, or a report that never
got published, leaves an ``about`` link that 404s or renders an empty shell.

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


def _production_collections() -> list[tuple[str, str, str]]:
    """(id, title, validation report href) for each committed collection."""
    out: list[tuple[str, str, str]] = []
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
        out.append((collection["id"], collection["title"], hrefs[0]))
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
    ("collection_id", "title", "href"),
    _PRODUCTION_COLLECTIONS,
    ids=[c[0] for c in _PRODUCTION_COLLECTIONS],
)
def test_validation_report_url_renders_report(
    collection_id: str, title: str, href: str
) -> None:
    assert href == f"https://dynamical.org/catalog/{collection_id}/validation/"
    try:
        html = _fetch(href)
    except urllib.error.HTTPError as e:
        pytest.fail(f"{href} returned {e.code}")

    # The heading is built from the dataset name, so a rename here that the
    # website hasn't picked up (or a report published under the wrong id)
    # shows up as a mismatch rather than a silent 200.
    assert f"<h1>{title} validation report</h1>" in html, (
        f"{href} is missing the '{title} validation report' heading"
    )
    assert '<h2 id="summary">Summary</h2>' in html, (
        f"{href} is missing the Summary section"
    )
