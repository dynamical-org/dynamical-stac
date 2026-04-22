from __future__ import annotations

import os
import pathlib

import boto3

_BUCKET = "stac"


def upload(stac_dir: pathlib.Path) -> None:
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
    )
    for file in sorted(stac_dir.rglob("*.json")):
        key = str(file.relative_to(stac_dir))
        s3.upload_file(
            str(file),
            _BUCKET,
            key,
            ExtraArgs={"ContentType": "application/json"},
        )
        print(f"uploaded {key}")  # noqa: T201
