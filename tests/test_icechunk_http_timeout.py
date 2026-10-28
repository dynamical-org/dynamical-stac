from __future__ import annotations

from unittest.mock import patch

import icechunk
import pytest

from catalog import CATALOG_ITEMS
from generate import _storage


@pytest.mark.parametrize(
    ("opts", "expected"),
    [
        (None, {"timeout": "90s"}),
        ({"connect_timeout": "5s"}, {"timeout": "90s", "connect_timeout": "5s"}),
        ({"timeout": "2s"}, {"timeout": "2s"}),
    ],
)
def test_http_storage_preserves_options_and_headers(
    opts: dict[str, str] | None, expected: dict[str, str]
) -> None:
    with patch.object(
        icechunk.storage, "http_storage", wraps=icechunk.storage.http_storage
    ) as factory:
        storage = icechunk.http_storage(
            "https://example.invalid/repo", opts=opts, headers={"x-test": "fixture"}
        )

    assert isinstance(storage, icechunk.Storage)
    factory.assert_called_once_with(
        "https://example.invalid/repo",
        opts=expected,
        headers={"x-test": "fixture"},
    )


def test_generator_http_storage_uses_fixture_timeout() -> None:
    item = next(item for item in CATALOG_ITEMS if item.icechunk_scheme == "https")
    with patch.object(
        icechunk.storage, "http_storage", wraps=icechunk.storage.http_storage
    ) as factory:
        _storage(item)

    assert factory.call_args.kwargs["opts"]["timeout"] == "90s"


def test_catalog_open_uses_fixture_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    catalog = pytest.importorskip("dynamical_catalog")
    monkeypatch.setattr(
        catalog,
        "_resolve",
        lambda _: {
            "icechunk": {"type": "http", "base_url": "https://example.invalid/repo"}
        },
    )
    with (
        patch.object(
            icechunk.storage, "http_storage", wraps=icechunk.storage.http_storage
        ) as factory,
        patch.object(icechunk.Repository, "open"),
        patch("xarray.open_zarr") as open_zarr,
    ):
        assert catalog.open("fixture") is open_zarr.return_value

    assert factory.call_args.kwargs["opts"]["timeout"] == "90s"
