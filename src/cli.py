from __future__ import annotations

import pathlib
import tempfile

from generate import generate
from upload import upload


def main(argv: list[str]) -> int:
    match argv:
        case ["generate", "--output", out]:
            generate(pathlib.Path(out))
        case ["upload", stac_dir]:
            upload(pathlib.Path(stac_dir))
        case ["generate-and-upload"]:
            with tempfile.TemporaryDirectory() as tmp:
                generate(pathlib.Path(tmp))
                upload(pathlib.Path(tmp))
        case _:
            print(  # noqa: T201
                "usage: generate --output DIR | upload DIR | generate-and-upload"
            )
            return 1
    return 0
