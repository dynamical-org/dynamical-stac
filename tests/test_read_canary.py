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
from collections.abc import Callable, Iterator
from typing import Any

import pytest

_SCRIPT = pathlib.Path(__file__).parent.parent / "scripts" / "read_canary.py"

_CATALOG = [f"collection-{i}" for i in range(8)]

_LOGGER = "read_canary"


class _Recorder:
    """Records log lines and every call to the sentry_sdk stubs, in order."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def checkins(self) -> list[str]:
        return [kw["status"] for name, kw in self.calls if name == "capture_checkin"]

    def flushes(self) -> list[dict[str, Any]]:
        return [kw for name, kw in self.calls if name == "flush"]

    def exceptions(self) -> list[BaseException]:
        return [kw["error"] for name, kw in self.calls if name == "capture_exception"]

    def messages(self) -> list[str]:
        return [kw["message"] for name, kw in self.calls if name == "log"]

    def index_of_log(self, prefix: str) -> int:
        return next(
            i
            for i, (name, kw) in enumerate(self.calls)
            if name == "log" and kw["message"].startswith(prefix)
        )

    def index_of_checkin(self, status: str) -> int:
        return next(
            i
            for i, (name, kw) in enumerate(self.calls)
            if name == "capture_checkin" and kw["status"] == status
        )


class _LoggingIntegration:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs


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


def _stub_sentry(recorder: _Recorder) -> dict[str, types.ModuleType]:
    sentry_sdk = types.ModuleType("sentry_sdk")
    crons = types.ModuleType("sentry_sdk.crons")
    integrations = types.ModuleType("sentry_sdk.integrations")
    integrations_logging = types.ModuleType("sentry_sdk.integrations.logging")

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
    sentry_sdk.integrations = integrations  # type: ignore[attr-defined]
    crons.capture_checkin = capture_checkin  # type: ignore[attr-defined]
    integrations.logging = integrations_logging  # type: ignore[attr-defined]
    integrations_logging.LoggingIntegration = _LoggingIntegration  # type: ignore[attr-defined]
    return {
        "sentry_sdk": sentry_sdk,
        "sentry_sdk.crons": crons,
        "sentry_sdk.integrations": integrations,
        "sentry_sdk.integrations.logging": integrations_logging,
    }


def _stub_catalog(collection_ids: list[str]) -> dict[str, types.ModuleType]:
    dynamical_catalog = types.ModuleType("dynamical_catalog")
    stac = types.ModuleType("dynamical_catalog._stac")
    stac.load_catalog = lambda: dict.fromkeys(collection_ids)  # type: ignore[attr-defined]
    dynamical_catalog._stac = stac  # type: ignore[attr-defined]
    return {"dynamical_catalog": dynamical_catalog, "dynamical_catalog._stac": stac}


@pytest.fixture
def recorder() -> _Recorder:
    return _Recorder()


@pytest.fixture
def canary_logger() -> Iterator[logging.Logger]:
    """The script's logger with its handlers and level restored afterwards.

    `_logger()` attaches a StreamHandler bound to whatever sys.stdout is at the
    time, so without this a handler bound to a closed pytest capture stream
    would outlive the test that created it.
    """
    log = logging.getLogger(_LOGGER)
    saved_handlers, saved_level = list(log.handlers), log.level
    for handler in saved_handlers:
        log.removeHandler(handler)
    yield log
    for handler in list(log.handlers):
        log.removeHandler(handler)
        handler.close()
    for handler in saved_handlers:
        log.addHandler(handler)
    log.setLevel(saved_level)


@pytest.fixture
def load_canary(
    monkeypatch: pytest.MonkeyPatch, recorder: _Recorder, canary_logger: logging.Logger
) -> Callable[[list[str]], types.ModuleType]:
    """Load the script fresh with stubbed modal/sentry_sdk/dynamical_catalog."""

    class _LogRecorder(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            recorder.calls.append(("log", {"message": record.getMessage()}))

    canary_logger.addHandler(_LogRecorder())

    def _version(name: str) -> str:
        if name == "zarr":
            raise importlib.metadata.PackageNotFoundError(name)
        return f"{name}-v"

    def _load(collection_ids: list[str]) -> types.ModuleType:
        monkeypatch.setattr(importlib.metadata, "version", _version)
        monkeypatch.setitem(sys.modules, "modal", _stub_modal())
        for name, module in (
            _stub_sentry(recorder) | _stub_catalog(collection_ids)
        ).items():
            monkeypatch.setitem(sys.modules, name, module)
        monkeypatch.delenv("SENTRY_DSN", raising=False)

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
) -> None:
    canary = load_canary(_CATALOG)
    checked: list[str] = []

    def fake_check(collection_id: str) -> float:
        checked.append(collection_id)
        return 0.25 if collection_id != "collection-3" else 1.5

    monkeypatch.setattr(canary, "_check_collection", fake_check)

    canary.read_canary()

    assert sorted(checked) == _CATALOG
    assert recorder.checkins() == ["in_progress", "ok"]
    # The terminal check-in must get a real flush budget: the sdk default is 2 s,
    # which a slow Sentry edge exhausts before the envelope leaves the queue.
    assert recorder.flushes() == [{"timeout": canary._FLUSH_TIMEOUT_SECONDS}]
    assert canary._FLUSH_TIMEOUT_SECONDS == 15
    assert recorder.exceptions() == []

    messages = recorder.messages()
    assert messages[0] == (
        "read canary started; dynamical-catalog dynamical-catalog-v, "
        "icechunk icechunk-v, zarr unknown, sentry-sdk sentry-sdk-v"
    )
    assert messages[1] == "in_progress check-in check-in-id submitted"
    assert messages[-1].startswith("read canary ok: 8/8 collections read in ")
    assert (
        "(slowest collection-3 1.5s); submitting ok check-in check-in-id"
        in messages[-1]
    )
    # The summary is evidence for Modal's logs and must be emitted before the
    # terminal check-in, so a lost or hung flush cannot erase it.
    assert recorder.index_of_log("read canary ok:") < recorder.index_of_checkin("ok")


def test_start_line_precedes_sentry_init_and_catalog_import(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
) -> None:
    canary = load_canary(_CATALOG)

    def broken_init(**_: object) -> None:
        raise RuntimeError("sentry init exploded")

    monkeypatch_init = sys.modules["sentry_sdk"]
    monkeypatch_init.init = broken_init  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError, match="sentry init exploded"):
        canary.read_canary()
    assert recorder.messages() == [recorder.messages()[0]]
    assert recorder.messages()[0].startswith("read canary started;")

    # Same guarantee when the reader package itself cannot be imported.
    recorder.calls.clear()
    del sys.modules["dynamical_catalog._stac"].load_catalog  # type: ignore[attr-defined]
    with pytest.raises(ImportError):
        canary.read_canary()
    assert [m[:20] for m in recorder.messages()] == ["read canary started;"]


def test_sentry_logging_integration_does_not_double_report_failures(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The failure line is logged at ERROR; only capture_exception may make an event."""
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_check_collection", lambda _cid: 0.1)

    canary.read_canary()

    ((_, init_kwargs),) = [c for c in recorder.calls if c[0] == "init"]
    assert init_kwargs["enable_logs"] is True
    (integration,) = init_kwargs["integrations"]
    assert isinstance(integration, _LoggingIntegration)
    assert integration.kwargs == {"event_level": None}


def test_log_lines_reach_stdout_without_root_logging_config(
    load_canary: Callable[[list[str]], types.ModuleType],
    canary_logger: logging.Logger,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Modal only sees what hits stdout; a record-level check would pass without any handler."""
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_check_collection", lambda _cid: 0.1)
    recording_handlers = list(canary_logger.handlers)

    canary.read_canary()
    canary.read_canary()  # warm container: second entry must not add a handler

    out = capsys.readouterr().out
    assert out.count("read canary started;") == 2
    assert out.count("read canary ok: 8/8 collections") == 2
    assert re.match(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ INFO read canary started;", out)
    stream_handlers = [h for h in canary_logger.handlers if h not in recording_handlers]
    assert [h.name for h in stream_handlers] == [canary._STDOUT_HANDLER]


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
) -> None:
    canary = load_canary(_CATALOG)
    checked: list[str] = []

    def fake_check(collection_id: str) -> float:
        checked.append(collection_id)
        if collection_id == "collection-5":
            raise ValueError("collection-5.var is inf")
        return 0.1

    monkeypatch.setattr(canary, "_check_collection", fake_check)

    with pytest.raises(RuntimeError, match=r"failed for 1/8 collections"):
        canary.read_canary()

    assert sorted(checked) == _CATALOG  # one failure does not stop the sweep
    assert recorder.checkins() == ["in_progress", "error"]
    assert recorder.flushes() == [{"timeout": 15}]
    (captured,) = recorder.exceptions()
    assert "collection-5: ValueError('collection-5.var is inf')" in str(captured)
    failure = recorder.messages()[-1]
    assert failure.startswith("read canary failed after ")
    assert "; submitting error check-in check-in-id: " in failure
    assert "collection-5" in failure
    assert recorder.index_of_log("read canary failed") < recorder.index_of_checkin(
        "error"
    )


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


def test_catalog_at_exactly_the_floor_is_read(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    floor_catalog = _CATALOG[:6]
    canary = load_canary(floor_catalog)
    assert len(floor_catalog) == canary.MIN_COLLECTIONS
    checked: list[str] = []
    monkeypatch.setattr(
        canary, "_check_collection", lambda cid: checked.append(cid) or 0.1
    )

    canary.read_canary()

    assert sorted(checked) == floor_catalog
    assert recorder.checkins() == ["in_progress", "ok"]
