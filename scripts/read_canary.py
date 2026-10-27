#!/usr/bin/env python3
"""Modal cron — hot-storage read canary for the dynamical.org catalog.

Every 10 minutes this opens every collection in the live STAC catalog from
its Icechunk store on S3 and reads a single value from each, exercising the
full icechunk -> S3 -> zarr decode path for the whole catalog, not just one
dataset. The run sends an `in_progress` Sentry cron check-in on start and
closes it `ok` or `error`; a hung or killed run is caught when it exceeds
`max_runtime` rather than waiting for the next scheduled miss.

Every run also logs a start line and a one-line summary to stdout, so
`modal app logs dynamical-read-canary` is evidence of whether and how the
canary ran that does not depend on Sentry. On 2026-09-10, during a Sentry US
ingestion incident, two consecutive check-ins never showed up and the status
page showed "Data product reads" down for 25 minutes; nothing outside Sentry
could show whether those two runs had executed, let alone what they read.

This is the data-plane half of the 99.5% uptime SLA: proof that reads actually
resolve, not merely that catalog.json is served.

A read that fails is re-read from a fresh container before it counts. Each
collection that failed, or that the sweep never reached, is read again twice by
`confirm_reads`, in its own single-use container. A collection without a
positive read, in the sweep or in both re-reads, is a confirmed failure: the
run closes `error` as it always has. A run whose every failure read back is one
the canary could not confirm. It still closes `read-canary` as `error`, never
`ok`, and also closes a second monitor, `read-canary-coverage`, as `error`
under a check-in id derived from the run's own. The status publisher
(dynamical.org-data) treats only that exact pair as a monitoring gap, so a
lost or late marker leaves an outage, and only a full sweep's `ok` ends one.
Missing confirmation (the call failed, timed out, or left a collection out) is
a confirmed failure, never a pass.

A run with a confirmed failure sends its error event under an id derived from
the run's check-in id, carrying a report of which collections passed, failed,
or could not be verified. The status publisher fetches it by that id to say
how much of the catalog an outage affects; the report never changes the
verdict.

Deploy:
    modal deploy scripts/read_canary.py

Configure:
    modal secret create sentry-read-canary \
        SENTRY_DSN="https://<key>@<org>.ingest.us.sentry.io/<project>"

The icechunk stores are public AWS Open Data buckets, read anonymously, so no
AWS credentials are needed. If a monitored store ever requires signed access,
attach an AWS secret to the function.
"""

from __future__ import annotations

import functools
import importlib.metadata
import logging
import queue
import sys
import threading
import time
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import modal

if TYPE_CHECKING:
    import xarray as xr

image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "dynamical-catalog>=1.0.0",
    "sentry-sdk>=2.72.0",
)

app = modal.App("dynamical-read-canary")

# Floor on the catalog size, so a truncated/empty catalog fails loudly instead
# of passing vacuously — with no collections the read loop checks nothing and
# would otherwise report `ok`. The live catalog has ~12; this is a conservative
# floor well below that.
MIN_COLLECTIONS = 6

# Modal kills the container at this timeout, so a run can never legitimately
# stay `in_progress` past it. `max_runtime` (below) adds a couple of minutes
# of buffer on top before Sentry declares the check-in hung.
_TIMEOUT_SECONDS = 600
_MAX_RUNTIME_MINUTES = _TIMEOUT_SECONDS // 60 + 2

# sentry-sdk's default flush budget is `shutdown_timeout`, 2 seconds. If
# Sentry's ingest edge is slow to accept an envelope, the terminal check-in can
# still be queued when flush gives up and Modal reclaims the container, and the
# run then reads as hung or missed even though every read passed. The SDK does
# not retry a rejected envelope, so this covers a slow edge, not a failing one.
# 15 s matches reformatters' cron monitoring and is well inside the schedule.
_FLUSH_TIMEOUT_SECONDS = 15

# One budget from the run's start, inside _TIMEOUT_SECONDS. Healthy sweeps take
# 18-32 s; a read still going at the sweep's deadline is a failed attempt that
# the confirmation re-reads. The run stops waiting for the confirmation at
# _CONFIRM_DEADLINE_SECONDS and keeps the rest for reporting and the flush.
_CATALOG_DEADLINE_SECONDS = 60
_MAIN_PASS_DEADLINE_SECONDS = 240
_CONFIRM_DEADLINE_SECONDS = 500
_READ_WORKERS = 8

# The confirmation re-reads each collection _CONFIRM_READS times, a pause
# apart, each attempt bounded, and starts no attempt it could not finish before
# its own deadline. It returns a little before the run stops waiting.
_CONFIRM_READS = 2
_CONFIRM_ATTEMPT_SECONDS = 90
_CONFIRM_INTERVAL_SECONDS = 15
_CONFIRM_BUDGET_SECONDS = 240
_CONFIRM_RETURN_MARGIN_SECONDS = 10
_NO_TIME_TO_REREAD = "no time left to re-read"

# The second monitor, closed `error` only on a run the canary could not
# confirm. Its check-in id is uuid5 of the run's read-canary id (as hex) in
# this namespace; dynamical.org-data's status.py holds the same constant and
# pairs the two by it.
_MONITOR_SLUG = "read-canary"
_COVERAGE_MONITOR_SLUG = "read-canary-coverage"
_COVERAGE_NAMESPACE = uuid.UUID("d014545d-f123-4e15-9893-6bfff7bbc831")

# A failed run sends its error event under uuid5 of its read-canary id (as hex)
# in this namespace, with a `read_canary_report` context when it has confirmed
# failures. dynamical.org-data's status.py holds the same constant and fetches
# the report by it.
_REPORT_NAMESPACE = uuid.UUID("f19ee126-79b9-4217-95db-f305e99ce3a6")
_REPORT_VERSION = 1


# Unpinned, Modal places runs in any of its regions worldwide. The WeatherNext 2
# collections are served only to countries their terms permit, and a run placed
# in one that is not fails those reads with HTTP 451 although the stores are
# fine. The broad US region keeps every run in the US at a lower price
# multiplier than any single narrow region.
_REGION = "us"

# The canary names itself in the User-Agent of its WeatherNext chunk reads, so
# proxy analytics can tell our own traffic apart.
_WN_CHUNKS_PREFIX = "https://wn.dynamical.org/"
_CLIENT = "dynamical-stac-read-canary/1"
# The service token puts the canary's reads in our services' own allowance at
# the WeatherNext proxy's rate limit. It comes from the wn-service-token Modal
# secret; without it the reads go out as before and count as public traffic.
_SERVICE_TOKEN_ENV = "WN_SERVICE_TOKEN"  # noqa: S105
_SERVICE_TOKEN_HEADER = "X-Dynamical-Service-Token"  # noqa: S105
_WN_SECRET = modal.Secret.from_name("wn-service-token")


_STDOUT_HANDLER = "read_canary.stdout"


def _logger() -> logging.Logger:
    """The canary's stdout logger, wired once per container.

    Modal captures stdout; python's root logger only emits WARNING and up, so
    the INFO lines need their own handler. Warm containers re-enter
    `read_canary`, hence the guard, keyed on our own handler so that another
    handler on this logger cannot suppress it. Propagation is off so a root
    handler (a library calling basicConfig, say) cannot print every line twice;
    sentry-sdk's logging integration hooks the logger itself, not the root, so
    with `enable_logs=True` it still forwards a copy as Sentry logs.
    """
    log = logging.getLogger("read_canary")
    log.setLevel(logging.INFO)
    log.propagate = False
    if not any(handler.name == _STDOUT_HANDLER for handler in log.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.name = _STDOUT_HANDLER
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ"
        )
        formatter.converter = time.gmtime
        handler.setFormatter(formatter)
        log.addHandler(handler)
    return log


def _runtime_versions() -> str:
    """The deployed read stack; the image pins only lower bounds."""

    def _version(name: str) -> str:
        # Evidence, not a precondition: a renamed distribution must not turn
        # the canary's start line into a failed run.
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            return "unknown"

    return ", ".join(
        f"{name} {_version(name)}"
        for name in ("dynamical-catalog", "icechunk", "zarr", "sentry-sdk")
    )


def _user_agent() -> str:
    """The User-Agent of the canary's WeatherNext chunk reads."""
    import icechunk  # noqa: PLC0415

    # icechunk 2.3 keeps a configured user agent as a prefix of its own token;
    # earlier releases replace theirs with it, so name the library ourselves.
    if hasattr(icechunk, "Attribution"):
        return _CLIENT
    return f"{_CLIENT} icechunk-rust-{icechunk.__version__}"


def _open_dataset(collection_id: str) -> xr.Dataset:
    """The collection's `main` tip, its WeatherNext chunk reads identified."""
    import os  # noqa: PLC0415

    import dynamical_catalog  # noqa: PLC0415
    import icechunk  # noqa: PLC0415
    import xarray as xr  # noqa: PLC0415

    repo = dynamical_catalog.get_repository(collection_id)
    config = repo.config
    # A config's containers replace the persisted ones wholesale, so every
    # container is carried over and only the WeatherNext stores gain the agent,
    # keeping the options and headers they were persisted with.
    wn_containers = [
        container
        for container in (config.virtual_chunk_containers or {}).values()
        if container.url_prefix.startswith(_WN_CHUNKS_PREFIX)
        and isinstance(container.store, icechunk.ObjectStoreConfig.Http)
    ]
    # The token goes only into this reopened config, which is never saved.
    token = os.environ.get(_SERVICE_TOKEN_ENV)
    for container in wn_containers:
        # The Http variant's fields are positional: (opts, headers).
        opts, headers = container.store._0, container.store._1  # noqa: SLF001
        if token:
            headers = {**(headers or {}), _SERVICE_TOKEN_HEADER: token}
        store = icechunk.http_store(
            opts={**(opts or {}), "user_agent": _user_agent()}, headers=headers
        )
        config.set_virtual_chunk_container(
            icechunk.VirtualChunkContainer(container.url_prefix, store, container.name)
        )
    if wn_containers:
        # Without new credentials, reopen keeps the ones the catalog authorized.
        repo = repo.reopen(config=config)
    # icechunk manages its own metadata; zarr's consolidated metadata doesn't apply.
    return xr.open_zarr(repo.readonly_session("main").store, consolidated=False)


def _check_collection(collection_id: str) -> float:
    """Read one value from the collection; return the wall time it took."""
    import math  # noqa: PLC0415

    started = time.monotonic()
    ds = _open_dataset(collection_id)
    first_var = next(iter(ds.data_vars))
    da = ds[first_var]
    value = da.isel(dict.fromkeys(da.dims, 0)).load().item()

    # NaN is fine (sparse/unobserved corner cells), but the read must return a
    # real number — an inf or a non-numeric means the decode path is broken.
    if not isinstance(value, float | int):
        raise TypeError(f"{collection_id}.{first_var} -> {value!r}")
    if isinstance(value, float) and math.isinf(value):
        raise ValueError(f"{collection_id}.{first_var} is inf")
    return time.monotonic() - started


def _run_with_deadline[T](fn: Callable[[], T], seconds: float, what: str) -> T:
    """fn's result, or TimeoutError once `seconds` pass without one.

    fn runs on a daemon thread, which is abandoned rather than joined when it
    overruns: a thread cannot be killed, and a daemon one cannot hold up
    reporting or the interpreter's exit. The single-use container takes it.
    """
    outcome: list[tuple[bool, Any]] = []

    def target() -> None:
        try:
            outcome.append((True, fn()))
        except Exception as error:  # noqa: BLE001
            outcome.append((False, error))

    thread = threading.Thread(target=target, name=f"read-canary {what}", daemon=True)
    thread.start()
    thread.join(max(0.0, seconds))
    if not outcome:
        raise TimeoutError(f"{what} did not finish within {seconds:.0f}s")
    succeeded, value = outcome[0]
    if succeeded:
        return value
    raise value


def _read_all(
    collection_ids: list[str], *, deadline: float
) -> tuple[dict[str, float], dict[str, BaseException], list[str]]:
    """Read one value from every collection until the monotonic `deadline`.

    Returns each read's wall time, each failed read's error, and the
    collections no worker reached. Every collection is attempted even after one
    fails, so a failure reports the full set of broken stores rather than the
    first one. A read still going at the deadline is a failure; its daemon
    worker is abandoned.
    """
    pending: queue.SimpleQueue[str] = queue.SimpleQueue()
    for collection_id in collection_ids:
        pending.put(collection_id)
    results: queue.SimpleQueue[tuple[str, float | None, BaseException | None]] = (
        queue.SimpleQueue()
    )

    def work() -> None:
        while True:
            try:
                collection_id = pending.get_nowait()
            except queue.Empty:
                return
            try:
                results.put((collection_id, _check_collection(collection_id), None))
            except Exception as error:  # noqa: BLE001
                results.put((collection_id, None, error))

    for index in range(min(_READ_WORKERS, len(collection_ids))):
        threading.Thread(target=work, name=f"read-canary {index}", daemon=True).start()

    durations: dict[str, float] = {}
    failures: dict[str, BaseException] = {}

    def record(item: tuple[str, float | None, BaseException | None]) -> None:
        collection_id, duration, error = item
        if error is not None:
            failures[collection_id] = error
        elif duration is not None:
            durations[collection_id] = duration

    while len(durations) + len(failures) < len(collection_ids):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            record(results.get(timeout=remaining))
        except queue.Empty:
            break

    # Taking the queue empty first stops the workers starting anything more.
    unattempted: list[str] = []
    while True:
        try:
            unattempted.append(pending.get_nowait())
        except queue.Empty:
            break
    while True:
        try:
            record(results.get_nowait())
        except queue.Empty:
            break
    for collection_id in collection_ids:
        if (
            collection_id not in durations
            and collection_id not in failures
            and collection_id not in unattempted
        ):
            failures[collection_id] = TimeoutError(
                f"read did not finish by the sweep's {_MAIN_PASS_DEADLINE_SECONDS}s "
                "deadline"
            )
    return durations, failures, sorted(unattempted)


def _confirm_one(collection_id: str, deadline: float) -> list[tuple[bool, str]]:
    """Up to _CONFIRM_READS bounded re-reads, stopping at the first failure.

    `deadline` is wall-clock (time.time()), since the run that set it is in
    another container. An attempt that could not finish before it is never
    started; its place is recorded as _NO_TIME_TO_REREAD.
    """
    attempts: list[tuple[bool, str]] = []
    for attempt in range(_CONFIRM_READS):
        if attempt:
            time.sleep(_CONFIRM_INTERVAL_SECONDS)
        if time.time() + _CONFIRM_ATTEMPT_SECONDS > deadline:
            attempts.append((False, _NO_TIME_TO_REREAD))
            break
        try:
            seconds = _run_with_deadline(
                lambda: _check_collection(collection_id),
                _CONFIRM_ATTEMPT_SECONDS,
                f"re-read of {collection_id}",
            )
        except Exception as error:  # noqa: BLE001
            attempts.append((False, repr(error)))
            break
        attempts.append((True, f"read in {seconds:.1f}s"))
    return attempts


def _read_back(attempts: object) -> bool:
    """Whether a confirmation shows a collection readable: every re-read passed."""
    return (
        isinstance(attempts, list)
        and len(attempts) == _CONFIRM_READS
        and all(
            isinstance(attempt, tuple) and len(attempt) == 2 and attempt[0] is True
            for attempt in attempts
        )
    )


def _confirm_all(
    collection_ids: list[str], deadline: float
) -> dict[str, list[tuple[bool, str]]]:
    """_confirm_one for every collection, _READ_WORKERS at a time."""
    pending: queue.SimpleQueue[str] = queue.SimpleQueue()
    for collection_id in collection_ids:
        pending.put(collection_id)
    reads: dict[str, list[tuple[bool, str]]] = {}

    def work() -> None:
        while True:
            try:
                collection_id = pending.get_nowait()
            except queue.Empty:
                return
            reads[collection_id] = _confirm_one(collection_id, deadline)

    workers = [
        threading.Thread(target=work, name=f"read-canary confirm {index}", daemon=True)
        for index in range(min(_READ_WORKERS, len(collection_ids)))
    ]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(max(0.0, deadline - time.time()))
    return {
        collection_id: list(reads.get(collection_id, [(False, _NO_TIME_TO_REREAD)]))
        for collection_id in collection_ids
    }


@app.function(
    image=image,
    timeout=_CONFIRM_BUDGET_SECONDS + 60,
    secrets=[_WN_SECRET],
    region=_REGION,
    single_use_containers=True,
)
def confirm_reads(collection_ids: list[str], deadline: float) -> dict[str, Any]:
    """Re-read collections from a fresh container, with a fresh catalog.

    The run spawns this for every collection that failed or went unread, so
    a fault confined to its own container, host, or connections does not
    repeat here. Returns this container's Modal region and each collection's
    re-read attempts as (passed, detail) pairs; `deadline` is wall-clock.
    """
    import os  # noqa: PLC0415

    import dynamical_catalog  # noqa: PLC0415

    log = _logger()
    dynamical_catalog.clear_cache()
    region = os.environ.get("MODAL_REGION", "unknown")
    log.info("confirming %d collections in %s", len(collection_ids), region)
    reads = _confirm_all(collection_ids, deadline)
    log.info(
        "confirmation read back %d of %d collections",
        sum(_read_back(attempts) for attempts in reads.values()),
        len(collection_ids),
    )
    return {"region": region, "reads": reads}


def _confirm_remotely(
    collection_ids: list[str], *, run_started: float
) -> tuple[dict[str, Any] | None, str]:
    """The confirmation's result, or None and why there is none.

    Bounded by the run's _CONFIRM_DEADLINE_SECONDS. A call that does not
    return by then is cancelled and its container terminated.
    """
    log = _logger()
    remaining = run_started + _CONFIRM_DEADLINE_SECONDS - time.monotonic()
    if remaining <= _CONFIRM_RETURN_MARGIN_SECONDS:
        return None, "no time left to confirm"
    deadline = time.time() + min(
        remaining - _CONFIRM_RETURN_MARGIN_SECONDS, _CONFIRM_BUDGET_SECONDS
    )
    try:
        call = _run_with_deadline(
            lambda: confirm_reads.spawn(collection_ids, deadline),
            remaining,
            "starting the confirmation",
        )
    except Exception as error:  # noqa: BLE001
        return None, f"could not start: {error!r}"
    try:
        wait = run_started + _CONFIRM_DEADLINE_SECONDS - time.monotonic()
        result = _run_with_deadline(
            lambda: call.get(timeout=max(0.0, wait)),
            wait + 5,
            "the confirmation",
        )
    except Exception as error:  # noqa: BLE001
        try:
            _run_with_deadline(
                lambda: call.cancel(terminate_containers=True),
                10,
                "cancelling the confirmation",
            )
        except Exception:
            log.exception("cancelling the confirmation failed")
        return None, f"did not return: {error!r}"
    if not isinstance(result, dict) or not isinstance(result.get("reads"), dict):
        return None, f"returned {type(result).__name__}, not its result"
    return result, ""


def _confirmed_failures(
    failures: dict[str, BaseException],
    unattempted: list[str],
    confirmation: dict[str, Any] | None,
    missing: str,
) -> tuple[dict[str, str], dict[str, str]]:
    """Split the sweep's shortfall into confirmed and unconfirmed failures.

    Confirmed: any collection without a positive read in the sweep or in both
    re-reads, including one the confirmation could not attempt or left out.
    Unconfirmed: a failed read that read back twice. A collection the sweep
    never reached that reads back twice is simply read.
    """
    reads: dict[str, Any] = confirmation["reads"] if confirmation else {}
    confirmed: dict[str, str] = {}
    unconfirmed: dict[str, str] = {}
    for collection_id in sorted([*failures, *unattempted]):
        error = failures.get(collection_id)
        sweep = repr(error) if error is not None else "not reached by the sweep"
        attempts = reads.get(collection_id)
        if _read_back(attempts):
            if error is not None:
                unconfirmed[collection_id] = sweep
            continue
        if confirmation is None:
            why = f"confirmation missing: {missing}"
        elif not isinstance(attempts, list) or not attempts:
            why = "confirmation missing: no re-read returned"
        elif attempts[-1] == (False, _NO_TIME_TO_REREAD):
            why = f"confirmation missing: {_NO_TIME_TO_REREAD}"
        else:
            why = f"re-read: {attempts[-1][1]}"
        confirmed[collection_id] = f"{sweep}; {why}"
    return confirmed, unconfirmed


def _read_report(
    run: str,
    environment: str,
    catalog: dict[str, Any],
    *,
    durations: dict[str, float],
    failures: dict[str, BaseException],
    confirmation: dict[str, Any] | None,
    confirmed: dict[str, str],
) -> dict[str, Any]:
    """Every catalog collection as passed, failed, or unverified.

    Passed: a positive sweep read, or both re-reads. Failed: confirmed, and at
    least one read was seen to fail, in the sweep (its deadline included) or a
    re-read. Unverified: confirmed with no read seen to fail, such as one the
    sweep never reached whose confirmation is missing.
    """
    reads: dict[str, Any] = confirmation["reads"] if confirmation else {}
    passed = 0
    failed: list[dict[str, str]] = []
    unverified: list[dict[str, str]] = []
    for collection_id in sorted(catalog):
        attempts = reads.get(collection_id)
        if collection_id in durations or _read_back(attempts):
            passed += 1
            continue
        if collection_id not in confirmed:
            raise ValueError(f"{collection_id} is neither read nor confirmed")
        config = catalog[collection_id]
        name = config.get("name") if isinstance(config, dict) else None
        entry = {
            "id": collection_id,
            "name": name if isinstance(name, str) and name else collection_id,
        }
        failed_reread = isinstance(attempts, list) and any(
            isinstance(attempt, tuple)
            and len(attempt) == 2
            and attempt[0] is False
            and attempt[1] != _NO_TIME_TO_REREAD
            for attempt in attempts
        )
        if collection_id in failures or failed_reread:
            failed.append(entry)
        else:
            unverified.append(entry)
    return {
        "v": _REPORT_VERSION,
        "run": run,
        "environment": environment,
        "selected": len(catalog),
        "passed": passed,
        "failed": failed,
        "unverified": unverified,
    }


def _capture_failure(
    error: BaseException,
    event_id: str,
    report: Callable[[], dict[str, Any]] | None,
) -> None:
    """Send the run's error event under `event_id`, with its report if any.

    Best effort: if the event or its report cannot be built or sent, the error
    goes out as a plain capture_exception, as it did before reports existed.
    """
    import sentry_sdk  # noqa: PLC0415
    import sentry_sdk.utils  # noqa: PLC0415

    try:
        event, hint = sentry_sdk.utils.event_from_exception(
            error, client_options=sentry_sdk.get_client().options
        )
        event["event_id"] = event_id
        if report is not None:
            event.setdefault("contexts", {})["read_canary_report"] = report()
        sentry_sdk.capture_event(event, hint=hint)
    except Exception:  # noqa: BLE001
        _logger().warning(
            "could not send the run's report as event %s; capturing the error "
            "without it",
            event_id,
            exc_info=True,
        )
        sentry_sdk.capture_exception(error)


@app.function(
    image=image,
    schedule=modal.Period(minutes=10),
    secrets=[modal.Secret.from_name("sentry-read-canary"), _WN_SECRET],
    timeout=_TIMEOUT_SECONDS,
    region=_REGION,
    # A read abandoned at the sweep's deadline dies with its container instead
    # of living on in a warm one beside the next run.
    single_use_containers=True,
)
def read_canary() -> None:  # noqa: PLR0915
    import os  # noqa: PLC0415
    from typing import Literal  # noqa: PLC0415

    # The start line goes out before the third-party imports and anything else
    # that can fail or hang, so a run that dies early still leaves a trace in
    # Modal's logs of having begun. Versions come from installed metadata, not
    # from importing the packages.
    log = _logger()
    started = time.monotonic()
    log.info("read canary started; %s", _runtime_versions())

    import dynamical_catalog  # noqa: PLC0415
    import sentry_sdk  # noqa: PLC0415
    import sentry_sdk.crons  # noqa: PLC0415
    from sentry_sdk.integrations.logging import LoggingIntegration  # noqa: PLC0415

    # No-op when SENTRY_DSN is unset (e.g. the secret isn't attached yet).
    # `event_level=None`: the failure line below is logged at ERROR, and the
    # default integration would turn that into a second error event beside the
    # explicit one. Breadcrumbs and Sentry logs stay on.
    environment = os.environ.get("SENTRY_ENVIRONMENT", "production")
    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        environment=environment,
        enable_logs=True,
        keep_alive=True,
        integrations=[LoggingIntegration(event_level=None)],
    )
    monitor_config = {
        # Must match the `modal.Period` schedule above.
        "schedule": {"type": "interval", "value": 10, "unit": "minute"},
        "timezone": "UTC",
        "checkin_margin": 5,
        "max_runtime": _MAX_RUNTIME_MINUTES,
        "failure_issue_threshold": 1,
        "recovery_threshold": 1,
    }
    # The run's own id rather than capture_checkin's return value, which is None
    # whenever the SDK does not capture the event (no DSN, say); the coverage
    # marker's id is derived from it.
    check_in_id = uuid.uuid4().hex
    coverage_id = uuid.uuid5(_COVERAGE_NAMESPACE, check_in_id).hex
    sentry_sdk.crons.capture_checkin(
        monitor_slug=_MONITOR_SLUG,
        check_in_id=check_in_id,
        status="in_progress",
        monitor_config=monitor_config,
    )
    sentry_sdk.crons.capture_checkin(
        monitor_slug=_COVERAGE_MONITOR_SLUG,
        check_in_id=coverage_id,
        status="in_progress",
        monitor_config=monitor_config,
    )
    log.info("in_progress check-in %s queued, coverage %s", check_in_id, coverage_id)

    def _finish(
        status: Literal["ok", "error"], coverage: Literal["ok", "error"] = "ok"
    ) -> None:
        # The marker goes first: a publisher that reads between the two sees
        # the bare error, an outage, never a marker without its error.
        sentry_sdk.crons.capture_checkin(
            monitor_slug=_COVERAGE_MONITOR_SLUG,
            check_in_id=coverage_id,
            status=coverage,
            monitor_config=monitor_config,
        )
        sentry_sdk.crons.capture_checkin(
            monitor_slug=_MONITOR_SLUG,
            check_in_id=check_in_id,
            status=status,
            monitor_config=monitor_config,
        )
        # Modal may reclaim the container the moment this function returns; an
        # unflushed terminal check-in is lost and reads as a hung run. The
        # elapsed time is logged as evidence: a flush that returned early left
        # nothing queued, one that ran the whole budget did not drain (which
        # envelope was still pending, and whether it was later delivered, it
        # cannot say).
        flush_started = time.monotonic()
        sentry_sdk.flush(timeout=_FLUSH_TIMEOUT_SECONDS)
        log.info(
            "%s check-in %s: flush returned after %.1fs (budget %ds)",
            status,
            check_in_id,
            time.monotonic() - flush_started,
            _FLUSH_TIMEOUT_SECONDS,
        )

    # Set once the run has confirmed failures to report.
    report: Callable[[], dict[str, Any]] | None = None
    try:
        # A warm container keeps dynamical_catalog's module-level catalog cache;
        # each run must fetch catalog.json afresh or it checks a stale listing.
        dynamical_catalog.clear_cache()
        catalog = _run_with_deadline(
            dynamical_catalog.load_catalog,
            started + _CATALOG_DEADLINE_SECONDS - time.monotonic(),
            "loading the catalog",
        )
        collection_ids = sorted(catalog)
        if len(collection_ids) < MIN_COLLECTIONS:
            raise RuntimeError(
                f"catalog returned {len(collection_ids)} collections, "
                f"expected >= {MIN_COLLECTIONS}"
            )
        durations, failures, unattempted = _read_all(
            collection_ids, deadline=started + _MAIN_PASS_DEADLINE_SECONDS
        )
        confirmation: dict[str, Any] | None = None
        missing = ""
        if failures or unattempted:
            log.warning(
                "sweep left %d failed and %d unread of %d collections after "
                "%.1fs; confirming from a fresh container",
                len(failures),
                len(unattempted),
                len(collection_ids),
                time.monotonic() - started,
            )
            confirmation, missing = _confirm_remotely(
                sorted([*failures, *unattempted]), run_started=started
            )
        confirmed, unconfirmed = _confirmed_failures(
            failures, unattempted, confirmation, missing
        )
        if confirmed:
            # Built only when the event is sent, so that a fault building it
            # cannot change what this run raises.
            report = functools.partial(
                _read_report,
                check_in_id,
                environment,
                catalog,
                durations=durations,
                failures=failures,
                confirmation=confirmation,
                confirmed=confirmed,
            )
            raise RuntimeError(
                f"read canary failed for {len(confirmed)}/{len(collection_ids)} "
                "collections:\n"
                + "\n".join(f"{cid}: {why}" for cid, why in confirmed.items())
            )
    except Exception as error:
        # Anything that goes wrong after the in_progress check-in closes it as
        # `error` rather than leaving Sentry to declare a hang at max_runtime.
        # Evidence first: the log line must not depend on the check-in or the
        # flush getting through.
        log.error(
            "read canary failed after %.1fs; queueing error check-in %s: %s",
            time.monotonic() - started,
            check_in_id,
            error,
        )
        _capture_failure(error, uuid.uuid5(_REPORT_NAMESPACE, check_in_id).hex, report)
        _finish("error")
        raise

    if unconfirmed:
        # Evidence first, as above. Never `ok`: an `ok` would end a failure
        # still standing from an earlier run, which only a full sweep may do.
        log.warning(
            "read canary could not confirm %d failed reads after %.1fs; queueing "
            "error check-in %s with coverage marker %s: %s",
            len(unconfirmed),
            time.monotonic() - started,
            check_in_id,
            coverage_id,
            "; ".join(f"{cid}: {why}" for cid, why in unconfirmed.items()),
        )
        confirmed_by = confirmation or {}
        sentry_sdk.capture_message(
            "read canary could not confirm a failed read",
            level="warning",
            contexts={
                "read_canary": {
                    "unconfirmed": unconfirmed,
                    "re-reads": {
                        cid: confirmed_by.get("reads", {}).get(cid)
                        for cid in unconfirmed
                    },
                    "regions": {
                        "run": os.environ.get("MODAL_REGION", "unknown"),
                        "confirmation": confirmed_by.get("region", "unknown"),
                    },
                }
            },
        )
        _finish("error", coverage="error")
        return

    # A collection the sweep never reached was read in the confirmation, and
    # has no sweep time.
    slowest_id, slowest = max(
        durations.items(), key=lambda item: item[1], default=("none", 0.0)
    )
    log.info(
        "read canary ok: %d collections read in %.1fs (slowest %s %.1fs); "
        "queueing ok check-in %s",
        len(collection_ids),
        time.monotonic() - started,
        slowest_id,
        slowest,
        check_in_id,
    )
    # Every collection read succeeded — report liveness. Any exception above
    # skips this line, so Sentry opens an incident.
    _finish("ok")
