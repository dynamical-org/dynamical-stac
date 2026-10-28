"""Unit tests for scripts/read_canary.py, the Modal hot-storage read canary.

The script imports `modal` at module top and `sentry_sdk` / `dynamical_catalog`
inside the function; none of them are project dependencies (modal is pulled in
ephemerally by the deploy workflow). The tests install small recording stubs
for all three into `sys.modules` and load the script from its path, so they run
under the normal `uv sync --group integration` environment with no network.
"""

from __future__ import annotations

import http.server
import importlib.metadata
import importlib.util
import logging
import math
import pathlib
import re
import sys
import threading
import time
import types
import uuid
from collections.abc import Callable, Iterator
from typing import Any

import numpy as np
import pytest
import xarray as xr

_SCRIPT = pathlib.Path(__file__).parent.parent / "scripts" / "read_canary.py"

_CATALOG = [f"collection-{i}" for i in range(8)]

_LOGGER = "read_canary"

# The id the run gives its opening check-in, uuid4().hex.
_RUN = "5f0c4a2e8b8d4c4f9d3c1f6a7b2e9d10"
# Shared with dynamical.org-data's status publisher, which pairs on it.
_COVERAGE_NAMESPACE = uuid.UUID("d014545d-f123-4e15-9893-6bfff7bbc831")
_MARKER = uuid.uuid5(_COVERAGE_NAMESPACE, _RUN).hex
# Shared with the status publisher, which fetches a failed run's event by it.
_REPORT_NAMESPACE = uuid.UUID("f19ee126-79b9-4217-95db-f305e99ce3a6")
_REPORT_EVENT = uuid.uuid5(_REPORT_NAMESPACE, _RUN).hex


class _Recorder:
    """Records log lines and every call to the sentry_sdk stubs, in order."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def checkins(self, slug: str = "read-canary") -> list[str]:
        return [
            kw["status"]
            for name, kw in self.calls
            if name == "capture_checkin" and kw["monitor_slug"] == slug
        ]

    def coverage(self) -> list[str]:
        return self.checkins("read-canary-coverage")

    def warnings(self) -> list[dict[str, Any]]:
        return [kw for name, kw in self.calls if name == "capture_message"]

    def spawns(self) -> list[dict[str, Any]]:
        return [kw for name, kw in self.calls if name == "spawn"]

    def flushes(self) -> list[dict[str, Any]]:
        return [kw for name, kw in self.calls if name == "flush"]

    def events(self) -> list[dict[str, Any]]:
        return [kw["event"] for name, kw in self.calls if name == "capture_event"]

    def exceptions(self) -> list[BaseException]:
        """Every error sent, by capture_exception or as a built event."""
        return [
            kw["error"] if name == "capture_exception" else kw["hint"]["exc_info"][1]
            for name, kw in self.calls
            if name in {"capture_exception", "capture_event"}
        ]

    def messages(self) -> list[str]:
        return [kw["message"] for name, kw in self.calls if name == "log"]

    def index_of(self, call: str, **match: object) -> int:
        return next(
            i
            for i, (name, kw) in enumerate(self.calls)
            if name == call and all(kw.get(k) == v for k, v in match.items())
        )

    def index_of_log(self, prefix: str) -> int:
        return next(
            i
            for i, (name, kw) in enumerate(self.calls)
            if name == "log" and kw["message"].startswith(prefix)
        )


class _LoggingIntegration:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs


class _Call:
    """A finished modal.FunctionCall: its result, or the error it raised."""

    def __init__(self, recorder: _Recorder, outcome: Callable[[], object]) -> None:
        self._recorder = recorder
        self._outcome = outcome

    def get(self, timeout: float | None = None) -> object:
        self._recorder.calls.append(("get", {"timeout": timeout}))
        return self._outcome()

    def cancel(self, terminate_containers: bool = False) -> None:
        self._recorder.calls.append(
            ("cancel", {"terminate_containers": terminate_containers})
        )


def _stub_modal(recorder: _Recorder) -> types.ModuleType:
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
        def function(
            **kwargs: object,
        ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def decorate(fn: Callable[..., Any]) -> Callable[..., Any]:
                fn.function_kwargs = kwargs  # type: ignore[attr-defined]

                # Runs the call here, as a fresh container would run it there.
                def spawn(*args: object) -> _Call:
                    recorder.calls.append(("spawn", {"fn": fn.__name__, "args": args}))
                    try:
                        result = fn(*args)
                    except Exception as error:  # noqa: BLE001
                        raised = error

                        def outcome() -> object:
                            raise raised

                        return _Call(recorder, outcome)
                    return _Call(recorder, lambda: result)

                fn.spawn = spawn  # type: ignore[attr-defined]
                return fn

            return decorate

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
    """sentry_sdk with the real signatures of the functions the canary calls."""
    sentry_sdk = types.ModuleType("sentry_sdk")
    crons = types.ModuleType("sentry_sdk.crons")
    integrations = types.ModuleType("sentry_sdk.integrations")
    integrations_logging = types.ModuleType("sentry_sdk.integrations.logging")
    utils = types.ModuleType("sentry_sdk.utils")

    def init(**kwargs: object) -> None:
        recorder.calls.append(("init", kwargs))

    def capture_exception(error: BaseException) -> None:
        recorder.calls.append(("capture_exception", {"error": error}))

    def event_from_exception(
        exc_info: BaseException | tuple[Any, Any, Any],
        client_options: dict[str, Any] | None = None,
        mechanism: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        error = exc_info if isinstance(exc_info, BaseException) else exc_info[1]
        event = {
            "level": "error",
            "exception": {"values": [{"type": type(error).__name__}]},
        }
        return event, {"exc_info": (type(error), error, error.__traceback__)}

    def get_client() -> types.SimpleNamespace:
        return types.SimpleNamespace(options={})

    def capture_event(
        event: dict[str, Any],
        hint: dict[str, Any] | None = None,
        scope: object = None,
        **scope_kwargs: object,
    ) -> str | None:
        recorder.calls.append(("capture_event", {"event": event, "hint": hint}))
        return event.get("event_id")

    def capture_message(
        message: str,
        level: str | None = None,
        scope: object = None,
        **scope_kwargs: object,
    ) -> None:
        recorder.calls.append(
            ("capture_message", {"message": message, "level": level, **scope_kwargs})
        )

    def flush(timeout: float | None = None, callback: object = None) -> None:
        recorder.calls.append(("flush", {"timeout": timeout, "callback": callback}))

    def capture_checkin(
        monitor_slug: str | None = None,
        check_in_id: str | None = None,
        status: str | None = None,
        duration: float | None = None,
        monitor_config: dict[str, Any] | None = None,
    ) -> str:
        recorder.calls.append(
            (
                "capture_checkin",
                {
                    "monitor_slug": monitor_slug,
                    "check_in_id": check_in_id,
                    "status": status,
                    "duration": duration,
                    "monitor_config": monitor_config,
                },
            )
        )
        return check_in_id or _RUN

    sentry_sdk.init = init  # type: ignore[attr-defined]
    sentry_sdk.capture_exception = capture_exception  # type: ignore[attr-defined]
    sentry_sdk.capture_event = capture_event  # type: ignore[attr-defined]
    sentry_sdk.get_client = get_client  # type: ignore[attr-defined]
    sentry_sdk.utils = utils  # type: ignore[attr-defined]
    utils.event_from_exception = event_from_exception  # type: ignore[attr-defined]
    sentry_sdk.capture_message = capture_message  # type: ignore[attr-defined]
    sentry_sdk.flush = flush  # type: ignore[attr-defined]
    sentry_sdk.crons = crons  # type: ignore[attr-defined]
    sentry_sdk.integrations = integrations  # type: ignore[attr-defined]
    crons.capture_checkin = capture_checkin  # type: ignore[attr-defined]
    integrations.logging = integrations_logging  # type: ignore[attr-defined]
    integrations_logging.LoggingIntegration = _LoggingIntegration  # type: ignore[attr-defined]
    return {
        "sentry_sdk": sentry_sdk,
        "sentry_sdk.crons": crons,
        "sentry_sdk.utils": utils,
        "sentry_sdk.integrations": integrations,
        "sentry_sdk.integrations.logging": integrations_logging,
    }


def _stub_catalog(recorder: _Recorder, collection_ids: list[str]) -> types.ModuleType:
    dynamical_catalog = types.ModuleType("dynamical_catalog")

    def clear_cache() -> None:
        recorder.calls.append(("clear_cache", {}))

    def load_catalog() -> dict[str, dict[str, Any]]:
        recorder.calls.append(("load_catalog", {}))
        return {cid: {"name": _name(cid)} for cid in collection_ids}

    dynamical_catalog.clear_cache = clear_cache  # type: ignore[attr-defined]
    dynamical_catalog.load_catalog = load_catalog  # type: ignore[attr-defined]
    return dynamical_catalog


def _name(collection_id: str) -> str:
    """The title the stub catalog gives a collection."""
    return collection_id.replace("-", " ").title()


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
    saved_handlers, saved_level, saved_propagate = (
        list(log.handlers),
        log.level,
        log.propagate,
    )
    for handler in saved_handlers:
        log.removeHandler(handler)
    yield log
    for handler in list(log.handlers):
        log.removeHandler(handler)
        handler.close()
    for handler in saved_handlers:
        log.addHandler(handler)
    log.setLevel(saved_level)
    log.propagate = saved_propagate


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
        monkeypatch.setattr(uuid, "uuid4", lambda: uuid.UUID(_RUN))
        monkeypatch.setitem(sys.modules, "modal", _stub_modal(recorder))
        for name, module in _stub_sentry(recorder).items():
            monkeypatch.setitem(sys.modules, name, module)
        monkeypatch.setitem(
            sys.modules, "dynamical_catalog", _stub_catalog(recorder, collection_ids)
        )
        monkeypatch.delenv("SENTRY_DSN", raising=False)

        spec = importlib.util.spec_from_file_location("read_canary_under_test", _SCRIPT)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # The shipped pauses are checked in
        # test_the_budget_fits_inside_modals_timeout; tests do not wait them out.
        module.SHIPPED_CATALOG_BACKOFF_SECONDS = module._CATALOG_BACKOFF_SECONDS
        module.SHIPPED_READ_RETRY_PAUSE_SECONDS = module._READ_RETRY_PAUSE_SECONDS
        module._CATALOG_BACKOFF_SECONDS = (0,)
        module._READ_RETRY_PAUSE_SECONDS = 0.0
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
    assert recorder.coverage() == ["in_progress", "ok"]
    assert recorder.spawns() == []  # nothing failed, so nothing to re-run
    # The terminal check-in must get a real flush budget: the sdk default is 2 s,
    # which a slow Sentry edge exhausts before the envelope leaves the queue.
    assert recorder.flushes() == [
        {"timeout": canary._FLUSH_TIMEOUT_SECONDS, "callback": None}
    ]
    assert canary._FLUSH_TIMEOUT_SECONDS == 15
    assert recorder.exceptions() == []
    # A warm container keeps dynamical_catalog's cache; every run refetches.
    assert recorder.index_of("clear_cache") < recorder.index_of("load_catalog")

    messages = recorder.messages()
    assert messages[0] == (
        "read canary started; dynamical-catalog dynamical-catalog-v, "
        "icechunk icechunk-v, zarr unknown, sentry-sdk sentry-sdk-v"
    )
    assert messages[1] == f"in_progress check-in {_RUN} queued, coverage {_MARKER}"
    assert messages[2].startswith("read canary ok: 8 collections read in ")
    assert f"(slowest collection-3 1.5s); queueing ok check-in {_RUN}" in messages[2]
    assert re.fullmatch(
        rf"ok check-in {_RUN}: flush returned after \d+\.\ds \(budget 15s\)",
        messages[3],
    )
    assert len(messages) == 4
    # Ordering is the point: the start line before Sentry is touched, and the
    # summary (evidence for Modal's logs) before the terminal check-in, so a
    # lost or hung flush cannot erase it.
    assert recorder.index_of_log("read canary started") < recorder.index_of("init")
    assert recorder.index_of_log("read canary ok:") < recorder.index_of(
        "capture_checkin", status="ok"
    )


def test_start_line_precedes_sentry_init_and_reader_import(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)

    def broken_init(**_: object) -> None:
        raise RuntimeError("sentry init exploded")

    monkeypatch.setattr(sys.modules["sentry_sdk"], "init", broken_init)
    with pytest.raises(RuntimeError, match="sentry init exploded"):
        canary.read_canary()
    assert [m[:20] for m in recorder.messages()] == ["read canary started;"]

    # Same guarantee when the reader package itself cannot be imported.
    recorder.calls.clear()
    monkeypatch.setitem(sys.modules, "dynamical_catalog", None)
    with pytest.raises(ImportError):
        canary.read_canary()
    assert [m[:20] for m in recorder.messages()] == ["read canary started;"]


def test_sentry_logging_integration_does_not_double_report_failures(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The failure line is logged at ERROR; only the explicit capture may make an event."""
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
    assert out.count("read canary ok: 8 collections") == 2
    assert re.match(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ INFO read canary started;", out)
    (stream_handler,) = [
        h for h in canary_logger.handlers if h not in recording_handlers
    ]
    assert stream_handler.name == canary._STDOUT_HANDLER
    assert stream_handler.formatter is not None
    assert stream_handler.formatter.converter is time.gmtime  # the Z is earned
    assert canary_logger.propagate is False  # no double printing via root handlers


def test_terminal_checkin_reuses_in_progress_id_and_config(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_check_collection", lambda _cid: 0.1)

    canary.read_canary()

    checkins = [kw for name, kw in recorder.calls if name == "capture_checkin"]
    canary_checkins, coverage_checkins = (
        [kw for kw in checkins if kw["monitor_slug"] == slug]
        for slug in ("read-canary", "read-canary-coverage")
    )
    assert [kw["check_in_id"] for kw in canary_checkins] == [_RUN, _RUN]
    # The publisher pairs a coverage marker with its run by this derived id.
    assert [kw["check_in_id"] for kw in coverage_checkins] == [_MARKER, _MARKER]
    assert len({str(kw["monitor_config"]) for kw in checkins}) == 1
    config = checkins[0]["monitor_config"]
    assert config["schedule"] == {"type": "interval", "value": 10, "unit": "minute"}
    assert config["max_runtime"] == canary._TIMEOUT_SECONDS // 60 + 2
    # Both openings precede any read.
    assert [kw["monitor_slug"] for kw in checkins[:2]] == [
        "read-canary",
        "read-canary-coverage",
    ]


def test_canary_runs_in_a_us_region(
    load_canary: Callable[[list[str]], types.ModuleType],
) -> None:
    # Unpinned, Modal schedules runs worldwide; a run from a country where
    # WeatherNext data is restricted fails those reads with 451.
    canary = load_canary(_CATALOG)

    assert canary.read_canary.function_kwargs["region"] == "us"


def test_each_rerun_is_pinned_to_its_own_region(
    load_canary: Callable[[list[str]], types.ModuleType],
) -> None:
    """One function per region, so placement is fixed at deploy; none is in a
    country the WeatherNext terms exclude."""
    canary = load_canary(_CATALOG)

    assert canary._REGIONS == ("us-east", "us-west", "eu-west")
    assert {
        region: function.function_kwargs["region"]
        for region, function in canary._REGION_FUNCTIONS.items()
    } == {"us-east": "us-east", "us-west": "us-west", "eu-west": "eu-west"}


def test_every_run_and_every_rerun_gets_its_own_container(
    load_canary: Callable[[list[str]], types.ModuleType],
) -> None:
    """A read left hanging dies with its container instead of living on in a
    warm one, and a re-run never reuses the connections, cache, or host state
    of the run whose failure triggered it."""
    canary = load_canary(_CATALOG)

    assert canary.read_canary.function_kwargs["single_use_containers"] is True
    for function in canary._REGION_FUNCTIONS.values():
        assert function.function_kwargs["single_use_containers"] is True
        assert function.function_kwargs["image"] is canary.image
        assert function.function_kwargs["timeout"] >= canary._RETURN_BY_SECONDS
        assert "secrets" not in function.function_kwargs  # no telemetry of its own


def test_the_budget_fits_inside_modals_timeout(
    load_canary: Callable[[list[str]], types.ModuleType],
) -> None:
    canary = load_canary(_CATALOG)

    assert canary._TIMEOUT_SECONDS == 840
    assert canary._MAX_RUNTIME_MINUTES == 16
    assert canary.SHIPPED_CATALOG_BACKOFF_SECONDS == (2, 4, 8, 16)
    assert canary.SHIPPED_READ_RETRY_PAUSE_SECONDS == 5
    # The scheduled run's catalog window and sweep end before the re-runs
    # start, and the last spawn leaves Modal time to start a container before
    # the region's own admission deadline.
    assert canary._CATALOG_WINDOW_SECONDS == 120
    assert (
        canary._CATALOG_WINDOW_SECONDS
        < canary._SWEEP_DEADLINE_SECONDS
        < canary._SPAWN_BY_SECONDS
        < canary._REGION_START_BY_SECONDS
    )
    assert canary._REGION_START_BY_SECONDS - canary._SPAWN_BY_SECONDS >= 60
    # A region admitted at the last moment still gets the full catalog window
    # and two full reads of a collection with the pause between them.
    assert (
        canary._REGION_START_BY_SECONDS
        + canary._CATALOG_WINDOW_SECONDS
        + 2 * canary._READ_ATTEMPT_SECONDS
        + canary.SHIPPED_READ_RETRY_PAUSE_SECONDS
        + canary._REGION_RETURN_MARGIN_SECONDS
        == canary._RETURN_BY_SECONDS
    )
    # The slowest healthy read seen (122 s) fits one read.
    assert canary._READ_ATTEMPT_SECONDS > 122
    # Waiting, cancelling, reporting and the flush keep their reserve.
    assert canary._RETURN_BY_SECONDS < canary._COLLECT_BY_SECONDS
    assert (
        canary._COLLECT_BY_SECONDS
        + canary._CANCEL_SECONDS
        + canary._FLUSH_TIMEOUT_SECONDS
        + 30
        <= canary._TIMEOUT_SECONDS
    )


def _dataset(value: float) -> xr.Dataset:
    return xr.Dataset({"temperature": (("time", "x"), np.array([[value, 3.0]]))})


@pytest.mark.parametrize("value", [1.5, math.nan])
def test_check_collection_reads_corner_value_and_times_it(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
    value: float,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_open_dataset", lambda _cid: _dataset(value))

    elapsed = canary._check_collection("collection-0")

    assert isinstance(elapsed, float)
    assert 0 <= elapsed < 5


def test_check_collection_rejects_inf(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_open_dataset", lambda _cid: _dataset(math.inf))

    with pytest.raises(ValueError, match=r"collection-0\.temperature is inf"):
        canary._check_collection("collection-0")


# --- identifying the canary to the WeatherNext proxy --------------------------


class _ChunkServer(http.server.ThreadingHTTPServer):
    """Serves one virtual chunk file, recording each request's User-Agent."""

    def __init__(self, body: bytes) -> None:
        self.body = body
        self.user_agents: list[str | None] = []
        super().__init__(("127.0.0.1", 0), _ChunkHandler)


class _ChunkHandler(http.server.BaseHTTPRequestHandler):
    server: _ChunkServer

    def do_GET(self) -> None:
        self.server.user_agents.append(self.headers.get("User-Agent"))
        body = self.server.body
        size, status, start, end = len(body), 200, 0, len(body) - 1
        if match := re.fullmatch(r"bytes=(\d+)-(\d*)", self.headers.get("Range", "")):
            start, end = int(match[1]), int(match[2] or size - 1)
            body, status = body[start : end + 1], 206
        self.send_response(status)
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass


@pytest.fixture
def chunk_server() -> Iterator[_ChunkServer]:
    server = _ChunkServer(np.array([[1.5, 3.0]]).tobytes())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()


def test_weathernext_chunk_reads_name_the_canary(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    chunk_server: _ChunkServer,
) -> None:
    """The virtual chunk's HTTP request carries the canary's User-Agent."""
    import icechunk  # noqa: PLC0415
    import zarr  # noqa: PLC0415

    host, port = chunk_server.server_address[:2]
    prefix = f"http://{host}:{port}/chunks/"
    storage = icechunk.local_filesystem_storage(str(tmp_path / "repo"))
    config = icechunk.RepositoryConfig.default()
    config.set_virtual_chunk_container(
        icechunk.VirtualChunkContainer(prefix, icechunk.http_store(), "wn-data")
    )
    repo = icechunk.Repository.create(storage, config=config)
    repo.save_config()
    session = repo.writable_session("main")
    zarr.create_array(
        session.store,
        name="temperature",
        shape=(1, 2),
        chunks=(1, 2),
        dtype="<f8",
        compressors=None,
        dimension_names=("time", "x"),
    )
    # A reference through the container's name, which the reopen must keep.
    session.store.set_virtual_ref(
        "temperature/c/0/0", "vcc://wn-data/data.bin", offset=0, length=16
    )
    session.commit("one virtual chunk")

    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_WN_CHUNKS_PREFIX", prefix)
    # As the catalog opens it: the persisted container, authorized anonymously.
    monkeypatch.setattr(
        sys.modules["dynamical_catalog"],
        "get_repository",
        lambda _cid: icechunk.Repository.open(
            storage,
            authorize_virtual_chunk_access={prefix: icechunk.Credentials.HttpAccess()},
        ),
        raising=False,
    )

    canary._check_collection("collection-0")

    assert chunk_server.user_agents
    if hasattr(icechunk, "Attribution"):
        expected = f"dynamical-stac-read-canary/1 icechunk/{icechunk.__version__}"
        assert all(ua.startswith(expected) for ua in chunk_server.user_agents)
    else:
        expected = f"dynamical-stac-read-canary/1 icechunk-rust-{icechunk.__version__}"
        assert set(chunk_server.user_agents) == {expected}


# --- the catalog window ----------------------------------------------------------


def _loads(
    monkeypatch: pytest.MonkeyPatch,
    recorder: _Recorder,
    outcomes: list[Callable[[], dict[str, Any]]],
) -> None:
    """load_catalog answering with each outcome in turn, the last one repeated."""
    remaining = list(outcomes)

    def load_catalog() -> dict[str, Any]:
        recorder.calls.append(("load_catalog", {}))
        outcome = remaining.pop(0) if len(remaining) > 1 else remaining[0]
        return outcome()

    monkeypatch.setattr(sys.modules["dynamical_catalog"], "load_catalog", load_catalog)


def _catalog_of(ids: list[str]) -> Callable[[], dict[str, Any]]:
    return lambda: {cid: {"name": _name(cid)} for cid in ids}


def _raise(error: BaseException) -> Callable[[], dict[str, Any]]:
    def fail() -> dict[str, Any]:
        raise error

    return fail


def test_the_catalog_is_retried_until_it_loads(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    _loads(
        monkeypatch,
        recorder,
        [
            _raise(TimeoutError("The read operation timed out")),
            _catalog_of(_CATALOG[:3]),  # short: a failed load too
            _catalog_of(_CATALOG),
        ],
    )

    catalog, outcome = canary._load_catalog(time.monotonic() + 30)

    assert sorted(catalog) == _CATALOG
    assert outcome["loaded"] is True
    assert outcome["attempts"] == 3
    assert outcome["error"] is None
    # One clear for the window, so later loads may reuse what earlier ones fetched.
    assert [name for name, _ in recorder.calls if name == "clear_cache"] == [
        "clear_cache"
    ]


def test_a_catalog_that_never_loads_fails_when_the_window_ends(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_CATALOG_MIN_ATTEMPT_SECONDS", 0.05)
    _loads(monkeypatch, recorder, [_raise(ConnectionError("unreachable"))])
    started = time.monotonic()

    catalog, outcome = canary._load_catalog(started + 0.3)

    assert catalog is None
    assert outcome["loaded"] is False
    assert outcome["attempts"] >= 2
    assert "ConnectionError('unreachable')" in outcome["error"]
    assert time.monotonic() - started < 0.5


def test_a_hung_catalog_load_ends_the_window_without_a_second_load(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A second load would race the first for the client's cache."""
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_CATALOG_MIN_ATTEMPT_SECONDS", 0.01)
    release = threading.Event()

    def hang() -> dict[str, Any]:
        release.wait(5)
        return {}

    _loads(monkeypatch, recorder, [hang])
    started = time.monotonic()
    try:
        catalog, outcome = canary._load_catalog(started + 0.2)
    finally:
        release.set()

    assert catalog is None
    assert outcome["attempts"] == 1
    assert "did not finish" in outcome["error"]
    assert time.monotonic() - started < 1


def test_no_catalog_load_starts_without_time_for_it(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
) -> None:
    canary = load_canary(_CATALOG)

    catalog, outcome = canary._load_catalog(time.monotonic() + 1)

    assert catalog is None
    assert outcome == {
        "loaded": False,
        "attempts": 0,
        "seconds": 0.0,
        "error": "no time to load",
    }
    assert [name for name, _ in recorder.calls if name == "load_catalog"] == []


# --- reads ------------------------------------------------------------------------


def test_the_scheduled_sweep_stops_at_its_first_failure(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The scheduled run only triggers the re-runs; reading on would delay them."""
    canary = load_canary(_CATALOG)
    release = threading.Event()

    def check(collection_id: str) -> float:
        if collection_id == "collection-0":
            raise OSError("store unreachable")
        release.wait(5)
        return 0.1

    monkeypatch.setattr(canary, "_check_collection", check)
    started = time.monotonic()
    try:
        _durations, failures, unread = canary._read_all(_CATALOG, deadline=started + 5)
    finally:
        release.set()

    assert time.monotonic() - started < 1
    assert list(failures) == ["collection-0"]
    assert isinstance(failures["collection-0"], OSError)
    # Reads cut short by the failure are unread, not failed.
    assert set(unread) <= set(_CATALOG[1:])


@pytest.mark.parametrize(
    ("raised", "expected"),
    [
        (None, "passed"),
        (OSError("403"), "error"),
        # The library's own timeout is a read that returned an error.
        (TimeoutError("The read operation timed out"), "error"),
    ],
)
def test_an_attempt_tells_an_error_from_a_pass(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
    raised: BaseException | None,
    expected: str,
) -> None:
    canary = load_canary(_CATALOG)

    def check(_cid: str) -> float:
        if raised is not None:
            raise raised
        return 0.25

    monkeypatch.setattr(canary, "_check_collection", check)

    result, detail = canary._attempt("collection-0", 5)

    assert result == expected
    assert detail == ("read in 0.2s" if raised is None else repr(raised))


def test_an_attempt_the_canary_stops_waiting_for_is_a_deadline(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    release = threading.Event()
    monkeypatch.setattr(canary, "_check_collection", lambda _cid: release.wait(5))
    try:
        assert canary._attempt("collection-0", 0.1) == (
            "deadline",
            "no result within 0s",
        )
    finally:
        release.set()


@pytest.mark.parametrize(
    ("attempts", "cell"),
    [
        (["passed"], "passed"),
        (["error", "passed"], "passed"),
        (["deadline", "passed"], "passed"),
        (["error", "error"], "failed"),
        (["error", "deadline"], "not_verified"),
        (["deadline", "deadline"], "not_verified"),
        (["error"], "not_verified"),  # no time for the second read
        ([], "not_verified"),
    ],
)
def test_one_read_of_two_passes_a_collection_in_a_region(
    load_canary: Callable[[list[str]], types.ModuleType],
    attempts: list[str],
    cell: str,
) -> None:
    canary = load_canary(_CATALOG)

    assert canary._cell([(result, "detail") for result in attempts]) == cell


def _scripted(script: dict[str, list[str]]) -> Callable[[str], float]:
    """_check_collection following each collection's script of results.

    "pass" returns, "error" raises, a number sleeps that long and returns.
    Collections without a script pass.
    """
    lock = threading.Lock()
    remaining = {cid: list(results) for cid, results in script.items()}

    def check(collection_id: str) -> float:
        with lock:
            queue_ = remaining.get(collection_id)
            step = queue_.pop(0) if queue_ else "pass"
        if step == "error":
            raise OSError(f"{collection_id} unreadable")
        if step != "pass":
            time.sleep(float(step))
        return 0.1

    return check


def test_read_twice_retries_only_what_did_not_pass(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(
        canary,
        "_check_collection",
        _scripted(
            {
                "collection-1": ["error", "pass"],
                "collection-2": ["error", "error"],
                "collection-3": ["error", "error", "pass"],  # never a third read
            }
        ),
    )

    reads = canary._read_twice(_CATALOG, end=time.monotonic() + 5)

    cells = {cid: canary._cell(attempts) for cid, attempts in reads.items()}
    assert cells == {
        **dict.fromkeys(_CATALOG, "passed"),
        "collection-2": "failed",
        "collection-3": "failed",
    }
    assert [result for result, _ in reads["collection-0"]] == ["passed"]
    assert [result for result, _ in reads["collection-1"]] == ["error", "passed"]
    assert len(reads["collection-3"]) == 2


def test_read_twice_bounds_each_read_and_retries_a_slow_one(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_READ_ATTEMPT_SECONDS", 0.2)
    monkeypatch.setattr(
        canary, "_check_collection", _scripted({"collection-4": ["3", "pass"]})
    )

    reads = canary._read_twice(_CATALOG, end=time.monotonic() + 2)

    assert [result for result, _ in reads["collection-4"]] == ["deadline", "passed"]
    assert canary._cell(reads["collection-4"]) == "passed"


def test_read_twice_reads_every_collection_once_before_any_twice(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_READ_WORKERS", 1)
    order: list[str] = []
    failing = _scripted({cid: ["error"] for cid in _CATALOG[:2]})

    def check(collection_id: str) -> float:
        order.append(collection_id)
        return failing(collection_id)

    monkeypatch.setattr(canary, "_check_collection", check)

    canary._read_twice(_CATALOG, end=time.monotonic() + 5)

    assert order == [*_CATALOG, "collection-0", "collection-1"]


def test_read_twice_starts_nothing_after_its_end(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_READ_WORKERS", 1)
    started: list[str] = []

    def check(collection_id: str) -> float:
        started.append(collection_id)
        time.sleep(0.2)
        return 0.2

    monkeypatch.setattr(canary, "_check_collection", check)
    began = time.monotonic()

    reads = canary._read_twice(_CATALOG, end=began + 0.3)

    assert time.monotonic() - began < 0.6
    assert len(started) <= 2
    unread = [cid for cid, attempts in reads.items() if not attempts]
    assert len(unread) >= len(_CATALOG) - 2
    assert all(canary._cell(reads[cid]) == "not_verified" for cid in unread)


# --- a region's re-run ------------------------------------------------------------


def test_a_region_reruns_the_whole_canary(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setenv("MODAL_REGION", "us-east-1")
    monkeypatch.setattr(
        canary, "_check_collection", _scripted({"collection-2": ["error", "error"]})
    )

    result = canary._run_region("us-east", time.time() + canary._RETURN_BY_SECONDS)

    assert result["region"] == "us-east"
    assert result["placed"] == "us-east-1"
    assert result["status"] == "ran"
    assert result["catalog"]["loaded"] is True
    assert result["names"] == {cid: _name(cid) for cid in _CATALOG}
    assert sorted(result["reads"]) == _CATALOG
    judged = canary._judge_region("us-east", result)
    assert judged["cells"]["collection-2"] == "failed"
    assert recorder.index_of("clear_cache") < recorder.index_of("load_catalog")


def test_a_region_started_too_late_reads_nothing(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Too late for the catalog window and two reads: Modal placed it late,
    which is no observation of the stores."""
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(
        canary, "_check_collection", lambda _cid: pytest.fail("must not read")
    )
    margin = canary._RETURN_BY_SECONDS - canary._REGION_START_BY_SECONDS

    result = canary._run_region("eu-west", time.time() + margin - 1)

    assert result["status"] == "late_start"
    assert [name for name, _ in recorder.calls if name == "load_catalog"] == []
    assert canary._judge_region("eu-west", result)["why"] == "late_start"


def test_a_region_without_a_catalog_reports_it_and_reads_nothing(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_CATALOG_WINDOW_SECONDS", 0.2)
    monkeypatch.setattr(canary, "_CATALOG_MIN_ATTEMPT_SECONDS", 0.05)
    _loads(monkeypatch, recorder, [_raise(ConnectionError("unreachable"))])
    monkeypatch.setattr(
        canary, "_check_collection", lambda _cid: pytest.fail("must not read")
    )

    result = canary._run_region("us-west", time.time() + canary._RETURN_BY_SECONDS)

    assert result["catalog"]["loaded"] is False
    assert result["names"] == {}
    assert result["reads"] == {}
    assert canary._region_status(canary._judge_region("us-west", result), {}) == "fail"


def _ran(
    region: str,
    cells: dict[str, str] | None = None,
    *,
    catalog: list[str] = _CATALOG,
) -> dict[str, Any]:
    """A re-run's result: every collection passed unless `cells` says otherwise.

    A cell of "failed" is two errored reads, "not_verified" one read that the
    canary stopped waiting for.
    """
    reads_for = {
        "passed": [["passed", "read in 0.1s"]],
        "failed": [["error", "OSError('x')"], ["error", "OSError('x')"]],
        "not_verified": [["deadline", "no result within 150s"]],
    }
    cells = cells or {}
    return {
        "region": region,
        "placed": f"{region}-1",
        "status": "ran",
        "catalog": {"loaded": True, "attempts": 1, "seconds": 0.5, "error": None},
        "names": {cid: _name(cid) for cid in catalog},
        "reads": {cid: reads_for[cells.get(cid, "passed")] for cid in catalog},
    }


def _no_catalog(region: str) -> dict[str, Any]:
    return {
        "region": region,
        "placed": f"{region}-1",
        "status": "ran",
        "catalog": {
            "loaded": False,
            "attempts": 7,
            "seconds": 120.0,
            "error": "CatalogFetchError('timed out')",
        },
        "names": {},
        "reads": {},
    }


@pytest.mark.parametrize(
    "result",
    [
        None,
        "ok",
        {**_ran("us-east"), "region": "us-west"},
        {**_ran("us-east"), "status": "maybe"},
        {**_ran("us-east"), "names": {}},  # catalog loaded, yet empty
        {**_ran("us-east", catalog=_CATALOG[:3])},  # under the floor
        {**_ran("us-east"), "reads": {}},
        {**_no_catalog("us-east"), "names": {"collection-0": "x"}},
        {**_ran("us-east"), "catalog": {"loaded": "yes"}},
        {
            **_ran("us-east"),
            "reads": {cid: [["passed", "x"]] * 3 for cid in _CATALOG},
        },
        {**_ran("us-east"), "reads": {cid: [["maybe", "x"]] for cid in _CATALOG}},
    ],
)
def test_a_rerun_result_of_any_other_shape_is_unobserved(
    load_canary: Callable[[list[str]], types.ModuleType],
    result: object,
) -> None:
    """Never a failed read: the canary cannot tell what the region saw."""
    canary = load_canary(_CATALOG)

    assert canary._judge_region("us-east", result) == {
        "id": "us-east",
        "status": "unobserved",
        "why": "invalid_result",
    }


# --- starting, waiting on and cancelling the re-runs -------------------------------


class _Rerun:
    """A region function whose spawn and call behave as told."""

    def __init__(
        self,
        recorder: _Recorder,
        region: str,
        *,
        result: object = None,
        spawn_error: BaseException | None = None,
        get: Callable[[float | None], object] | None = None,
    ) -> None:
        self.recorder = recorder
        self.region = region
        self.result = _ran(region) if result is None else result
        self.spawn_error = spawn_error
        self.get = get

    def spawn(self, return_by: float) -> _Call:
        self.recorder.calls.append(("spawn", {"fn": self.region, "args": (return_by,)}))
        if self.spawn_error is not None:
            raise self.spawn_error
        recorder, region, get = self.recorder, self.region, self.get

        class _RegionCall(_Call):
            def get(self, timeout: float | None = None) -> object:
                recorder.calls.append(("get", {"region": region, "timeout": timeout}))
                return get(timeout) if get is not None else self._outcome()

            def cancel(self, terminate_containers: bool = False) -> None:
                recorder.calls.append(
                    (
                        "cancel",
                        {
                            "region": region,
                            "terminate_containers": terminate_containers,
                        },
                    )
                )

        return _RegionCall(recorder, lambda: self.result)


def _reruns(
    canary: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    recorder: _Recorder,
    **behaviour: dict[str, Any],
) -> None:
    """Replace each region's function; `behaviour` maps us_east=... to _Rerun kwargs."""
    monkeypatch.setattr(
        canary,
        "_REGION_FUNCTIONS",
        {
            region: _Rerun(
                recorder, region, **behaviour.get(region.replace("-", "_"), {})
            )
            for region in canary._REGIONS
        },
    )


def test_reruns_start_together_and_one_that_hangs_costs_the_others_nothing(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    release = threading.Event()

    def hang(timeout: float | None) -> object:
        release.wait(timeout)
        raise TimeoutError("still running")

    _reruns(canary, monkeypatch, recorder, us_west={"get": hang})
    # Leave 0.3 s before the run stops waiting.
    run_started = time.monotonic() - (canary._COLLECT_BY_SECONDS - 0.3)
    monkeypatch.setattr(canary, "_SPAWN_BY_SECONDS", canary._COLLECT_BY_SECONDS)
    try:
        regions = canary._rerun_regions(run_started)
    finally:
        release.set()

    assert [region["id"] for region in regions] == ["us-east", "us-west", "eu-west"]
    assert regions[1] == {"id": "us-west", "status": "unobserved", "why": "no_result"}
    assert regions[0]["cells"] == dict.fromkeys(_CATALOG, "passed")
    assert regions[2]["cells"] == dict.fromkeys(_CATALOG, "passed")
    cancels = [kw for name, kw in recorder.calls if name == "cancel"]
    assert cancels == [{"region": "us-west", "terminate_containers": True}]
    # Every re-run got the same wall-clock deadline.
    assert len({kw["args"] for kw in recorder.spawns()}) == 1


def test_a_rerun_that_cannot_start_is_unobserved(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    _reruns(
        canary,
        monkeypatch,
        recorder,
        eu_west={"spawn_error": RuntimeError("no capacity")},
    )

    regions = canary._rerun_regions(time.monotonic())

    assert regions[2] == {"id": "eu-west", "status": "unobserved", "why": "not_started"}
    assert [kw["fn"] for kw in recorder.spawns()].count("eu-west") == 1


def test_no_rerun_starts_after_its_spawn_deadline(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    _reruns(canary, monkeypatch, recorder)
    run_started = time.monotonic() - canary._SPAWN_BY_SECONDS - 1

    regions = canary._rerun_regions(run_started)

    assert recorder.spawns() == []
    assert {region["why"] for region in regions} == {"not_started"}


def test_a_rerun_that_raises_is_unobserved(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)

    def crash(_timeout: float | None) -> object:
        raise RuntimeError("container exited")

    _reruns(canary, monkeypatch, recorder, us_east={"get": crash})

    regions = canary._rerun_regions(time.monotonic())

    assert regions[0] == {"id": "us-east", "status": "unobserved", "why": "no_result"}


# --- the verdict -------------------------------------------------------------------


def _expected_verdict(statuses: tuple[str, ...]) -> str:
    passing, failing = statuses.count("pass"), statuses.count("fail")
    unobserved = statuses.count("unobserved")
    if not failing:
        return "gap" if unobserved else "ok"
    return "degraded" if passing else "down"


@pytest.mark.parametrize(
    "statuses",
    [
        (a, b, c)
        for a in ("pass", "fail", "unobserved")
        for b in ("pass", "fail", "unobserved")
        for c in ("pass", "fail", "unobserved")
    ],
)
def test_the_verdict_for_every_combination_of_regions(
    load_canary: Callable[[list[str]], types.ModuleType],
    statuses: tuple[str, ...],
) -> None:
    canary = load_canary(_CATALOG)

    assert canary.regional_verdict(list(statuses)) == _expected_verdict(statuses)


def test_regions_that_failed_beside_one_unobserved_are_down(
    load_canary: Callable[[list[str]], types.ModuleType],
) -> None:
    """Every region that could be checked failed."""
    canary = load_canary(_CATALOG)

    assert canary._UNOBSERVED_WITH_ONLY_FAILURES == "down"
    assert canary.regional_verdict(["fail", "fail", "unobserved"]) == "down"
    assert canary.regional_verdict(["fail", "unobserved", "unobserved"]) == "down"


# --- the report ---------------------------------------------------------------------


def _judged(canary: types.ModuleType, *results: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        canary._judge_region(region, result)
        if result.get("status") != "unobserved"
        else result
        for region, result in zip(canary._REGIONS, results, strict=True)
    ]


def _ids(entries: list[dict[str, str]]) -> list[str]:
    return [entry["id"] for entry in entries]


def test_report_of_one_region_failing_one_collection(
    load_canary: Callable[[list[str]], types.ModuleType],
) -> None:
    canary = load_canary(_CATALOG)
    regions = _judged(
        canary,
        _ran("us-east", {"collection-3": "failed"}),
        _ran("us-west"),
        _ran("eu-west"),
    )

    report = canary._read_report(_RUN, "production", regions, "degraded")

    assert report["v"] == 2
    assert report["run"] == _RUN
    assert report["environment"] == "production"
    assert report["verdict"] == "degraded"
    east, west, europe = report["regions"]
    assert east == {
        "id": "us-east",
        "status": "fail",
        "catalog": "loaded",
        "passed": 7,
        "failed": [{"id": "collection-3", "name": "Collection 3"}],
        "not_verified": [],
    }
    assert west["status"] == europe["status"] == "pass"
    assert west["passed"] == 8
    # Passed only where every region read it; failed only where every one
    # failed it: collection-3 read elsewhere is neither.
    assert report["selected"] == 8
    assert report["passed"] == 7
    assert report["failed"] == []
    assert _ids(report["unverified"]) == ["collection-3"]


def test_report_counts_a_collection_failed_only_where_every_region_failed_it(
    load_canary: Callable[[list[str]], types.ModuleType],
) -> None:
    canary = load_canary(_CATALOG)
    broken = {"collection-3": "failed"}
    regions = _judged(
        canary,
        _ran("us-east", broken),
        _ran("us-west", broken),
        _ran("eu-west", broken),
    )

    report = canary._read_report(_RUN, "production", regions, "down")

    assert _ids(report["failed"]) == ["collection-3"]
    assert report["passed"] == 7
    assert report["unverified"] == []


def test_failures_spread_over_regions_never_add_up_to_every_collection(
    load_canary: Callable[[list[str]], types.ModuleType],
) -> None:
    """Each collection failed somewhere and was unknown elsewhere: no region
    saw them all fail, so the report must not say every collection failed."""
    canary = load_canary(_CATALOG)
    thirds = [_CATALOG[0:3], _CATALOG[3:6], _CATALOG[6:8]]
    results = [
        _ran(
            region,
            {
                cid: "failed" if cid in thirds[index] else "not_verified"
                for cid in _CATALOG
            },
        )
        for index, region in enumerate(canary._REGIONS)
    ]

    report = canary._read_report(_RUN, "production", _judged(canary, *results), "down")

    assert report["failed"] == []
    assert report["passed"] == 0
    assert _ids(report["unverified"]) == _CATALOG


def test_a_region_without_a_catalog_leaves_every_collection_unverified(
    load_canary: Callable[[list[str]], types.ModuleType],
) -> None:
    canary = load_canary(_CATALOG)
    regions = _judged(canary, _no_catalog("us-east"), _ran("us-west"), _ran("eu-west"))

    report = canary._read_report(_RUN, "production", regions, "degraded")

    assert report["regions"][0] == {
        "id": "us-east",
        "status": "fail",
        "catalog": "failed",
        "passed": 0,
        "failed": [],
        "not_verified": [],
    }
    assert report["selected"] == 8
    assert report["passed"] == 0
    assert _ids(report["unverified"]) == _CATALOG


def test_no_catalog_anywhere_reports_no_collections(
    load_canary: Callable[[list[str]], types.ModuleType],
) -> None:
    canary = load_canary(_CATALOG)
    regions = _judged(
        canary, _no_catalog("us-east"), _no_catalog("us-west"), _no_catalog("eu-west")
    )

    report = canary._read_report(_RUN, "production", regions, "down")

    assert [region["catalog"] for region in report["regions"]] == ["failed"] * 3
    assert report["selected"] == 0
    assert report["passed"] == 0
    assert report["failed"] == report["unverified"] == []


def test_a_collection_one_region_did_not_list_is_unverified_there(
    load_canary: Callable[[list[str]], types.ModuleType],
) -> None:
    canary = load_canary(_CATALOG)
    regions = _judged(
        canary,
        _ran("us-east"),
        _ran("us-west", catalog=_CATALOG[:7]),
        _ran("eu-west"),
    )

    union = canary._union(regions)
    assert canary._region_status(regions[1], union) == "fail"
    report = canary._read_report(_RUN, "production", regions, "degraded")

    assert report["regions"][1]["passed"] == 7
    assert _ids(report["regions"][1]["not_verified"]) == ["collection-7"]
    assert _ids(report["unverified"]) == ["collection-7"]


def test_report_of_an_unobserved_region(
    load_canary: Callable[[list[str]], types.ModuleType],
) -> None:
    canary = load_canary(_CATALOG)
    regions = _judged(
        canary,
        _ran("us-east"),
        _ran("us-west"),
        {"id": "eu-west", "status": "unobserved", "why": "no_result"},
    )

    report = canary._read_report(_RUN, "production", regions, "gap")

    assert report["regions"][2] == {
        "id": "eu-west",
        "status": "unobserved",
        "why": "no_result",
    }
    assert report["passed"] == 0  # not read in every region
    assert len(report["unverified"]) == 8


def test_report_names_fall_back_to_the_id(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    _loads(
        monkeypatch,
        recorder,
        [
            lambda: {
                cid: {"name": ""} if cid == "collection-0" else {} for cid in _CATALOG
            }
        ],
    )
    monkeypatch.setattr(canary, "_check_collection", lambda _cid: 0.1)

    result = canary._run_region("us-east", time.time() + canary._RETURN_BY_SECONDS)

    assert set(result["names"].values()) == set(_CATALOG)


# --- the run, end to end --------------------------------------------------------------


def _failing_schedule(
    canary: types.ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The scheduled sweep fails collection-5; regional reads go through _REGION_FUNCTIONS."""

    def check(collection_id: str) -> float:
        if collection_id == "collection-5":
            raise OSError("collection-5 unreadable")
        return 0.1

    monkeypatch.setattr(canary, "_check_collection", check)


def test_a_scheduled_failure_that_every_region_reads_clean_is_ok(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    _failing_schedule(canary, monkeypatch)
    _reruns(canary, monkeypatch, recorder)

    canary.read_canary()

    assert sorted(kw["fn"] for kw in recorder.spawns()) == sorted(canary._REGIONS)
    assert recorder.checkins() == ["in_progress", "ok"]
    assert recorder.coverage() == ["in_progress", "ok"]
    assert recorder.events() == []
    (warning,) = recorder.warnings()
    assert warning["level"] == "warning"
    assert warning["message"] == (
        "read canary scheduled run failed; every region re-ran clean"
    )
    detail = warning["contexts"]["read_canary"]
    assert "collection-5" in detail["scheduled"]["failed"]
    assert {region: s["status"] for region, s in detail["regions"].items()} == {
        "us-east": "pass",
        "us-west": "pass",
        "eu-west": "pass",
    }
    assert any(
        m.startswith("read canary ok: 8 collections") for m in recorder.messages()
    )


def test_a_catalog_the_scheduled_run_cannot_load_triggers_the_reruns(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_CATALOG_WINDOW_SECONDS", 0.2)
    monkeypatch.setattr(canary, "_CATALOG_MIN_ATTEMPT_SECONDS", 0.05)
    _loads(monkeypatch, recorder, [_raise(ConnectionError("catalog.json unreachable"))])
    monkeypatch.setattr(
        canary, "_check_collection", lambda _cid: pytest.fail("must not read")
    )
    _reruns(canary, monkeypatch, recorder)

    canary.read_canary()

    assert len(recorder.spawns()) == 3
    assert recorder.checkins() == ["in_progress", "ok"]
    (warning,) = recorder.warnings()
    scheduled = warning["contexts"]["read_canary"]["scheduled"]
    assert scheduled["catalog"]["loaded"] is False
    assert "catalog.json unreachable" in scheduled["catalog"]["error"]


def test_one_region_failing_is_a_regional_partial_outage(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    _failing_schedule(canary, monkeypatch)
    _reruns(
        canary,
        monkeypatch,
        recorder,
        us_east={"result": _ran("us-east", {"collection-5": "failed"})},
    )

    with pytest.raises(
        RuntimeError, match=r"read canary degraded: us-east fail"
    ) as excinfo:
        canary.read_canary()

    assert recorder.checkins() == ["in_progress", "error"]
    assert recorder.coverage() == ["in_progress", "ok"]
    (event,) = recorder.events()
    assert event["event_id"] == _REPORT_EVENT
    report = event["contexts"]["read_canary_report"]
    assert report["verdict"] == "degraded"
    assert [region["status"] for region in report["regions"]] == [
        "fail",
        "pass",
        "pass",
    ]
    assert "collection-5" in event["contexts"]["read_canary"]["scheduled"]["failed"]
    (captured,) = recorder.exceptions()
    assert captured is excinfo.value
    assert recorder.warnings() == []
    assert [f["timeout"] for f in recorder.flushes()] == [15]
    assert recorder.index_of_log("read canary failed") < recorder.index_of(
        "capture_checkin", status="error"
    )


def test_every_region_failing_is_an_outage(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    _failing_schedule(canary, monkeypatch)
    broken = {"collection-5": "failed"}
    _reruns(
        canary,
        monkeypatch,
        recorder,
        **{
            region.replace("-", "_"): {"result": _ran(region, broken)}
            for region in canary._REGIONS
        },
    )

    with pytest.raises(RuntimeError, match=r"read canary down"):
        canary.read_canary()

    assert recorder.checkins() == ["in_progress", "error"]
    assert recorder.coverage() == ["in_progress", "ok"]
    (event,) = recorder.events()
    report = event["contexts"]["read_canary_report"]
    assert report["verdict"] == "down"
    assert _ids(report["failed"]) == ["collection-5"]


def test_no_catalog_in_any_region_is_an_outage(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The STAC catalog is on the path to every read: no catalog, no reads."""
    canary = load_canary(_CATALOG)
    _failing_schedule(canary, monkeypatch)
    _reruns(
        canary,
        monkeypatch,
        recorder,
        **{
            region.replace("-", "_"): {"result": _no_catalog(region)}
            for region in canary._REGIONS
        },
    )

    with pytest.raises(RuntimeError, match=r"read canary down"):
        canary.read_canary()

    assert recorder.coverage() == ["in_progress", "ok"]
    report = recorder.events()[0]["contexts"]["read_canary_report"]
    assert report["selected"] == 0


def test_reruns_that_could_not_run_without_a_failure_are_a_gap(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    _failing_schedule(canary, monkeypatch)
    _reruns(
        canary,
        monkeypatch,
        recorder,
        eu_west={"spawn_error": RuntimeError("no capacity")},
    )

    with pytest.raises(RuntimeError, match=r"read canary gap"):
        canary.read_canary()

    assert recorder.checkins() == ["in_progress", "error"]
    assert recorder.coverage() == ["in_progress", "error"]
    # The marker goes first: a publisher reading between them sees an outage,
    # never a marker without its error.
    assert recorder.index_of(
        "capture_checkin", monitor_slug="read-canary-coverage", status="error"
    ) < recorder.index_of("capture_checkin", monitor_slug="read-canary", status="error")
    report = recorder.events()[0]["contexts"]["read_canary_report"]
    assert report["verdict"] == "gap"
    failure = next(m for m in recorder.messages() if m.startswith("read canary failed"))
    assert f"with coverage marker {_MARKER}" in failure


def test_failed_regions_beside_an_unobserved_one_are_an_outage(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    _failing_schedule(canary, monkeypatch)
    broken = {"collection-5": "failed"}
    _reruns(
        canary,
        monkeypatch,
        recorder,
        us_east={"result": _ran("us-east", broken)},
        us_west={"result": _ran("us-west", broken)},
        eu_west={"spawn_error": RuntimeError("no capacity")},
    )

    with pytest.raises(RuntimeError, match=r"read canary down"):
        canary.read_canary()

    assert recorder.coverage() == ["in_progress", "ok"]
    report = recorder.events()[0]["contexts"]["read_canary_report"]
    assert [region["status"] for region in report["regions"]] == [
        "fail",
        "fail",
        "unobserved",
    ]


def test_an_unexpected_fault_is_a_plain_failure(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Never ok, never a gap."""
    canary = load_canary(_CATALOG)
    _failing_schedule(canary, monkeypatch)

    def explode(_started: float) -> list[dict[str, Any]]:
        raise KeyError("bug")

    monkeypatch.setattr(canary, "_rerun_regions", explode)

    with pytest.raises(KeyError, match="bug"):
        canary.read_canary()

    assert recorder.checkins() == ["in_progress", "error"]
    assert recorder.coverage() == ["in_progress", "ok"]
    (event,) = recorder.events()
    assert "read_canary_report" not in event.get("contexts", {})


def test_the_run_owns_its_check_in_ids_when_sentry_captures_nothing(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """capture_checkin returns None when the SDK drops the event (no DSN, say);
    the run's ids, and the marker derived from them, must not depend on it."""
    canary = load_canary(_CATALOG)
    _failing_schedule(canary, monkeypatch)
    _reruns(canary, monkeypatch, recorder, eu_west={"spawn_error": RuntimeError("x")})
    capture = sys.modules["sentry_sdk.crons"].capture_checkin

    def dropped(**kwargs: object) -> None:
        capture(**kwargs)

    monkeypatch.setattr(sys.modules["sentry_sdk.crons"], "capture_checkin", dropped)

    with pytest.raises(RuntimeError, match="read canary gap"):
        canary.read_canary()

    ids = {
        (kw["monitor_slug"], kw["check_in_id"])
        for name, kw in recorder.calls
        if name == "capture_checkin"
    }
    assert ids == {("read-canary", _RUN), ("read-canary-coverage", _MARKER)}


@pytest.mark.parametrize("broken", ["_read_report", "capture_event"])
def test_a_report_that_cannot_be_sent_leaves_the_run_unchanged(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
    broken: str,
) -> None:
    canary = load_canary(_CATALOG)
    _failing_schedule(canary, monkeypatch)
    _reruns(
        canary,
        monkeypatch,
        recorder,
        us_east={"result": _ran("us-east", {"collection-5": "failed"})},
    )

    def explode(*_: object, **__: object) -> None:
        raise KeyError("report exploded")

    if broken == "_read_report":
        monkeypatch.setattr(canary, "_read_report", explode)
    else:
        monkeypatch.setattr(sys.modules["sentry_sdk"], "capture_event", explode)

    with pytest.raises(RuntimeError, match=r"read canary degraded") as excinfo:
        canary.read_canary()

    assert recorder.events() == []
    assert [
        kw["error"] for name, kw in recorder.calls if name == "capture_exception"
    ] == [excinfo.value]
    assert recorder.checkins() == ["in_progress", "error"]
    assert recorder.coverage() == ["in_progress", "ok"]
    assert [f["timeout"] for f in recorder.flushes()] == [15]
    assert any(
        m.startswith("could not send the run's report") for m in recorder.messages()
    )


def test_a_rerun_runs_the_real_region_code_through_spawn(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The shipped wrappers, spawned as Modal would, reach a verdict."""
    canary = load_canary(_CATALOG)
    _failing_schedule(canary, monkeypatch)

    with pytest.raises(RuntimeError, match=r"read canary down"):
        canary.read_canary()

    assert sorted(kw["fn"] for kw in recorder.spawns()) == [
        "rerun_eu_west",
        "rerun_us_east",
        "rerun_us_west",
    ]
    report = recorder.events()[0]["contexts"]["read_canary_report"]
    # collection-5 errors on every read, in every region.
    assert _ids(report["failed"]) == ["collection-5"]
    assert report["passed"] == 7


def test_a_read_the_sweep_deadline_stops_is_a_failure(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    release = threading.Event()

    def check(collection_id: str) -> float:
        if collection_id == "collection-0":
            release.wait(5)
        return 0.1

    monkeypatch.setattr(canary, "_check_collection", check)
    try:
        durations, failures, unread = canary._read_all(
            _CATALOG, deadline=time.monotonic() + 0.2
        )
    finally:
        release.set()

    assert list(failures) == ["collection-0"]
    assert "deadline" in str(failures["collection-0"])
    assert sorted(durations) == _CATALOG[1:]
    assert unread == []
