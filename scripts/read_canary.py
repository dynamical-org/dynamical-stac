#!/usr/bin/env python3
"""Modal cron — hot-storage read canary for the dynamical.org catalog.

Every 10 minutes this opens every collection in the live STAC catalog from
its Icechunk store on S3 and reads a single value from each, exercising the
full icechunk -> S3 -> zarr decode path for the whole catalog, not just one
dataset. A successful read of every collection pings a Better Stack
heartbeat and sends an `ok` Sentry cron check-in; any failure (or a hung
read) simply skips both, so the heartbeat lapses and the Sentry monitor
records a missed check-in, opening an incident in each system.

This is the data-plane half of the 99.5% uptime SLA: proof that reads actually
resolve, not merely that catalog.json is served.

Deploy:
    modal deploy scripts/read_canary.py

Configure (the heartbeat URL comes from Better Stack; keep it out of git):
    modal secret create betterstack-read-canary \
        BETTERSTACK_HEARTBEAT_URL="https://uptime.betterstack.com/api/v1/heartbeat/XXXXXXXX"

    modal secret create sentry-read-canary \
        SENTRY_DSN="https://<key>@<org>.ingest.us.sentry.io/<project>"

The icechunk stores are public AWS Open Data buckets, read anonymously, so no
AWS credentials are needed. If a monitored store ever requires signed access,
attach an AWS secret to the function.
"""

from __future__ import annotations

import modal

image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "dynamical-catalog>=0.7.0",
    "requests>=2.32",
    "sentry-sdk>=2.20",
)

app = modal.App("dynamical-read-canary")


def _check_collection(collection_id: str) -> None:
    import math  # noqa: PLC0415

    import dynamical_catalog  # noqa: PLC0415

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


@app.function(
    image=image,
    schedule=modal.Period(minutes=10),
    secrets=[
        modal.Secret.from_name("betterstack-read-canary"),
        modal.Secret.from_name("sentry-read-canary"),
    ],
    timeout=600,
)
def read_canary() -> None:
    import os  # noqa: PLC0415
    from concurrent.futures import ThreadPoolExecutor, as_completed  # noqa: PLC0415

    import requests  # noqa: PLC0415
    import sentry_sdk  # noqa: PLC0415
    import sentry_sdk.crons  # noqa: PLC0415
    from dynamical_catalog._stac import load_catalog  # noqa: PLC0415

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
        "failure_issue_threshold": 1,
        "recovery_threshold": 1,
    }

    heartbeat_url = os.environ["BETTERSTACK_HEARTBEAT_URL"]
    collection_ids = sorted(load_catalog())

    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(_check_collection, cid): cid for cid in collection_ids}
        for future in as_completed(futures):
            collection_id = futures[future]
            try:
                future.result()
            except Exception as e:  # noqa: BLE001
                errors.append(f"{collection_id}: {e!r}")

    # No check-in is sent at the start of the run (unlike a typical Sentry
    # cron), so a hang produces a missed check-in instead of a stuck
    # `in_progress` one — the same lapsed-heartbeat semantics as Better Stack.
    if errors:
        error = RuntimeError(
            f"read canary failed for {len(errors)}/{len(collection_ids)} "
            "collections:\n" + "\n".join(errors)
        )
        sentry_sdk.capture_exception(error)
        sentry_sdk.crons.capture_checkin(
            monitor_slug="read-canary", status="error", monitor_config=monitor_config
        )
        raise error

    # Every collection read succeeded — report liveness. Any exception above
    # skips these lines, so the heartbeat lapses and both Better Stack and
    # Sentry open an incident.
    requests.get(heartbeat_url, timeout=10).raise_for_status()
    sentry_sdk.crons.capture_checkin(
        monitor_slug="read-canary", status="ok", monitor_config=monitor_config
    )
