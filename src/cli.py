from __future__ import annotations

import pathlib

from generate import generate
from upload import upload

DEFAULT_OUTPUT_DIR = pathlib.Path("stac")


def main(argv: list[str]) -> int:
    match argv:
        case ["generate"]:
            generate(DEFAULT_OUTPUT_DIR)
        case ["generate", "--output", out]:
            generate(pathlib.Path(out))
        case ["upload", stac_dir]:
            upload(pathlib.Path(stac_dir))
        case _:
            print(  # noqa: T201
                "usage: generate [--output DIR] | upload DIR"
            )
            return 1
    return 0
