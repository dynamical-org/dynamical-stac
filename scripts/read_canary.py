#!/usr/bin/env python3
"""Modal cron — hot-storage read canary for the dynamical.org catalog.

Every 10 minutes this opens every collection in the live STAC catalog from
its Icechunk store on S3 and reads a single value from each, exercising the
full icechunk -> S3 -> zarr decode path for the whole catalog, not just one
dataset. A successful read of every collection pings a Better Stack
heartbeat; any failure (or a hung read) simply skips the ping, so the
heartbeat lapses and Better Stack opens an incident.

This is the data-plane half of the 99.5% uptime SLA: proof that reads actually
resolve, not merely that catalog.json is served.

Deploy:
    modal deploy scripts/read_canary.py

Configure (the heartbeat URL comes from Better Stack; keep it out of git):
    modal secret create betterstack-read-canary \
        BETTERSTACK_HEARTBEAT_URL="https://uptime.betterstack.com/api/v1/heartbeat/XXXXXXXX"

The icechunk stores are public AWS Open Data buckets, read anonymously, so no
AWS credentials are needed. If a monitored store ever requires signed access,
attach an AWS secret to the function.
"""

from __future__ import annotations

import modal

# Still pinned to icechunk-2 rather than a released PyPI version: switching
# depends on dynamical-org/reformatters#724 (zarr/gribberish dep bump) landing
# and a new dynamical-catalog release following it. Re-check once that lands.
image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "dynamical-catalog @ git+https://github.com/dynamical-org/dynamical-catalog@icechunk-2",
    "requests>=2.32",
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
    secrets=[modal.Secret.from_name("betterstack-read-canary")],
    timeout=600,
)
def read_canary() -> None:
    import os  # noqa: PLC0415
    from concurrent.futures import ThreadPoolExecutor, as_completed  # noqa: PLC0415

    import requests  # noqa: PLC0415
    from dynamical_catalog._stac import load_catalog  # noqa: PLC0415

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

    if errors:
        raise RuntimeError(
            f"read canary failed for {len(errors)}/{len(collection_ids)} "
            "collections:\n" + "\n".join(errors)
        )

    # Every collection read succeeded — report liveness. Any exception above
    # skips this line, so the heartbeat lapses and Better Stack opens an
    # incident.
    requests.get(heartbeat_url, timeout=10).raise_for_status()
