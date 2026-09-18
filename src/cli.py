from __future__ import annotations

import pathlib

from generate import generate, generate_tiers
from upload import upload

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def main(argv: list[str]) -> int:
    match argv:
        case ["generate"]:
            generate_tiers(REPO_ROOT)
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
