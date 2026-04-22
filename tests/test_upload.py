from __future__ import annotations

import pathlib
from typing import Any
from unittest.mock import MagicMock

import pytest

import upload as upload_module
from upload import upload

_FAKE_ENDPOINT = "https://fake.r2.test"
_FAKE_KEY_ID = "fake-id"
_FAKE_SECRET = "fake-secret"  # noqa: S105


@pytest.fixture
def stac_tree(tmp_path: pathlib.Path) -> pathlib.Path:
    (tmp_path / "catalog.json").write_text("{}")
    (tmp_path / "noaa-gfs-analysis").mkdir()
    (tmp_path / "noaa-gfs-analysis" / "collection.json").write_text("{}")
    (tmp_path / "readme.txt").write_text("not json")
    return tmp_path


def test_upload_only_sends_json_files(
    stac_tree: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("R2_ENDPOINT_URL", _FAKE_ENDPOINT)
    monkeypatch.setenv("R2_ACCESS_KEY_ID", _FAKE_KEY_ID)
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", _FAKE_SECRET)
    client = MagicMock()
    monkeypatch.setattr(upload_module.boto3, "client", lambda *a, **kw: client)

    upload(stac_tree)

    uploaded_keys = [call.args[2] for call in client.upload_file.call_args_list]
    assert set(uploaded_keys) == {
        "catalog.json",
        "noaa-gfs-analysis/collection.json",
    }


def test_upload_sets_bucket_and_content_type(
    stac_tree: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("R2_ENDPOINT_URL", _FAKE_ENDPOINT)
    monkeypatch.setenv("R2_ACCESS_KEY_ID", _FAKE_KEY_ID)
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", _FAKE_SECRET)
    client = MagicMock()
    monkeypatch.setattr(upload_module.boto3, "client", lambda *a, **kw: client)

    upload(stac_tree)

    for call in client.upload_file.call_args_list:
        _local, bucket, _key = call.args
        extra: dict[str, Any] = call.kwargs["ExtraArgs"]
        assert bucket == upload_module._BUCKET
        assert extra == {"ContentType": "application/json"}


def test_upload_passes_r2_creds_to_boto(
    stac_tree: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("R2_ENDPOINT_URL", _FAKE_ENDPOINT)
    monkeypatch.setenv("R2_ACCESS_KEY_ID", _FAKE_KEY_ID)
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", _FAKE_SECRET)
    seen_kwargs: dict[str, Any] = {}

    def fake_client(service: str, **kwargs: Any) -> MagicMock:  # noqa: ANN401
        seen_kwargs["service"] = service
        seen_kwargs.update(kwargs)
        return MagicMock()

    monkeypatch.setattr(upload_module.boto3, "client", fake_client)

    upload(stac_tree)

    assert seen_kwargs["service"] == "s3"
    assert seen_kwargs["endpoint_url"] == _FAKE_ENDPOINT
    assert seen_kwargs["aws_access_key_id"] == _FAKE_KEY_ID
    assert seen_kwargs["aws_secret_access_key"] == _FAKE_SECRET
