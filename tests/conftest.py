from __future__ import annotations

import http.server
import json
import pathlib
import socketserver
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from catalog import CATALOG_ITEMS
from generate import generate


@contextmanager
def _serve(directory: pathlib.Path) -> Iterator[int]:
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, directory=str(directory), **kwargs)  # type: ignore[arg-type]

        def log_message(self, *_: object) -> None:
            pass

    with socketserver.TCPServer(("127.0.0.1", 0), Handler) as httpd:
        port: int = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            yield port
        finally:
            httpd.shutdown()


@pytest.fixture(scope="session")
def served_catalog(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[tuple[pathlib.Path, str]]:
    """Generate the catalog once per session and serve it over HTTP.

    `generate()` opens every catalog icechunk store from S3 and fetches every
    STAC extension schema. That's ~40s of network and it's identical for every
    integration test that needs a catalog — so we do it once and share.

    Includes staging items (but not test-tier fixtures, which have their own
    coverage in `test_test_catalog.py`) so the served catalog covers every
    `_COLLECTION_IDS` entry: the integration tests assert against that list
    (which spans staging items too), and staging datasets are still published
    to stac-staging, so they must generate and read correctly here.

    Also writes `catalog-production.json`, the same root with staging children
    removed, for `test_released_catalog_read.py`: released readers are held to
    the production contract only, while the `main` canary reads `catalog.json`.

    Yields (catalog_dir, root_url). Consumers must treat both as read-only.
    """
    tmp_path = tmp_path_factory.mktemp("served_catalog")
    with _serve(tmp_path) as port:
        root_url = f"http://127.0.0.1:{port}"
        generate(tmp_path, root_href=root_url, include_staging=True)
        root_path = tmp_path / "catalog.json"
        production_ids = {
            item.id for item in CATALOG_ITEMS if not (item.staging or item.test)
        }
        production_root = json.loads(root_path.read_text())
        production_root["links"] = [
            link
            for link in production_root["links"]
            if link.get("rel") != "child"
            or pathlib.PurePosixPath(link["href"]).parent.name in production_ids
        ]
        (tmp_path / "catalog-production.json").write_text(
            json.dumps(production_root, indent=2)
        )
        yield tmp_path, root_url


@pytest.fixture(scope="session")
def dynamical_catalog_fixture(
    served_catalog: tuple[pathlib.Path, str],
) -> object:
    """dynamical_catalog module redirected at the locally-served STAC catalog."""
    dynamical_catalog = pytest.importorskip("dynamical_catalog")
    from dynamical_catalog import _stac  # noqa: PLC0415

    _, root_url = served_catalog
    _stac.STAC_CATALOG_URL = f"{root_url}/catalog.json"
    _stac.clear_cache()
    return dynamical_catalog
