from __future__ import annotations

import http.server
import pathlib
import socketserver
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

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


@pytest.fixture
def served_catalog(tmp_path: pathlib.Path) -> Iterator[tuple[pathlib.Path, str]]:
    """Generate the catalog into tmp_path and serve it over HTTP.

    Yields (catalog_dir, root_url).
    """
    with _serve(tmp_path) as port:
        root_url = f"http://127.0.0.1:{port}"
        generate(tmp_path, root_href=root_url)
        yield tmp_path, root_url
