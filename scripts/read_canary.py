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
canary ran that does not depend on Sentry. On 2026-09-10 a Sentry cron
ingestion incident dropped two check-ins, the status page showed "Data
product reads" down for 25 minutes, and nothing outside Sentry could show
whether those two runs had happened at all.

This is the data-plane half of the 99.5% uptime SLA: proof that reads actually
resolve, not merely that catalog.json is served.

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

import importlib.metadata
import logging
import sys
import time

import modal

image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "dynamical-catalog>=1.0.0",
    "sentry-sdk>=2.20",
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

# sentry-sdk's default flush budget is `shutdown_timeout`, 2 seconds. When
# Sentry's ingest edge is slow (as during its 2026-09-10 US ingestion incident)
# the terminal check-in is still queued when flush gives up, Modal reclaims the
# container, and the run reads as hung or missed even though every read passed.
# 15 s matches reformatters' cron monitoring and is well inside the schedule.
_FLUSH_TIMEOUT_SECONDS = 15


def _logger() -> logging.Logger:
    """The canary's stdout logger, wired once per container.

    Modal captures stdout; python's root logger only emits WARNING and up, so
    the INFO lines need their own handler. Warm containers re-enter
    `read_canary`, hence the guard. Propagation stays on so sentry-sdk's
    `enable_logs=True` integration forwards a second copy as Sentry logs.
    """
    log = logging.getLogger("read_canary")
    log.setLevel(logging.INFO)
    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
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


def _check_collection(collection_id: str) -> float:
    """Read one value from the collection; return the wall time it took."""
    import math  # noqa: PLC0415

    import dynamical_catalog  # noqa: PLC0415

    started = time.monotonic()
    ds = dynamical_catalog.open(collection_id)
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


@app.function(
    image=image,
    schedule=modal.Period(minutes=10),
    secrets=[modal.Secret.from_name("sentry-read-canary")],
    timeout=_TIMEOUT_SECONDS,
)
def read_canary() -> None:
    import os  # noqa: PLC0415
    from concurrent.futures import ThreadPoolExecutor, as_completed  # noqa: PLC0415
    from typing import Literal  # noqa: PLC0415

    import sentry_sdk  # noqa: PLC0415
    import sentry_sdk.crons  # noqa: PLC0415
    from dynamical_catalog._stac import load_catalog  # noqa: PLC0415

    # The start line goes out before anything that can fail, so a run that
    # hangs or is killed still leaves a trace in Modal's logs of having begun.
    log = _logger()
    started = time.monotonic()
    log.info("read canary started; %s", _runtime_versions())

    # No-op when SENTRY_DSN is unset (e.g. the secret isn't attached yet).
    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
        enable_logs=True,
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
    check_in_id = sentry_sdk.crons.capture_checkin(
        monitor_slug="read-canary", status="in_progress", monitor_config=monitor_config
    )
    log.info("in_progress check-in %s sent", check_in_id)

    def _finish(status: Literal["ok", "error"]) -> None:
        sentry_sdk.crons.capture_checkin(
            monitor_slug="read-canary",
            check_in_id=check_in_id,
            status=status,
            monitor_config=monitor_config,
        )
        # Modal may reclaim the container the moment this function returns; an
        # unflushed terminal check-in is lost and reads as a hung run.
        sentry_sdk.flush(timeout=_FLUSH_TIMEOUT_SECONDS)

    def _fail(error: Exception) -> None:
        # Evidence first: the log line must not depend on the check-in or the
        # flush getting through.
        log.error(
            "read canary failed after %.1fs; sending error check-in %s: %s",
            time.monotonic() - started,
            check_in_id,
            error,
        )
        sentry_sdk.capture_exception(error)
        _finish("error")

    try:
        collection_ids = sorted(load_catalog())
    except Exception as e:
        # A catalog that cannot be loaded is a failed run, not a hung one: close
        # the check-in as `error` instead of leaving it to time out.
        _fail(e)
        raise

    if len(collection_ids) < MIN_COLLECTIONS:
        error = RuntimeError(
            f"catalog returned {len(collection_ids)} collections, "
            f"expected >= {MIN_COLLECTIONS}"
        )
        _fail(error)
        raise error

    errors: list[str] = []
    durations: dict[str, float] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(_check_collection, cid): cid for cid in collection_ids}
        for future in as_completed(futures):
            collection_id = futures[future]
            try:
                durations[collection_id] = future.result()
            except Exception as e:  # noqa: BLE001
                errors.append(f"{collection_id}: {e!r}")

    if errors:
        error = RuntimeError(
            f"read canary failed for {len(errors)}/{len(collection_ids)} "
            "collections:\n" + "\n".join(errors)
        )
        _fail(error)
        raise error

    slowest_id, slowest = max(durations.items(), key=lambda item: item[1])
    log.info(
        "read canary ok: %d/%d collections read in %.1fs (slowest %s %.1fs); "
        "sending ok check-in %s",
        len(durations),
        len(collection_ids),
        time.monotonic() - started,
        slowest_id,
        slowest,
        check_in_id,
    )
    # Every collection read succeeded — report liveness. Any exception above
    # skips this line, so Sentry opens an incident.
    _finish("ok")
