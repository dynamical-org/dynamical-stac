from __future__ import annotations

import os
import pathlib
import sys

import boto3

_BUCKET = os.environ.get("R2_BUCKET", "stac")


_CONTENT_TYPES = {
    ".json": "application/json",
    ".md": "text/markdown; charset=utf-8",
}


def upload_order(stac_dir: pathlib.Path) -> list[pathlib.Path]:
    """Every published file: the Markdown sidecars, then collections, then roots.

    Released dynamical-catalog clients fetch every child of the root before
    opening anything, so a root published ahead of a new collection fails every
    dataset for them until the upload finishes. The sidecars go first so a
    document never links to a README.md or AGENTS.md that is not there yet.
    """
    sidecars = sorted(stac_dir.rglob("*.md"))
    files = sorted(stac_dir.rglob("*.json"))
    roots = [file for file in files if file.parent == stac_dir]
    return sidecars + [file for file in files if file.parent != stac_dir] + roots


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
            ExtraArgs={"ContentType": _CONTENT_TYPES[file.suffix]},
        )
        print(f"uploaded {key}")  # noqa: T201


def main(argv: list[str]) -> int:
    match argv:
        case [stac_dir]:
            upload(pathlib.Path(stac_dir))
            return 0
        case _:
            print("usage: upload.py DIR")  # noqa: T201
            return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
