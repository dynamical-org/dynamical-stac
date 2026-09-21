from __future__ import annotations

import pathlib

from environments import STAC_ENVIRONMENTS
from generate import generate, generate_environments
from upload import upload

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def main(argv: list[str]) -> int:
    match argv:
        case ["generate"]:
            generate_environments(REPO_ROOT)
        case ["generate", "--output", out]:
            generate(pathlib.Path(out))
        case ["generate", "--output", out, "--environment", name] | [
            "generate",
            "--environment",
            name,
            "--output",
            out,
        ] if name in {environment.name for environment in STAC_ENVIRONMENTS}:
            generate(pathlib.Path(out), environment=name)
        case ["upload", stac_dir]:
            upload(pathlib.Path(stac_dir))
        case _:
            print(  # noqa: T201
                "usage: generate [--output DIR [--environment production|staging|test]] | upload DIR"
            )
            return 1
    return 0
