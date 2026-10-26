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

import icechunk
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

    def exceptions(self) -> list[BaseException]:
        return [kw["error"] for name, kw in self.calls if name == "capture_exception"]

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

    def init(**kwargs: object) -> None:
        recorder.calls.append(("init", kwargs))

    def capture_exception(error: BaseException) -> None:
        recorder.calls.append(("capture_exception", {"error": error}))

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
        "sentry_sdk.integrations": integrations,
        "sentry_sdk.integrations.logging": integrations_logging,
    }


def _stub_catalog(recorder: _Recorder, collection_ids: list[str]) -> types.ModuleType:
    dynamical_catalog = types.ModuleType("dynamical_catalog")

    def clear_cache() -> None:
        recorder.calls.append(("clear_cache", {}))

    def load_catalog() -> dict[str, None]:
        recorder.calls.append(("load_catalog", {}))
        return dict.fromkeys(collection_ids)

    dynamical_catalog.clear_cache = clear_cache  # type: ignore[attr-defined]
    dynamical_catalog.load_catalog = load_catalog  # type: ignore[attr-defined]
    return dynamical_catalog


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
        # The shipped pause between re-reads is checked in
        # test_the_budget_fits_inside_modals_timeout; tests do not wait it out.
        module.SHIPPED_CONFIRM_INTERVAL_SECONDS = module._CONFIRM_INTERVAL_SECONDS
        module._CONFIRM_INTERVAL_SECONDS = 0.0
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
    assert recorder.spawns() == []  # nothing failed, so nothing to confirm
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
    assert canary.confirm_reads.function_kwargs["region"] == "us"


def test_every_run_and_every_confirmation_gets_its_own_container(
    load_canary: Callable[[list[str]], types.ModuleType],
) -> None:
    """A read left hanging dies with its container instead of living on in a
    warm one, and a confirmation never reuses the connections, cache, or host
    state of the run whose failure it re-reads."""
    canary = load_canary(_CATALOG)

    assert canary.read_canary.function_kwargs["single_use_containers"] is True
    assert canary.confirm_reads.function_kwargs["single_use_containers"] is True
    assert canary.confirm_reads.function_kwargs["image"] is canary.image
    assert (
        canary.confirm_reads.function_kwargs["timeout"]
        >= canary._CONFIRM_BUDGET_SECONDS + 30
    )


def test_the_budget_fits_inside_modals_timeout(
    load_canary: Callable[[list[str]], types.ModuleType],
) -> None:
    canary = load_canary(_CATALOG)

    assert canary.SHIPPED_CONFIRM_INTERVAL_SECONDS == 15
    assert (
        canary._CATALOG_DEADLINE_SECONDS
        < canary._MAIN_PASS_DEADLINE_SECONDS
        < canary._CONFIRM_DEADLINE_SECONDS
    )
    # Reporting and the flush keep their reserve after confirmation gives up.
    assert (
        canary._CONFIRM_DEADLINE_SECONDS + canary._FLUSH_TIMEOUT_SECONDS + 60
        <= canary._TIMEOUT_SECONDS
    )
    # Two full re-reads and the pause between them fit one confirmation.
    assert (
        2 * canary._CONFIRM_ATTEMPT_SECONDS + canary.SHIPPED_CONFIRM_INTERVAL_SECONDS
        < canary._CONFIRM_BUDGET_SECONDS
    )


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

    with pytest.raises(RuntimeError, match=r"failed for 1/8 collections") as excinfo:
        canary.read_canary()

    # One failure does not stop the sweep; the confirmation re-read it once.
    assert sorted(checked) == sorted([*_CATALOG, "collection-5"])
    assert recorder.checkins() == ["in_progress", "error"]
    # A confirmed failure is a conclusive run.
    assert recorder.coverage() == ["in_progress", "ok"]
    assert [f["timeout"] for f in recorder.flushes()] == [15]
    (captured,) = recorder.exceptions()
    assert captured is excinfo.value  # captured as raised, so it carries a traceback
    assert "collection-5: ValueError('collection-5.var is inf')" in str(captured)
    assert "re-read: ValueError('collection-5.var is inf')" in str(captured)
    assert recorder.warnings() == []
    failure = next(m for m in recorder.messages() if m.startswith("read canary failed"))
    assert f"; queueing error check-in {_RUN}: " in failure
    assert "collection-5" in failure
    assert recorder.index_of_log("read canary failed") < recorder.index_of(
        "capture_checkin", status="error"
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
        sys.modules["dynamical_catalog"], "load_catalog", broken_load_catalog
    )
    monkeypatch.setattr(
        canary, "_check_collection", lambda _cid: pytest.fail("must not read")
    )

    with pytest.raises(ConnectionError, match=r"catalog\.json unreachable"):
        canary.read_canary()

    # Previously this raised straight through the in_progress check-in and
    # Sentry only noticed once max_runtime elapsed.
    assert recorder.checkins() == ["in_progress", "error"]
    assert recorder.coverage() == ["in_progress", "ok"]
    assert [f["timeout"] for f in recorder.flushes()] == [15]
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
    assert [f["timeout"] for f in recorder.flushes()] == [15]
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


def _dataset(value: float) -> xr.Dataset:
    return xr.Dataset({"temperature": (("time", "x"), np.array([[value, 3.0]]))})


@pytest.mark.parametrize("value", [1.5, math.nan])
def test_check_collection_reads_corner_value_and_times_it(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
    value: float,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(
        sys.modules["dynamical_catalog"],
        "open",
        lambda _cid, **_: _dataset(value),
        raising=False,
    )

    elapsed = canary._check_collection("collection-0")

    assert isinstance(elapsed, float)
    assert 0 <= elapsed < 5


def test_check_collection_rejects_inf(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(
        sys.modules["dynamical_catalog"],
        "open",
        lambda _cid, **_: _dataset(math.inf),
        raising=False,
    )

    with pytest.raises(ValueError, match=r"collection-0\.temperature is inf"):
        canary._check_collection("collection-0")


def test_check_collection_opens_with_longer_storage_backoff(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    opened: list[tuple[str, icechunk.RepositoryConfig]] = []

    def fake_open(
        collection_id: str, *, repository_config: icechunk.RepositoryConfig
    ) -> xr.Dataset:
        opened.append((collection_id, repository_config))
        return _dataset(1.5)

    monkeypatch.setattr(
        sys.modules["dynamical_catalog"], "open", fake_open, raising=False
    )

    canary._check_collection("collection-0")

    [(collection_id, config)] = opened
    assert collection_id == "collection-0"
    assert isinstance(config, icechunk.RepositoryConfig)
    assert config.storage.retries == icechunk.StorageRetriesSettings(
        max_tries=20, initial_backoff_ms=1_000, max_backoff_ms=5_000
    )
    # Timeouts are left to the repository's own persisted settings.
    assert config.storage.timeouts is None


def test_storage_retries_fit_a_confirmation_attempt(
    load_canary: Callable[[list[str]], types.ModuleType],
) -> None:
    """The sleeps alone, at their longest, leave a re-read most of its time.

    object_store's decorrelated jitter makes each sleep at most twice the last,
    capped, so a fetch whose every attempt fails sleeps at most this long in
    total before giving up.
    """
    canary = load_canary(_CATALOG)
    longest, total = canary._STORAGE_INITIAL_BACKOFF_MS / 1000, 0.0
    for _ in range(canary._STORAGE_MAX_TRIES - 1):
        total += longest
        longest = min(canary._STORAGE_MAX_BACKOFF_MS / 1000, 2 * longest)
    assert total < canary._MAIN_PASS_DEADLINE_SECONDS - canary._CATALOG_DEADLINE_SECONDS
    assert canary._STORAGE_MAX_BACKOFF_MS / 1000 < canary._CONFIRM_ATTEMPT_SECONDS / 10


# --- confirming a failed read from a fresh container --------------------------


def _flaky(failing: dict[str, int]) -> Callable[[str], float]:
    """A read that fails each listed collection that many times, then succeeds."""
    remaining = dict(failing)

    def check(collection_id: str) -> float:
        if remaining.get(collection_id, 0) > 0:
            remaining[collection_id] -= 1
            raise TimeoutError(f"{collection_id}: operation timed out")
        return 0.1

    return check


def test_a_failure_that_reads_back_twice_is_reported_unconfirmed(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """2026-10-24 01:04Z: one fetch timed out, and the next run read it fine.
    The run reports `error` on read-canary, never `ok`, with its coverage
    marker, so the status page publishes a gap and a lost marker errs to down."""
    canary = load_canary(_CATALOG)
    monkeypatch.setenv("MODAL_REGION", "us-east")
    monkeypatch.setattr(canary, "_check_collection", _flaky({"collection-2": 1}))

    canary.read_canary()  # an inconclusive run is not a failed function

    assert recorder.checkins() == ["in_progress", "error"]
    assert recorder.coverage() == ["in_progress", "error"]
    # The marker goes first, so a publisher reading between them sees the
    # pair or the bare error — down — never a bare marker.
    assert recorder.index_of(
        "capture_checkin", monitor_slug="read-canary-coverage", status="error"
    ) < recorder.index_of("capture_checkin", monitor_slug="read-canary", status="error")
    (spawn,) = recorder.spawns()
    assert spawn["fn"] == "confirm_reads"
    assert spawn["args"][0] == ["collection-2"]
    assert recorder.exceptions() == []
    (warning,) = recorder.warnings()
    assert warning["level"] == "warning"
    assert warning["message"] == "read canary could not confirm a failed read"
    evidence = warning["contexts"]["read_canary"]
    assert evidence["unconfirmed"] == {
        "collection-2": "TimeoutError('collection-2: operation timed out')"
    }
    assert evidence["regions"] == {"run": "us-east", "confirmation": "us-east"}
    assert len(evidence["re-reads"]["collection-2"]) == 2
    assert [f["timeout"] for f in recorder.flushes()] == [15]
    line = next(m for m in recorder.messages() if m.startswith("read canary could"))
    assert f"queueing error check-in {_RUN} with coverage marker {_MARKER}" in line


def test_a_failure_that_fails_its_first_reread_is_confirmed(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    checked: list[str] = []
    flaky = _flaky({"collection-2": 2})

    def check(collection_id: str) -> float:
        checked.append(collection_id)
        return flaky(collection_id)

    monkeypatch.setattr(canary, "_check_collection", check)

    with pytest.raises(RuntimeError, match=r"failed for 1/8 collections"):
        canary.read_canary()

    # The first failed re-read settles it; there is no second.
    assert checked.count("collection-2") == 2
    assert recorder.checkins() == ["in_progress", "error"]
    assert recorder.coverage() == ["in_progress", "ok"]
    assert len(recorder.exceptions()) == 1
    assert recorder.warnings() == []


def test_a_second_reread_failure_confirms(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fails in the sweep, reads back once, then fails again."""
    canary = load_canary(_CATALOG)
    calls: dict[str, int] = {}

    def check(collection_id: str) -> float:
        calls[collection_id] = calls.get(collection_id, 0) + 1
        if collection_id == "collection-4" and calls[collection_id] != 2:
            raise OSError("connection reset")
        return 0.1

    monkeypatch.setattr(canary, "_check_collection", check)

    with pytest.raises(RuntimeError, match=r"failed for 1/8 collections"):
        canary.read_canary()

    assert calls["collection-4"] == 3
    assert recorder.coverage() == ["in_progress", "ok"]


def test_one_confirmed_failure_outranks_unconfirmed_ones(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(
        canary, "_check_collection", _flaky({"collection-1": 1, "collection-6": 9})
    )

    with pytest.raises(RuntimeError, match=r"failed for 1/8 collections") as excinfo:
        canary.read_canary()

    assert "collection-6" in str(excinfo.value)
    assert "collection-1" not in str(excinfo.value)
    assert recorder.checkins() == ["in_progress", "error"]
    assert recorder.coverage() == ["in_progress", "ok"]


@pytest.mark.parametrize(
    "broken",
    [
        pytest.param("spawn", id="confirmation cannot start"),
        pytest.param("get", id="confirmation raises"),
        pytest.param("timeout", id="confirmation does not return"),
        pytest.param("missing", id="confirmation omits the collection"),
        pytest.param("malformed", id="confirmation returns garbage"),
    ],
)
def test_a_missing_confirmation_is_a_confirmed_failure(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
    broken: str,
) -> None:
    """Missing evidence is never evidence of health."""
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_check_collection", _flaky({"collection-2": 1}))

    def outcome() -> object:
        if broken == "get":
            raise RuntimeError("remote function crashed")
        if broken == "timeout":
            raise TimeoutError
        if broken == "missing":
            return {"region": "us-east", "reads": {}}
        return {"region": "us-east", "reads": {"collection-2": "ok"}}

    def spawn(*args: object) -> _Call:
        recorder.calls.append(("spawn", {"fn": "confirm_reads", "args": args}))
        if broken == "spawn":
            raise ConnectionError("modal unreachable")
        return _Call(recorder, outcome)

    monkeypatch.setattr(canary.confirm_reads, "spawn", spawn)

    with pytest.raises(RuntimeError, match=r"failed for 1/8 collections") as excinfo:
        canary.read_canary()

    assert "confirmation missing" in str(excinfo.value)
    assert recorder.checkins() == ["in_progress", "error"]
    assert recorder.coverage() == ["in_progress", "ok"]
    cancels = [kw for name, kw in recorder.calls if name == "cancel"]
    if broken in {"get", "timeout"}:
        assert cancels == [{"terminate_containers": True}]
    else:
        assert cancels == []


def test_a_hung_read_does_not_hold_the_run_past_its_deadline(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A read that never returns is a failed attempt at the sweep's deadline;
    the run confirms it elsewhere and reports instead of waiting for Modal to
    kill it."""
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_MAIN_PASS_DEADLINE_SECONDS", 0.5)
    never = threading.Event()
    hung = {"collection-3"}

    def check(collection_id: str) -> float:
        if collection_id in hung:
            hung.discard(collection_id)  # the confirmation's reads are fine
            never.wait()
        return 0.1

    monkeypatch.setattr(canary, "_check_collection", check)

    started = time.monotonic()
    try:
        canary.read_canary()
    finally:
        never.set()

    assert time.monotonic() - started < 5
    assert recorder.checkins() == ["in_progress", "error"]
    assert recorder.coverage() == ["in_progress", "error"]
    (warning,) = recorder.warnings()
    assert "collection-3" in warning["contexts"]["read_canary"]["unconfirmed"]


def test_reads_never_started_are_confirmed_not_failed(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With the only worker stuck, the queued collections were never
    attempted: each goes to the confirmation, and reading fine there counts as
    read, not as an unconfirmed failure."""
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_MAIN_PASS_DEADLINE_SECONDS", 0.5)
    monkeypatch.setattr(canary, "_READ_WORKERS", 1)
    never = threading.Event()
    hung = {"collection-0"}

    def check(collection_id: str) -> float:
        if collection_id in hung:
            hung.discard(collection_id)
            never.wait()
        return 0.1

    monkeypatch.setattr(canary, "_check_collection", check)

    try:
        canary.read_canary()
    finally:
        never.set()

    (spawn,) = recorder.spawns()
    assert spawn["args"][0] == _CATALOG
    (warning,) = recorder.warnings()
    assert list(warning["contexts"]["read_canary"]["unconfirmed"]) == ["collection-0"]


def test_a_hung_catalog_load_fails_the_run_inside_its_budget(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_CATALOG_DEADLINE_SECONDS", 0.2)
    never = threading.Event()

    def hung_load_catalog() -> dict[str, None]:
        never.wait()
        return {}

    monkeypatch.setattr(
        sys.modules["dynamical_catalog"], "load_catalog", hung_load_catalog
    )

    try:
        with pytest.raises(TimeoutError, match=r"catalog"):
            canary.read_canary()
    finally:
        never.set()

    assert recorder.checkins() == ["in_progress", "error"]
    assert recorder.coverage() == ["in_progress", "ok"]
    assert recorder.spawns() == []


def test_confirm_reads_reads_each_collection_twice_from_a_fresh_catalog(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setenv("MODAL_REGION", "us-west")
    checked: list[str] = []
    monkeypatch.setattr(
        canary, "_check_collection", lambda cid: checked.append(cid) or 0.1
    )

    result = canary.confirm_reads(
        ["collection-1", "collection-2"], time.time() + canary._CONFIRM_BUDGET_SECONDS
    )

    assert sorted(checked) == ["collection-1"] * 2 + ["collection-2"] * 2
    assert result["region"] == "us-west"
    assert set(result["reads"]) == {"collection-1", "collection-2"}
    assert all(canary._read_back(attempts) for attempts in result["reads"].values())
    assert recorder.index_of("clear_cache") < recorder.index_of_log("confirming")


def test_confirm_reads_bounds_each_attempt(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_CONFIRM_ATTEMPT_SECONDS", 0.2)
    never = threading.Event()

    def check(_collection_id: str) -> float:
        never.wait()
        return 0.1

    monkeypatch.setattr(canary, "_check_collection", check)

    try:
        result = canary.confirm_reads(
            ["collection-1"], time.time() + canary._CONFIRM_BUDGET_SECONDS
        )
    finally:
        never.set()

    (attempt,) = result["reads"]["collection-1"]
    assert attempt[0] is False
    assert "TimeoutError" in attempt[1]
    assert not canary._read_back(result["reads"]["collection-1"])


def test_confirm_reads_never_starts_an_attempt_it_cannot_finish(
    load_canary: Callable[[list[str]], types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Out of time is confirmation missing, never a read failure or a pass."""
    canary = load_canary(_CATALOG)
    checked: list[str] = []
    monkeypatch.setattr(
        canary, "_check_collection", lambda cid: checked.append(cid) or 0.1
    )

    result = canary.confirm_reads(
        ["collection-1"], time.time() + canary._CONFIRM_ATTEMPT_SECONDS - 1
    )

    assert checked == []
    assert result["reads"]["collection-1"] == [(False, "no time left to re-read")]
    assert not canary._read_back(result["reads"]["collection-1"])


def test_the_run_owns_its_check_in_ids_when_sentry_captures_nothing(
    load_canary: Callable[[list[str]], types.ModuleType],
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """capture_checkin returns None when the SDK drops the event (no DSN, say);
    the run's ids, and the marker derived from them, must not depend on it."""
    canary = load_canary(_CATALOG)
    monkeypatch.setattr(canary, "_check_collection", _flaky({"collection-2": 1}))
    capture = sys.modules["sentry_sdk.crons"].capture_checkin

    def dropped(**kwargs: object) -> None:
        capture(**kwargs)

    monkeypatch.setattr(sys.modules["sentry_sdk.crons"], "capture_checkin", dropped)

    canary.read_canary()

    ids = {
        (kw["monitor_slug"], kw["check_in_id"])
        for name, kw in recorder.calls
        if name == "capture_checkin"
    }
    assert ids == {("read-canary", _RUN), ("read-canary-coverage", _MARKER)}
