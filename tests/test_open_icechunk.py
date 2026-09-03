"""Unit tests for `generate._open_icechunk`'s per-backend dispatch.

The store is never really opened: `icechunk.s3_storage`/`gcs_storage`/
`azure_storage`, `icechunk.Repository.open`, `xr.open_zarr` and
`zarr.open_group` are all patched, so these assert only which icechunk
constructor each href scheme reaches and with what arguments.
"""

from __future__ import annotations

from typing import Any

import icechunk
import pytest

import generate
from catalog import CatalogItem, DatasetExample, DatasetNotebook

_S3_ID = "noaa-gfs-analysis"
_GCS_ID = "test-gcs-virtual"
_AZ_ID = "test-azure-virtual"
_AZ_ACCOUNT = "dynamicalicechunktest"
_AZ_CONTAINER = "dynamical-icechunk-azure-demo"

_ITEM_KWARGS: dict[str, Any] = {
    "description_summary": "test summary",
    "reformatter_url": "https://example.com/reformatter.py",
    "examples": (
        DatasetExample(
            title="Example",
            code='import dynamical_catalog\n\nds = dynamical_catalog.open("x", chunks=None)',
        ),
    ),
}


def _s3_item(virtual_prefixes: tuple[str, ...] = ()) -> CatalogItem:
    return CatalogItem(
        id=_S3_ID,
        icechunk_href=f"s3://dynamical-noaa-gfs/{_S3_ID}/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        virtual_chunk_container_prefixes=virtual_prefixes,
        model_id="noaa-gfs",
        notebooks=(DatasetNotebook(slug=_S3_ID, title="Quickstart"),),
        **_ITEM_KWARGS,
    )


def _gcs_item(virtual_prefixes: tuple[str, ...] = ()) -> CatalogItem:
    return CatalogItem(
        id=_GCS_ID,
        icechunk_href=f"gs://dynamical-icechunk-gcs-demo/{_GCS_ID}/v0.1.0.icechunk/",
        virtual_chunk_container_prefixes=virtual_prefixes,
        model_id="dynamical-test",
        test=True,
        **_ITEM_KWARGS,
    )


def _azure_item(virtual_prefixes: tuple[str, ...] = ()) -> CatalogItem:
    return CatalogItem(
        id=_AZ_ID,
        icechunk_href=f"az://{_AZ_CONTAINER}/{_AZ_ID}/v0.1.0.icechunk/",
        icechunk_account=_AZ_ACCOUNT,
        virtual_chunk_container_prefixes=virtual_prefixes,
        model_id="dynamical-test",
        test=True,
        **_ITEM_KWARGS,
    )


@pytest.fixture
def storage_calls(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Record which storage constructor `_open_icechunk` reaches, and stub I/O."""
    calls: dict[str, Any] = {}

    class _Session:
        store = "store"

    class _Repo:
        def readonly_session(self, branch: str) -> _Session:
            calls["branch"] = branch
            return _Session()

    def fake_s3_storage(**kwargs: object) -> str:
        calls["s3_storage"] = kwargs
        return "s3-storage"

    def fake_gcs_storage(**kwargs: object) -> str:
        calls["gcs_storage"] = kwargs
        return "gcs-storage"

    def fake_azure_storage(**kwargs: object) -> str:
        calls["azure_storage"] = kwargs
        return "azure-storage"

    def fake_open(storage: object, **kwargs: object) -> _Repo:
        calls["repository_open"] = (storage, kwargs)
        return _Repo()

    monkeypatch.setattr(generate.icechunk, "s3_storage", fake_s3_storage)
    monkeypatch.setattr(generate.icechunk, "gcs_storage", fake_gcs_storage)
    monkeypatch.setattr(generate.icechunk, "azure_storage", fake_azure_storage)
    monkeypatch.setattr(generate.icechunk.Repository, "open", staticmethod(fake_open))
    monkeypatch.setattr(generate.xr, "open_zarr", lambda *a, **k: "dataset")
    monkeypatch.setattr(
        generate.zarr, "open_group", lambda *a, **k: type("G", (), {"groups": list})()
    )
    return calls


def test_open_icechunk_uses_s3_storage_for_s3_href(
    storage_calls: dict[str, Any],
) -> None:
    generate._open_icechunk(_s3_item())
    assert "gcs_storage" not in storage_calls
    assert storage_calls["s3_storage"] == {
        "bucket": "dynamical-noaa-gfs",
        "prefix": f"{_S3_ID}/v0.1.0.icechunk/",
        "region": "us-west-2",
        "anonymous": True,
    }
    assert storage_calls["repository_open"][0] == "s3-storage"


def test_open_icechunk_uses_gcs_storage_for_gs_href(
    storage_calls: dict[str, Any],
) -> None:
    generate._open_icechunk(_gcs_item())
    assert "s3_storage" not in storage_calls
    assert storage_calls["gcs_storage"] == {
        "bucket": "dynamical-icechunk-gcs-demo",
        "prefix": f"{_GCS_ID}/v0.1.0.icechunk/",
        "anonymous": True,
    }
    assert storage_calls["repository_open"][0] == "gcs-storage"


def test_open_icechunk_uses_azure_storage_for_az_href(
    storage_calls: dict[str, Any],
) -> None:
    generate._open_icechunk(_azure_item())
    assert "s3_storage" not in storage_calls
    assert "gcs_storage" not in storage_calls
    # Azure takes the href's netloc as `container` plus a separate `account`.
    assert storage_calls["azure_storage"] == {
        "account": _AZ_ACCOUNT,
        "container": _AZ_CONTAINER,
        "prefix": f"{_AZ_ID}/v0.1.0.icechunk/",
        "anonymous": True,
    }
    assert storage_calls["repository_open"][0] == "azure-storage"


def test_open_icechunk_omits_authorization_without_virtual_containers(
    storage_calls: dict[str, Any],
) -> None:
    generate._open_icechunk(_s3_item())
    _, kwargs = storage_calls["repository_open"]
    assert kwargs["authorize_virtual_chunk_access"] is None


def test_container_credentials_follow_the_prefix_scheme() -> None:
    s3_credentials = generate._container_credentials("s3://noaa-hrrr-bdp-pds/")
    gcs_credentials = generate._container_credentials("gs://some-bucket/source/")
    azure_credentials = generate._container_credentials("az://some-container/source/")
    assert isinstance(s3_credentials, icechunk.S3Credentials.Anonymous)
    assert isinstance(gcs_credentials, icechunk.GcsCredentials.Anonymous)
    assert isinstance(azure_credentials, icechunk.AzureCredentials.Anonymous)


def test_container_credentials_reject_unsupported_scheme() -> None:
    with pytest.raises(ValueError, match="unsupported object-store URL"):
        generate._container_credentials("https://example.com/source/")
