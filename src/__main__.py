from __future__ import annotations

import pathlib
import sys
import tempfile

from generate import generate
from upload import upload

match sys.argv[1:]:
    case ["generate", "--output", out]:
        generate(pathlib.Path(out))
    case ["upload", stac_dir]:
        upload(pathlib.Path(stac_dir))
    case ["generate-and-upload"]:
        with tempfile.TemporaryDirectory() as tmp:
            generate(pathlib.Path(tmp))
            upload(pathlib.Path(tmp))
    case _:
        print("usage: generate --output DIR | upload DIR | generate-and-upload")
        sys.exit(1)
