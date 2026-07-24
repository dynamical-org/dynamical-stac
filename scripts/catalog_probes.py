#!/usr/bin/env python3
"""Modal crons — semantic health probes for the dynamical.org catalog surface.

Two functions, each on a 10-minute schedule, replace the Better Stack "keyword"
monitors that used to assert response-body content for two public endpoints —
something Sentry Uptime (status-code only) can't do. Each performs a semantic
check and reports a Sentry cron check-in: `ok` on success, `error` (plus a
captured exception) on failure. No check-in is sent at the start of a run, so a
hang produces a missed check-in and Sentry opens an incident.

1. stac_catalog_probe: GET stac.dynamical.org/catalog.json and assert it is a
   STAC catalog with a healthy set of child (collection) links. Its monitor
   lives in the `read-canary` Sentry project (DSN env `SENTRY_DSN_READ_CANARY`).
2. mcp_probe: perform a real MCP round trip against mcp.dynamical.org/mcp
   (streamable HTTP) — `initialize` then `tools/list` — and assert the tool list
   is non-empty. Its monitor lives in the `mcp` Sentry project (DSN env
   `SENTRY_DSN_MCP`) so alerts route with that app's Slack channel.

Deploy:
    modal deploy scripts/catalog_probes.py

Configure (one secret carries both DSNs; each function reads its own):
    modal secret create sentry-catalog-probes \
        SENTRY_DSN_READ_CANARY="https://<key>@<org>.ingest.us.sentry.io/<project>" \
        SENTRY_DSN_MCP="https://<key>@<org>.ingest.us.sentry.io/<project>"

Both endpoints are public and unauthenticated, so no credentials are needed.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import modal

STAC_CATALOG_URL = "https://stac.dynamical.org/catalog.json"
MCP_URL = "https://mcp.dynamical.org/mcp"
MIN_CHILD_LINKS = 8

image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "sentry-sdk>=2.20",
    "httpx>=0.27",
    "mcp>=1.28.0",
)

app = modal.App("dynamical-catalog-probes")


def check_stac_catalog(doc: object) -> int:
    """Assert `doc` is a STAC catalog with at least MIN_CHILD_LINKS child links; return that count."""
    assert isinstance(doc, dict), (
        f"catalog.json is not a JSON object: {type(doc).__name__}"
    )
    assert doc.get("type") == "Catalog", (
        f"expected type 'Catalog', got {doc.get('type')!r}"
    )
    links = doc.get("links")
    assert isinstance(links, list), f"catalog links is not a list: {links!r}"
    assert links, "catalog has no links"
    child_count = sum(
        1 for link in links if isinstance(link, dict) and link.get("rel") == "child"
    )
    assert child_count >= MIN_CHILD_LINKS, (
        f"catalog has {child_count} child links, expected >= {MIN_CHILD_LINKS}"
    )
    return child_count


def check_mcp_tools(tool_names: Sequence[str]) -> int:
    """Assert the MCP server advertised at least one tool; return the tool count."""
    assert tool_names, "MCP tools/list returned no tools"
    return len(tool_names)


def _run_probe(monitor_slug: str, dsn_env_var: str, check: Callable[[], None]) -> None:
    import os  # noqa: PLC0415

    import sentry_sdk  # noqa: PLC0415
    import sentry_sdk.crons  # noqa: PLC0415

    # No-op when the DSN is unset (e.g. the secret isn't attached yet).
    sentry_sdk.init(
        dsn=os.environ.get(dsn_env_var),
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
        enable_logs=True,
    )
    monitor_config = {
        # Must match the `modal.Period` schedule on the functions below.
        "schedule": {"type": "interval", "value": 10, "unit": "minute"},
        "timezone": "UTC",
        "checkin_margin": 5,
        "failure_issue_threshold": 1,
        "recovery_threshold": 1,
    }
    try:
        check()
    except Exception:
        sentry_sdk.capture_exception()
        sentry_sdk.crons.capture_checkin(
            monitor_slug=monitor_slug, status="error", monitor_config=monitor_config
        )
        raise
    sentry_sdk.crons.capture_checkin(
        monitor_slug=monitor_slug, status="ok", monitor_config=monitor_config
    )


@app.function(
    image=image,
    schedule=modal.Period(minutes=10),
    secrets=[modal.Secret.from_name("sentry-catalog-probes")],
    timeout=120,
)
def stac_catalog_probe() -> None:
    def check() -> None:
        import httpx  # noqa: PLC0415

        response = httpx.get(STAC_CATALOG_URL, timeout=30, follow_redirects=True)
        response.raise_for_status()
        check_stac_catalog(response.json())

    _run_probe("stac-catalog-probe", "SENTRY_DSN_READ_CANARY", check)


@app.function(
    image=image,
    schedule=modal.Period(minutes=10),
    secrets=[modal.Secret.from_name("sentry-catalog-probes")],
    timeout=120,
)
def mcp_probe() -> None:
    def check() -> None:
        import asyncio  # noqa: PLC0415

        from mcp import ClientSession  # noqa: PLC0415
        from mcp.client.streamable_http import streamablehttp_client  # noqa: PLC0415

        async def roundtrip() -> list[str]:
            async with (
                streamablehttp_client(MCP_URL) as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                result = await session.list_tools()
                return [tool.name for tool in result.tools]

        check_mcp_tools(asyncio.run(roundtrip()))

    _run_probe("mcp-probe", "SENTRY_DSN_MCP", check)
