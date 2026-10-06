from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

_UPLOAD_SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "src" / "upload.py"
_BOOTSTRAP = """
import atexit
import json
import runpy
import sys
import types

calls = []

def upload_file(*args, **kwargs):
    calls.append(["upload_file", args, kwargs])

def client(*args, **kwargs):
    calls.append(["client", args, kwargs])
    return types.SimpleNamespace(upload_file=upload_file)

boto3 = types.ModuleType("boto3")
boto3.client = client
sys.modules["boto3"] = boto3
atexit.register(lambda: print("MOCK_CALLS=" + json.dumps(calls)))
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""


def _run_upload(args: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    # Isolated mode and no site packages leave only stdlib and the boto3 mock.
    return subprocess.run(  # noqa: S603
        [sys.executable, "-I", "-S", "-c", _BOOTSTRAP, str(_UPLOAD_SCRIPT), *args],
        cwd=cwd,
        env={
            "R2_BUCKET": "isolated-test",
            "R2_ENDPOINT_URL": "https://fake.r2.test",
            "R2_ACCESS_KEY_ID": "fake-id",
            "R2_SECRET_ACCESS_KEY": "fake-secret",
        },
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_upload_entrypoint_runs_without_generator_dependencies(
    tmp_path: pathlib.Path,
) -> None:
    tree = tmp_path / "catalog with spaces"
    collection = tree / "dataset" / "collection.json"
    collection.parent.mkdir(parents=True)
    collection.write_text("{}")
    root = tree / "catalog.json"
    root.write_text("{}")
    (tree / "readme.txt").write_text("not json")

    result = _run_upload([str(tree)], tmp_path)

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout.splitlines()[:2] == [
        "uploaded dataset/collection.json",
        "uploaded catalog.json",
    ]
    calls = json.loads(result.stdout.split("MOCK_CALLS=", 1)[1])
    assert calls == [
        [
            "client",
            ["s3"],
            {
                "endpoint_url": "https://fake.r2.test",
                "aws_access_key_id": "fake-id",
                "aws_secret_access_key": "fake-secret",
            },
        ],
        [
            "upload_file",
            [str(collection), "isolated-test", "dataset/collection.json"],
            {"ExtraArgs": {"ContentType": "application/json"}},
        ],
        [
            "upload_file",
            [str(root), "isolated-test", "catalog.json"],
            {"ExtraArgs": {"ContentType": "application/json"}},
        ],
    ]


@pytest.mark.parametrize("args", [[], ["tree", "extra"], ["upload", "tree"]])
def test_upload_entrypoint_rejects_wrong_argument_count(
    args: list[str], tmp_path: pathlib.Path
) -> None:
    result = _run_upload(args, tmp_path)

    assert result.returncode == 1, result.stderr
    assert result.stderr == ""
    assert result.stdout == "usage: upload.py DIR\nMOCK_CALLS=[]\n"
