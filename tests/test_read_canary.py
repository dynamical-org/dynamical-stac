"""Unit tests for scripts/read_canary.py, the Modal hot-storage read canary.

The script imports `modal` at module top and `sentry_sdk` / `dynamical_catalog`
inside the function; none of them are project dependencies (modal is pulled in
ephemerally by the deploy workflow). The tests install small recording stubs
for all three into `sys.modules` and load the script from its path, so they run
under the normal `uv sync --group integration` environment with no network.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import logging
import pathlib
import re
import sys
import types
from collections.abc import Callable
from typing import Any

import pytest

_SCRIPT = pathlib.Path(__file__).parent.parent / "scripts" / "read_canary.py"

_CATALOG = [f"collection-{i}" for i in range(8)]


class _Recorder:
    """Records every call made to the sentry_sdk stubs, in order."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def checkins(self) -> list[str]:
        return [kw["status"] for name, kw in self.calls if name == "capture_checkin"]

    def flushes(self) -> list[dict[str, Any]]:
        return [kw for name, kw in self.calls if name == "flush"]

    def exceptions(self) -> list[BaseException]:
        return [kw["error"] for name, kw in self.calls if name == "capture_exception"]


def _stub_modal() -> types.ModuleType:
    modal = types.ModuleType("modal")

    class _Image:
        @staticmethod
        def debian_slim(**_: object) -> _Image:
            return _Image()

        def pip_install(self, *_: str) -> _Image:
            return self

    class _App:
        def __init__(self, _name: str) -> None:
            pass

        @staticmethod
        def function(**_: object) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            return lambda fn: fn

    class _Secret:
        @staticmethod
        def from_name(_name: str) -> object:
            return object()

    modal.Image = _Image  # type: ignore[attr-defined]
    modal.App = _App  # type: ignore[attr-defined]
    modal.Secret = _Secret  # type: ignore[attr-defined]
    modal.Period = lambda **_: object()  # type: ignore[attr-defined]
    return modal


def _stub_sentry(recorder: _Recorder) -> tuple[types.ModuleType, types.ModuleType]:
    sentry_sdk = types.ModuleType("sentry_sdk")
    crons = types.ModuleType("sentry_sdk.crons")

    def init(**kwargs: object) -> None:
        recorder.calls.append(("init", kwargs))

    def capture_exception(error: BaseException) -> None:
        recorder.calls.append(("capture_exception", {"error": error}))

    def flush(**kwargs: object) -> None:
        recorder.calls.append(("flush", kwargs))

    def capture_checkin(**kwargs: object) -> str:
        recorder.calls.append(("capture_checkin", kwargs))
        return "check-in-id"

    sentry_sdk.init = init  # type: ignore[attr-defined]
    sentry_sdk.capture_exception = capture_exception  # type: ignore[attr-defined]
    sentry_sdk.flush = flush  # type: ignore[attr-defined]
    sentry_sdk.crons = crons  # type: ignore[attr-defined]
    crons.capture_checkin = capture_checkin  # type: ignore[attr-defined]
    return sentry_sdk, crons


def _stub_catalog(
    collection_ids: list[str],
) -> tuple[types.ModuleType, types.ModuleType]:
    dynamical_catalog = types.ModuleType("dynamical_catalog")
    stac = types.ModuleType("dynamical_catalog._stac")
    stac.load_catalog = lambda: dict.fromkeys(collection_ids)  # type: ignore[attr-defined]
    dynamical_catalog._stac = stac  # type: ignore[attr-defined]
    return dynamical_catalog, stac


@pytest.fixture
def recorder() -> _Recorder:
    return _Recorder()


@pytest.fixture
def load_canary(
    monkeypatch: pytest.MonkeyPatch, recorder: _Recorder, request: pytest.FixtureRequest
) -> Callable[[list[str]], types.ModuleType]:
    """Load the script fresh with stubbed modal/sentry_sdk/dynamical_catalog."""

    request_cleanup = request.addfinalizer

    def _load(collection_ids: list[str]) -> types.ModuleType:
        def _version(name: str) -> str:
            if name == "zarr":
                raise importlib.metadata.PackageNotFoundError(name)
            return f"{name}-v"

        monkeypatch.setattr(importlib.metadata, "version", _version)
        monkeypatch.setitem(sys.modules, "modal", _stub_modal())
        sentry_sdk, crons = _stub_sentry(recorder)
        monkeypatch.setitem(sys.modules, "sentry_sdk", sentry_sdk)
        monkeypatch.setitem(sys.modules, "sentry_sdk.crons", crons)
        catalog, stac = _stub_catalog(collection_ids)
        monkeypatch.setitem(sys.modules, "dynamical_catalog", catalog)
        monkeypatch.setitem(sys.modules, "dynamical_catalog._stac", stac)
        monkeypatch.delenv("SENTRY_DSN", raising=False)

        class _LogRecorder(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                recorder.calls.append(("log", {"message": record.getMessage()}))

        log = logging.getLogger("read_canary")
        log_recorder = _LogRecorder()
        log.addHandler(log_recorder)
        request_cleanup(lambda: log.removeHandler(log_recorder))

        spec = importlib.util.spec_from_file_location("read_canary_under_test", _SCRIPT)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return _load


def test_success_checks_in_ok_and_flushes_with_budget(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    canary = load_canary(_CATALOG)
    checked: list[str] = []

    def fake_check(collection_id: str) -> float:
        checked.append(collection_id)
        return 0.25 if collection_id != "collection-3" else 1.5

    monkeypatch.setattr(canary, "_check_collection", fake_check)

    with caplog.at_level(logging.INFO, logger="read_canary"):
        canary.read_canary()

    assert sorted(checked) == _CATALOG
    assert recorder.checkins() == ["in_progress", "ok"]
    # The terminal check-in must get a real flush budget: the sdk default is 2 s,
    # which a slow Sentry edge exhausts before the envelope leaves the queue.
    assert recorder.flushes() == [{"timeout": canary._FLUSH_TIMEOUT_SECONDS}]
    assert canary._FLUSH_TIMEOUT_SECONDS == 15
    assert recorder.exceptions() == []

    messages = [record.getMessage() for record in caplog.records]
    assert messages[0] == (
        "read canary started; dynamical-catalog dynamical-catalog-v, "
        "icechunk icechunk-v, zarr unknown, sentry-sdk sentry-sdk-v"
    )
    assert messages[1] == "in_progress check-in check-in-id sent"
    assert messages[-1].startswith("read canary ok: 8/8 collections read in ")
    assert (
        "(slowest collection-3 1.5s); sending ok check-in check-in-id" in messages[-1]
    )
    # The summary is evidence for Modal's logs and must be emitted before the
    # terminal check-in, so a lost or hung flush cannot erase it.
    summary_index = next(i for i, (n, _) in enumerate(recorder.calls) if n == "log")
    terminal_index = next(
        i
        for i, (n, kw) in enumerate(recorder.calls)
        if n == "capture_checkin" and kw["status"] == "ok"
    )
    assert summary_index < terminal_index


def test_log_lines_reach_stdout_without_root_logging_config(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Modal only sees what hits stdout; caplog would pass without any handler."""
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_check_collection", lambda _cid: 0.1)
    log = logging.getLogger("read_canary")
    for handler in list(log.handlers):
        log.removeHandler(handler)

    canary.read_canary()
    canary.read_canary()  # warm container: second entry must not add a handler

    out = capsys.readouterr().out
    assert out.count("read canary started;") == 2
    assert re.match(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ INFO read canary started;", out)
    assert out.count("read canary ok: 8/8 collections") == 2
    assert len(log.handlers) == 1


def test_terminal_checkin_reuses_in_progress_id_and_config(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_check_collection", lambda _cid: 0.1)

    canary.read_canary()

    checkins = [kw for name, kw in recorder.calls if name == "capture_checkin"]
    assert checkins[0]["monitor_slug"] == "read-canary"
    assert checkins[1]["check_in_id"] == "check-in-id"
    assert checkins[0]["monitor_config"] == checkins[1]["monitor_config"]
    config = checkins[0]["monitor_config"]
    assert config["schedule"] == {"type": "interval", "value": 10, "unit": "minute"}
    assert config["max_runtime"] == canary._TIMEOUT_SECONDS // 60 + 2


def test_read_failure_captures_error_checkin_and_raises(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    canary = load_canary(_CATALOG)

    def fake_check(collection_id: str) -> float:
        if collection_id == "collection-5":
            raise ValueError("collection-5.var is inf")
        return 0.1

    monkeypatch.setattr(canary, "_check_collection", fake_check)

    with (
        caplog.at_level(logging.INFO, logger="read_canary"),
        pytest.raises(RuntimeError, match=r"failed for 1/8 collections"),
    ):
        canary.read_canary()

    assert recorder.checkins() == ["in_progress", "error"]
    assert recorder.flushes() == [{"timeout": 15}]
    (captured,) = recorder.exceptions()
    assert "collection-5: ValueError('collection-5.var is inf')" in str(captured)
    failure_lines = [
        r.getMessage() for r in caplog.records if r.levelno == logging.ERROR
    ]
    assert len(failure_lines) == 1
    assert failure_lines[0].startswith("read canary failed after ")
    assert "; sending error check-in check-in-id: " in failure_lines[0]
    assert "collection-5" in failure_lines[0]


def test_catalog_load_failure_closes_checkin_as_error(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)

    def broken_load_catalog() -> dict[str, None]:
        raise ConnectionError("catalog.json unreachable")

    monkeypatch.setattr(
        sys.modules["dynamical_catalog._stac"], "load_catalog", broken_load_catalog
    )
    monkeypatch.setattr(
        canary, "_check_collection", lambda _cid: pytest.fail("must not read")
    )

    with pytest.raises(ConnectionError, match=r"catalog\.json unreachable"):
        canary.read_canary()

    # Previously this raised straight through the in_progress check-in and
    # Sentry only noticed once max_runtime elapsed.
    assert recorder.checkins() == ["in_progress", "error"]
    assert recorder.flushes() == [{"timeout": 15}]
    (captured,) = recorder.exceptions()
    assert isinstance(captured, ConnectionError)


def test_catalog_at_exactly_the_floor_is_read(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    floor_catalog = _CATALOG[: canary.MIN_COLLECTIONS]
    canary = load_canary(floor_catalog)
    checked: list[str] = []
    monkeypatch.setattr(
        canary, "_check_collection", lambda cid: checked.append(cid) or 0.1
    )

    canary.read_canary()

    assert sorted(checked) == floor_catalog
    assert recorder.checkins()[-1] == "ok"


def test_short_catalog_fails_before_reading(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    short_catalog = _CATALOG[:3]
    canary = load_canary(short_catalog)
    assert len(short_catalog) < canary.MIN_COLLECTIONS
    checked: list[str] = []
    monkeypatch.setattr(
        canary, "_check_collection", lambda cid: checked.append(cid) or 0.1
    )

    with pytest.raises(RuntimeError, match=r"returned 3 collections, expected >= "):
        canary.read_canary()

    assert checked == []
    assert recorder.checkins() == ["in_progress", "error"]
    assert recorder.flushes() == [{"timeout": 15}]
    assert len(recorder.exceptions()) == 1
