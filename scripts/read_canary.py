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

Any failure in the scheduled run, at the catalog step or at a data read, only
triggers a check: the canary then runs again in full (the catalog and every
collection) in three fresh single-use containers, one each in US East, US West
and Europe West (`_REGIONS`), and those re-runs alone decide the verdict. Each
container gives the catalog up to two minutes of retries, and a collection
passes in a region if one of its two reads there succeeds. Every region
passing closes the run `ok` (a warning event keeps the scheduled failure
visible). Some regions failing is a regional partial outage, all of them an
outage: the run closes `error` and sends its error event under an id derived
from the run's check-in id, carrying a report of what each region read. The
status publisher (dynamical.org-data) fetches it by that id to tell the two
apart and to name the regions. A run that cannot tell, because a region's
container never started or returned and no region failed, also closes a second
monitor, `read-canary-coverage`, as `error` under a check-in id derived from
the run's own; the publisher treats only that exact pair as a monitoring gap.

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
# of buffer on top before Sentry declares the check-in hung. A failed run can
# outlast the 10-minute schedule and overlap the next run; the publisher orders
# runs by when they started, so the newer one's result governs.
_TIMEOUT_SECONDS = 840
_MAX_RUNTIME_MINUTES = _TIMEOUT_SECONDS // 60 + 2

# sentry-sdk's default flush budget is `shutdown_timeout`, 2 seconds. If
# Sentry's ingest edge is slow to accept an envelope, the terminal check-in can
# still be queued when flush gives up and Modal reclaims the container, and the
# run then reads as hung or missed even though every read passed. The SDK does
# not retry a rejected envelope, so this covers a slow edge, not a failing one.
# 15 s matches reformatters' cron monitoring and is well inside the schedule.
_FLUSH_TIMEOUT_SECONDS = 15

# Every container retries the catalog for up to _CATALOG_WINDOW_SECONDS, one
# load at a time with these pauses between, and starts no load with less than
# _CATALOG_MIN_ATTEMPT_SECONDS of the window left. A load still running when
# the window ends ends the step: another would race it for the client's cache.
_CATALOG_WINDOW_SECONDS = 120
_CATALOG_BACKOFF_SECONDS = (2, 4, 8, 16)
_CATALOG_MIN_ATTEMPT_SECONDS = 5

# One budget from the scheduled run's start, inside _TIMEOUT_SECONDS. Healthy
# runs take 15-145 s. The scheduled sweep stops at its first failure, or at
# _SWEEP_DEADLINE_SECONDS, and the re-runs are started by _SPAWN_BY_SECONDS.
# Each region returns by _RETURN_BY_SECONDS; the run stops waiting at
# _COLLECT_BY_SECONDS and keeps the rest for reporting and the flush.
_SWEEP_DEADLINE_SECONDS = 215
_SPAWN_BY_SECONDS = 235
_SPAWN_SECONDS = 20
_RETURN_BY_SECONDS = 740
_COLLECT_BY_SECONDS = 750
_CANCEL_SECONDS = 10
_READ_WORKERS = 8

# In a region each collection gets up to _READ_ATTEMPTS reads, a pause apart,
# first reads before second ones, each bounded at _READ_ATTEMPT_SECONDS (the
# slowest healthy read seen is 122 s). One read passing passes it. A region
# stops reading _REGION_RETURN_MARGIN_SECONDS before it must return, and one
# that starts too late to give the catalog its window and a collection both of
# its reads does nothing: Modal placed it late, which is not a failed read.
_READ_ATTEMPTS = 2
_READ_ATTEMPT_SECONDS = 150
_READ_RETRY_PAUSE_SECONDS = 5
_REGION_RETURN_MARGIN_SECONDS = 5
_REGION_READ_SECONDS = (
    _READ_ATTEMPTS * _READ_ATTEMPT_SECONDS + _READ_RETRY_PAUSE_SECONDS
)
_REGION_START_BY_SECONDS = (
    _RETURN_BY_SECONDS
    - _REGION_RETURN_MARGIN_SECONDS
    - _CATALOG_WINDOW_SECONDS
    - _REGION_READ_SECONDS
)

# The second monitor, closed `error` only on a run whose re-runs could not
# reach a verdict. Its check-in id is uuid5 of the run's read-canary id (as hex) in
# this namespace; dynamical.org-data's status.py holds the same constant and
# pairs the two by it.
_MONITOR_SLUG = "read-canary"
_COVERAGE_MONITOR_SLUG = "read-canary-coverage"
_COVERAGE_NAMESPACE = uuid.UUID("d014545d-f123-4e15-9893-6bfff7bbc831")

# A failed run sends its error event under uuid5 of its read-canary id (as hex)
# in this namespace, with a `read_canary_report` context when its re-runs
# reported. dynamical.org-data's status.py holds the same constant and fetches
# the report by it.
_REPORT_NAMESPACE = uuid.UUID("f19ee126-79b9-4217-95db-f305e99ce3a6")
_REPORT_VERSION = 2


# Unpinned, Modal places runs in any of its regions worldwide. The WeatherNext 2
# collections are served only to countries their terms permit, and a run placed
# in one that is not fails those reads with HTTP 451 although the stores are
# fine. The broad US region keeps every run in the US at a lower price
# multiplier than any single narrow region.
_REGION = "us"

# The re-runs, each pinned to a narrow region (1.75x the base price, against
# 1.15x for broad `us`) and only run after a scheduled failure. None is in a
# country the WeatherNext 2 terms exclude. The order is the report's.
_REGIONS = ("us-east", "us-west", "eu-west")

# What a region's re-run found: every collection read, or not.
_PASS = "pass"  # noqa: S105
_FAIL = "fail"
# No result to judge: the container did not start, start in time, or return
# one the run could use.
_UNOBSERVED = "unobserved"
# The verdict when no region passed and at least one could not be observed:
# every region that could be checked failed.
_UNOBSERVED_WITH_ONLY_FAILURES = "down"

# The canary names itself in the User-Agent of its WeatherNext chunk reads, so
# proxy analytics can tell our own traffic apart.
_WN_CHUNKS_PREFIX = "https://wn.dynamical.org/"
_CLIENT = "dynamical-stac-read-canary/1"


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
    for container in wn_containers:
        # The Http variant's fields are positional: (opts, headers).
        opts, headers = container.store._0, container.store._1  # noqa: SLF001
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
    """Read one value from every collection until its first failure or `deadline`.

    Returns each read's wall time, each failed read's error, and the
    collections no worker reached. The scheduled run only triggers the
    re-runs, so it stops at the first failed read rather than reading on to
    the deadline. A read still going at the deadline is a failure; its daemon
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

    while len(durations) + len(failures) < len(collection_ids) and not failures:
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
    # A read still going is a failure only if the deadline stopped it; one cut
    # short by another's failure is simply unread.
    stopped_early = bool(failures) and time.monotonic() < deadline
    unfinished = [
        collection_id
        for collection_id in collection_ids
        if collection_id not in durations
        and collection_id not in failures
        and collection_id not in unattempted
    ]
    if stopped_early:
        unattempted.extend(unfinished)
    else:
        for collection_id in unfinished:
            failures[collection_id] = TimeoutError(
                "read did not finish by the sweep's deadline"
            )
    return durations, failures, sorted(unattempted)


def _load_catalog(window_end: float) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """The catalog, retried until the monotonic `window_end`, and how it went.

    Loads run one at a time, each bounded by what is left of the window, so a
    load that hangs ends the step rather than racing a second one for the
    client's cache. A catalog under MIN_COLLECTIONS counts as a failed load.
    Returns the catalog (None once the window is spent) and the step's
    outcome: whether it loaded, after how many loads and seconds, and the last
    error.
    """
    import dynamical_catalog  # noqa: PLC0415

    log = _logger()
    started = time.monotonic()
    # A warm container keeps dynamical_catalog's module-level catalog cache;
    # each run must fetch catalog.json afresh or it checks a stale listing.
    dynamical_catalog.clear_cache()
    attempts = 0
    error: BaseException | None = None
    while window_end - time.monotonic() >= _CATALOG_MIN_ATTEMPT_SECONDS:
        attempts += 1
        try:
            catalog = _run_with_deadline(
                dynamical_catalog.load_catalog,
                window_end - time.monotonic(),
                "loading the catalog",
            )
        except TimeoutError as timeout:
            # Ours, or one the client raised inside its own load: either way
            # this load is over and the window with it if it was ours.
            error = timeout
            if time.monotonic() >= window_end:
                break
        except Exception as failure:  # noqa: BLE001
            error = failure
        else:
            if len(catalog) >= MIN_COLLECTIONS:
                return catalog, {
                    "loaded": True,
                    "attempts": attempts,
                    "seconds": round(time.monotonic() - started, 1),
                    "error": None,
                }
            error = RuntimeError(
                f"catalog returned {len(catalog)} collections, "
                f"expected >= {MIN_COLLECTIONS}"
            )
            # The client cached that short catalog; the next load must fetch.
            dynamical_catalog.clear_cache()
        log.warning("catalog load %d failed: %r", attempts, error)
        pause = _CATALOG_BACKOFF_SECONDS[
            min(attempts, len(_CATALOG_BACKOFF_SECONDS)) - 1
        ]
        time.sleep(max(0.0, min(pause, window_end - time.monotonic())))
    return None, {
        "loaded": False,
        "attempts": attempts,
        "seconds": round(time.monotonic() - started, 1),
        "error": repr(error)[:500] if error is not None else "no time to load",
    }


def _attempt(collection_id: str, seconds: float) -> tuple[str, str]:
    """One bounded read of a collection: passed, error, or deadline.

    `error` is a read that returned an exception, an observation that the
    store could not be read; `deadline` is the canary no longer waiting, which
    says only that the read was slow. Its daemon thread is abandoned.
    """
    outcome: list[tuple[str, str]] = []

    def target() -> None:
        try:
            outcome.append(
                ("passed", f"read in {_check_collection(collection_id):.1f}s")
            )
        except Exception as error:  # noqa: BLE001
            outcome.append(("error", repr(error)[:500]))

    thread = threading.Thread(
        target=target, name=f"read-canary read {collection_id}", daemon=True
    )
    thread.start()
    thread.join(max(0.0, seconds))
    if not outcome:
        return "deadline", f"no result within {seconds:.0f}s"
    return outcome[0]


def _cell(attempts: list[tuple[str, str]]) -> str:
    """A collection's result in one region from its reads there.

    Passed on any passed read; failed only on _READ_ATTEMPTS reads that each
    returned an error; otherwise not verified (slow, never read, or no time
    for its second read).
    """
    if any(result == "passed" for result, _detail in attempts):
        return "passed"
    if len(attempts) >= _READ_ATTEMPTS and all(
        result == "error" for result, _detail in attempts
    ):
        return "failed"
    return "not_verified"


def _read_twice(
    collection_ids: list[str], *, end: float
) -> dict[str, list[tuple[str, str]]]:
    """Each collection's reads, up to _READ_ATTEMPTS, until the monotonic `end`.

    _READ_WORKERS threads take every first read before any second one; a read
    that did not pass is queued again _READ_RETRY_PAUSE_SECONDS later. Each
    read is bounded by _READ_ATTEMPT_SECONDS or what is left before `end`, and
    none starts after it. Reads still going at `end` are left out.
    """
    lock = threading.Condition()
    first = list(reversed(collection_ids))
    retries: list[tuple[float, str]] = []
    reads: dict[str, list[tuple[str, str]]] = {cid: [] for cid in collection_ids}

    def take() -> str | None:
        with lock:
            while True:
                now = time.monotonic()
                if now >= end:
                    return None
                if first:
                    return first.pop()
                ready = [entry for entry in retries if entry[0] <= now]
                if ready:
                    entry = min(ready)
                    retries.remove(entry)
                    return entry[1]
                if not retries:
                    return None
                lock.wait(min(*(at for at, _cid in retries), end) - now)

    def work() -> None:
        while (collection_id := take()) is not None:
            result = _attempt(
                collection_id, min(_READ_ATTEMPT_SECONDS, end - time.monotonic())
            )
            with lock:
                if time.monotonic() > end:
                    return
                reads[collection_id].append(result)
                if result[0] != "passed" and len(reads[collection_id]) < _READ_ATTEMPTS:
                    retries.append(
                        (time.monotonic() + _READ_RETRY_PAUSE_SECONDS, collection_id)
                    )
                    lock.notify_all()

    workers = [
        threading.Thread(target=work, name=f"read-canary region {index}", daemon=True)
        for index in range(min(_READ_WORKERS, len(collection_ids)))
    ]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(max(0.0, end - time.monotonic()))
    with lock:
        return {cid: list(attempts) for cid, attempts in reads.items()}


def _run_region(region: str, return_by: float) -> dict[str, Any]:
    """The canary in full from this container, to return by wall-clock `return_by`.

    Loads its own catalog and reads every collection in it with
    _read_twice. Returns plain data for the scheduled run to judge; it sends
    no telemetry of its own.
    """
    import os  # noqa: PLC0415

    log = _logger()
    placed = os.environ.get("MODAL_REGION", "unknown")
    # Monotonic from here on; `return_by` came from another container's clock.
    end = time.monotonic() + (return_by - _REGION_RETURN_MARGIN_SECONDS - time.time())
    result: dict[str, Any] = {"region": region, "placed": placed}
    start_by = return_by - (_RETURN_BY_SECONDS - _REGION_START_BY_SECONDS)
    if time.time() > start_by:
        log.warning("re-run in %s (%s) started too late to run", region, placed)
        return {**result, "status": "late_start"}
    log.info("re-running the canary in %s (%s)", region, placed)
    catalog, outcome = _load_catalog(time.monotonic() + _CATALOG_WINDOW_SECONDS)
    result.update(status="ran", catalog=outcome, names={}, reads={})
    if catalog is None:
        log.warning("re-run in %s could not load the catalog: %s", region, outcome)
        return result
    names: dict[str, str] = {}
    for collection_id, config in catalog.items():
        name = config.get("name") if isinstance(config, dict) else None
        names[collection_id] = name if isinstance(name, str) and name else collection_id
    reads = _read_twice(sorted(catalog), end=end)
    log.info(
        "re-run in %s read %d of %d collections",
        region,
        sum(_cell(attempts) == "passed" for attempts in reads.values()),
        len(reads),
    )
    result.update(names=names, reads=reads)
    return result


_REGION_FUNCTION_OPTIONS: dict[str, Any] = {
    "image": image,
    # A backstop only: a re-run returns by the deadline it is given.
    "timeout": _TIMEOUT_SECONDS,
    # A fresh container for every re-run, and a read abandoned at a deadline
    # dies with it instead of living on in a warm one.
    "single_use_containers": True,
}


@app.function(region="us-east", **_REGION_FUNCTION_OPTIONS)
def rerun_us_east(return_by: float) -> dict[str, Any]:
    return _run_region("us-east", return_by)


@app.function(region="us-west", **_REGION_FUNCTION_OPTIONS)
def rerun_us_west(return_by: float) -> dict[str, Any]:
    return _run_region("us-west", return_by)


@app.function(region="eu-west", **_REGION_FUNCTION_OPTIONS)
def rerun_eu_west(return_by: float) -> dict[str, Any]:
    return _run_region("eu-west", return_by)


# One function per region, so each re-run's placement is fixed at deploy time.
_REGION_FUNCTIONS: dict[str, Any] = {
    "us-east": rerun_us_east,
    "us-west": rerun_us_west,
    "eu-west": rerun_eu_west,
}


def _unobserved(region: str, why: str) -> dict[str, Any]:
    return {"id": region, "status": _UNOBSERVED, "why": why}


def _judge_region(region: str, result: object) -> dict[str, Any]:
    """A re-run's result checked and reduced, or unobserved if it is not one.

    The judged entry keeps the region's catalog outcome and, per collection,
    its cell and reads. Anything that does not have exactly the shape
    _run_region returns is `invalid_result`, never a failure of the reads.
    """
    if not isinstance(result, dict) or result.get("region") != region:
        return _unobserved(region, "invalid_result")
    if result.get("status") == "late_start":
        return {
            **_unobserved(region, "late_start"),
            "placed": str(result.get("placed")),
        }
    catalog = result.get("catalog")
    names = result.get("names")
    reads = result.get("reads")
    if (
        result.get("status") != "ran"
        or not isinstance(catalog, dict)
        or not isinstance(catalog.get("loaded"), bool)
        or not isinstance(names, dict)
        or not isinstance(reads, dict)
        or set(names) != set(reads)
        or (catalog["loaded"] and len(names) < MIN_COLLECTIONS)
        or (not catalog["loaded"] and names)
        or not all(
            isinstance(cid, str) and isinstance(name, str)
            for cid, name in names.items()
        )
        or not all(
            isinstance(attempts, list)
            and len(attempts) <= _READ_ATTEMPTS
            and all(
                isinstance(attempt, list | tuple)
                and len(attempt) == 2
                and attempt[0] in {"passed", "error", "deadline"}
                and isinstance(attempt[1], str)
                for attempt in attempts
            )
            for attempts in reads.values()
        )
    ):
        return _unobserved(region, "invalid_result")
    return {
        "id": region,
        "placed": str(result.get("placed")),
        "catalog": catalog,
        "names": names,
        "cells": {
            cid: _cell([tuple(attempt) for attempt in attempts])
            for cid, attempts in reads.items()
        },
        "reads": reads,
    }


def _cancel(call: modal.FunctionCall) -> None:
    """Cancel a re-run and terminate its container, best effort."""
    log = _logger()
    try:
        call.cancel(terminate_containers=True)
    except Exception:
        log.exception("cancelling a re-run failed")


def _spawn(
    function: modal.Function, return_by: float, seconds: float, region: str
) -> modal.FunctionCall:
    """`function.spawn(return_by)`, or TimeoutError once `seconds` pass.

    A spawn that completes after the run gave up on it is cancelled at once:
    nothing would collect it, and its container would run on unwatched.
    """
    lock = threading.Lock()
    outcome: list[modal.FunctionCall | BaseException] = []
    gave_up = False

    def target() -> None:
        try:
            call = function.spawn(return_by)
        except Exception as error:  # noqa: BLE001
            with lock:
                outcome.append(error)
            return
        with lock:
            late = gave_up
            if not late:
                outcome.append(call)
        if late:
            _cancel(call)

    thread = threading.Thread(
        target=target, name=f"read-canary spawn {region}", daemon=True
    )
    thread.start()
    thread.join(max(0.0, seconds))
    with lock:
        if not outcome:
            gave_up = True
            raise TimeoutError(
                f"starting the re-run in {region} did not finish within {seconds:.0f}s"
            )
        value = outcome[0]
    if isinstance(value, BaseException):
        raise value
    return value


def _rerun_regions(run_started: float) -> list[dict[str, Any]]:
    """Every region's judged re-run, in _REGIONS order.

    The re-runs start together and are waited on together, so one that hangs
    cannot cost another its result. Every call not known to have returned by
    the run's _COLLECT_BY_SECONDS, including one whose wait failed, is
    cancelled and its container terminated.
    """
    log = _logger()
    return_by = time.time() + (run_started + _RETURN_BY_SECONDS - time.monotonic())
    collect_by = run_started + _COLLECT_BY_SECONDS
    lock = threading.Lock()
    judged: dict[str, dict[str, Any]] = {}
    calls: dict[str, modal.FunctionCall] = {}
    # Calls known to have finished; any other is cancelled, whatever was judged.
    returned: set[str] = set()
    closed = False

    def settle(region: str, entry: dict[str, Any]) -> None:
        with lock:
            if not closed:
                judged[region] = entry

    def rerun(region: str) -> None:
        spawn_left = run_started + _SPAWN_BY_SECONDS - time.monotonic()
        if spawn_left <= 0:
            settle(region, _unobserved(region, "not_started"))
            return
        function = _REGION_FUNCTIONS[region]
        try:
            call = _spawn(function, return_by, min(_SPAWN_SECONDS, spawn_left), region)
        except Exception as error:  # noqa: BLE001
            log.warning("re-run in %s did not start: %r", region, error)
            settle(region, _unobserved(region, "not_started"))
            return
        with lock:
            calls[region] = call
            late = closed
        if late:
            # Started after the run stopped waiting: nothing will collect it.
            _cancel(call)
            return
        wait = collect_by - time.monotonic()
        try:
            result = _run_with_deadline(
                lambda: call.get(timeout=max(0.0, wait)),
                wait,
                f"the re-run in {region}",
            )
        except Exception as error:  # noqa: BLE001
            log.warning("re-run in %s returned no result: %r", region, error)
            settle(region, _unobserved(region, "no_result"))
            return
        with lock:
            returned.add(region)
        settle(region, _judge_region(region, result))

    threads = [
        threading.Thread(
            target=rerun, args=(region,), name=f"read-canary {region}", daemon=True
        )
        for region in _REGIONS
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(max(0.0, collect_by - time.monotonic()))
    with lock:
        closed = True
        frozen = dict(judged)
        outstanding = [call for region, call in calls.items() if region not in returned]

    cancels = [
        threading.Thread(
            target=_cancel, args=(call,), name="read-canary cancel", daemon=True
        )
        for call in outstanding
    ]
    for thread in cancels:
        thread.start()
    cancel_by = time.monotonic() + _CANCEL_SECONDS
    for thread in cancels:
        thread.join(max(0.0, cancel_by - time.monotonic()))
    return [frozen.get(region, _unobserved(region, "no_result")) for region in _REGIONS]


def _union(regions: list[dict[str, Any]]) -> dict[str, str]:
    """Every collection some region's catalog listed, with a name for it."""
    union: dict[str, str] = {}
    for entry in regions:
        for collection_id, name in sorted(entry.get("names", {}).items()):
            union.setdefault(collection_id, name)
    return dict(sorted(union.items()))


def _region_status(entry: dict[str, Any], union: dict[str, str]) -> str:
    """Pass only when the region read every collection any region listed."""
    if entry.get("status") == _UNOBSERVED:
        return _UNOBSERVED
    if not entry["catalog"]["loaded"]:
        return _FAIL
    cells = entry["cells"]
    return _PASS if all(cells.get(cid) == "passed" for cid in union) else _FAIL


def regional_verdict(statuses: list[str]) -> str:
    """ok, degraded, down, or gap from the regions' statuses.

    The one mapping from regions to a verdict; dynamical.org-data's status
    publisher recomputes it from the report with the same table.
    """
    passing = statuses.count(_PASS)
    failing = statuses.count(_FAIL)
    unobserved = statuses.count(_UNOBSERVED)
    if not failing:
        return "gap" if unobserved else "ok"
    if passing:
        return "degraded"
    return _UNOBSERVED_WITH_ONLY_FAILURES if unobserved else "down"


def _entry(collection_id: str, union: dict[str, str]) -> dict[str, str]:
    return {"id": collection_id, "name": union[collection_id]}


def _read_report(
    run: str, environment: str, regions: list[dict[str, Any]], verdict: str
) -> dict[str, Any]:
    """The run's report (v2): each region's result and a dataset projection.

    Per region: unobserved and why, or its catalog outcome and which
    collections passed, failed, or could not be verified there. A collection
    some region listed but this one did not is not verified here. The top
    level is the v1 shape, projected across all three regions: passed or
    failed only where every region read or failed it, so a run never claims
    every collection failed from failures spread over regions.
    """
    union = _union(regions)
    entries: list[dict[str, Any]] = []
    cells_by_region: list[dict[str, str] | None] = []
    for region in regions:
        status = _region_status(region, union)
        if status == _UNOBSERVED:
            entries.append(
                {"id": region["id"], "status": _UNOBSERVED, "why": region["why"]}
            )
            cells_by_region.append(None)
            continue
        if not region["catalog"]["loaded"]:
            entries.append(
                {
                    "id": region["id"],
                    "status": _FAIL,
                    "catalog": "failed",
                    "passed": 0,
                    "failed": [],
                    "not_verified": [],
                }
            )
            cells_by_region.append(None)
            continue
        cells = {cid: region["cells"].get(cid, "not_verified") for cid in union}
        entries.append(
            {
                "id": region["id"],
                "status": status,
                "catalog": "loaded",
                "passed": sum(cell == "passed" for cell in cells.values()),
                "failed": [
                    _entry(cid, union)
                    for cid, cell in cells.items()
                    if cell == "failed"
                ],
                "not_verified": [
                    _entry(cid, union)
                    for cid, cell in cells.items()
                    if cell == "not_verified"
                ],
            }
        )
        cells_by_region.append(cells)
    passed = 0
    failed: list[dict[str, str]] = []
    unverified: list[dict[str, str]] = []
    for collection_id in union:
        cells_here = [
            cells.get(collection_id) if cells else None for cells in cells_by_region
        ]
        if all(cell == "passed" for cell in cells_here):
            passed += 1
        elif all(cell == "failed" for cell in cells_here):
            failed.append(_entry(collection_id, union))
        else:
            unverified.append(_entry(collection_id, union))
    return {
        "v": _REPORT_VERSION,
        "run": run,
        "environment": environment,
        "verdict": verdict,
        "regions": entries,
        "selected": len(union),
        "passed": passed,
        "failed": failed,
        "unverified": unverified,
    }


def _region_summary(regions: list[dict[str, Any]]) -> dict[str, Any]:
    """What each region found, for logs and Sentry contexts."""
    union = _union(regions)
    summary: dict[str, Any] = {}
    for region in regions:
        status = _region_status(region, union)
        if status == _UNOBSERVED:
            summary[region["id"]] = {"status": status, "why": region["why"]}
            continue
        summary[region["id"]] = {
            "status": status,
            "placed": region["placed"],
            "catalog": region["catalog"],
            "not_passed": {
                cid: region["reads"].get(cid, "absent from this region's catalog")
                for cid in union
                if region["catalog"]["loaded"] and region["cells"].get(cid) != "passed"
            },
        }
    return summary


def _capture_failure(
    error: BaseException,
    event_id: str,
    report: Callable[[], dict[str, Any]] | None,
    detail: dict[str, Any] | None = None,
) -> None:
    """Send the run's error event under `event_id`, with its report if any.

    `detail` goes in a `read_canary` context: what the scheduled run and each
    region found, for whoever reads the event. Best effort: if the event or
    its report cannot be built or sent, the error goes out as a plain
    capture_exception, as it did before reports existed.
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
        if detail is not None:
            event.setdefault("contexts", {})["read_canary"] = detail
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
    secrets=[modal.Secret.from_name("sentry-read-canary")],
    timeout=_TIMEOUT_SECONDS,
    region=_REGION,
    # A read abandoned when the sweep stops dies with its container instead of
    # living on in a warm one beside the next run.
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

    # The reader first, as ever: an install that cannot import it fails here,
    # before any check-in.
    import dynamical_catalog  # noqa: F401, PLC0415
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

    # Set once the re-runs have a failure to report.
    report: Callable[[], dict[str, Any]] | None = None
    detail: dict[str, Any] | None = None
    coverage: Literal["ok", "error"] = "ok"
    try:
        catalog, catalog_outcome = _load_catalog(started + _CATALOG_WINDOW_SECONDS)
        durations: dict[str, float] = {}
        failures: dict[str, BaseException] = {}
        unattempted: list[str] = []
        if catalog is not None:
            durations, failures, unattempted = _read_all(
                sorted(catalog), deadline=started + _SWEEP_DEADLINE_SECONDS
            )
        collections_read = len(durations)
        if catalog is None or failures or unattempted:
            scheduled = {
                "region": os.environ.get("MODAL_REGION", "unknown"),
                "catalog": catalog_outcome,
                "failed": {cid: repr(error)[:500] for cid, error in failures.items()},
                "unread": unattempted,
            }
            log.warning(
                "scheduled run failed after %.1fs (%s); re-running in %s",
                time.monotonic() - started,
                "catalog not loaded"
                if catalog is None
                else f"{len(failures)} failed, {len(unattempted)} unread",
                ", ".join(_REGIONS),
            )
            regions = _rerun_regions(started)
            summary = _region_summary(regions)
            detail = {"scheduled": scheduled, "regions": summary}
            union = _union(regions)
            statuses = [_region_status(region, union) for region in regions]
            verdict = regional_verdict(statuses)
            log.info(
                "re-runs: %s; verdict %s",
                ", ".join(f"{r} {s}" for r, s in zip(_REGIONS, statuses, strict=True)),
                verdict,
            )
            if verdict == "ok":
                # Every region read everything: the run passes, and this
                # keeps the scheduled failure on record.
                collections_read = len(union)
                sentry_sdk.capture_message(
                    "read canary scheduled run failed; every region re-ran clean",
                    level="warning",
                    contexts={"read_canary": detail},
                )
            else:
                # Built only when the event is sent, so that a fault building
                # it cannot change what this run raises.
                report = functools.partial(
                    _read_report, check_in_id, environment, regions, verdict
                )
                if verdict == "gap":
                    coverage = "error"
                raise RuntimeError(
                    f"read canary {verdict}: "
                    + "; ".join(
                        f"{r} {s}" for r, s in zip(_REGIONS, statuses, strict=True)
                    )
                )
    except Exception as error:
        # Anything that goes wrong after the in_progress check-in closes it as
        # `error` rather than leaving Sentry to declare a hang at max_runtime.
        # Evidence first: the log line must not depend on the check-in or the
        # flush getting through.
        log.error(
            "read canary failed after %.1fs; queueing error check-in %s%s: %s",
            time.monotonic() - started,
            check_in_id,
            f" with coverage marker {coverage_id}" if coverage == "error" else "",
            error,
        )
        _capture_failure(
            error, uuid.uuid5(_REPORT_NAMESPACE, check_in_id).hex, report, detail
        )
        _finish("error", coverage)
        raise

    # After an ok re-run the scheduled sweep's times are partial.
    slowest_id, slowest = max(
        durations.items(), key=lambda item: item[1], default=("none", 0.0)
    )
    log.info(
        "read canary ok: %d collections read in %.1fs (slowest %s %.1fs); "
        "queueing ok check-in %s",
        collections_read,
        time.monotonic() - started,
        slowest_id,
        slowest,
        check_in_id,
    )
    # Every collection read succeeded — report liveness. Any exception above
    # skips this line, so Sentry opens an incident.
    _finish("ok")
