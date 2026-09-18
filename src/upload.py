from __future__ import annotations

import os
import pathlib

import boto3

_BUCKET = os.environ.get("R2_BUCKET", "stac")


def upload_order(stac_dir: pathlib.Path) -> list[pathlib.Path]:
    """Every STAC file, collections before the root catalogs that link to them.

    Released dynamical-catalog clients fetch every child of the root before
    opening anything, so a root published ahead of a new collection fails every
    dataset for them until the upload finishes.
    """
    files = sorted(stac_dir.rglob("*.json"))
    roots = [file for file in files if file.parent == stac_dir]
    return [file for file in files if file.parent != stac_dir] + roots


def upload(stac_dir: pathlib.Path) -> None:
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
    )
    for file in upload_order(stac_dir):
        key = str(file.relative_to(stac_dir))
        s3.upload_file(
            str(file),
            _BUCKET,
            key,
            ExtraArgs={"ContentType": "application/json"},
        )
        print(f"uploaded {key}")  # noqa: T201
