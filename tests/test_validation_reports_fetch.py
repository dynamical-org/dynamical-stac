from __future__ import annotations

import http.client
import io
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from tests import test_validation_reports as reports

URL = "https://example.invalid/validation_summary.md"
SUMMARY = b"Report\n## Summary\nComplete.\n"


def test_fetch_uses_longer_timeout() -> None:
    with patch.object(
        reports.urllib.request, "urlopen", return_value=io.BytesIO(SUMMARY)
    ) as open_url:
        assert reports._fetch(URL) == SUMMARY.decode()

    open_url.assert_called_once()
    request = open_url.call_args.args[0]
    assert request.full_url == URL
    assert request.get_header("User-agent") == "dynamical-stac-tests"
    assert open_url.call_args.kwargs == {"timeout": 90}


@pytest.mark.parametrize(
    "error",
    [
        TimeoutError("timed out"),
        ConnectionResetError("reset"),
        urllib.error.URLError("unavailable"),
    ],
)
def test_fetch_retries_open_failure_once(error: Exception) -> None:
    with patch.object(
        reports.urllib.request, "urlopen", side_effect=[error, io.BytesIO(SUMMARY)]
    ) as open_url:
        assert reports._fetch(URL) == SUMMARY.decode()

    assert open_url.call_count == 2


@pytest.mark.parametrize(
    "error", [TimeoutError("timed out"), http.client.IncompleteRead(b"partial", 20)]
)
def test_fetch_retries_body_failure_with_a_new_response(error: Exception) -> None:
    response = MagicMock()
    response.__enter__.return_value.read.side_effect = error
    with patch.object(
        reports.urllib.request, "urlopen", side_effect=[response, io.BytesIO(SUMMARY)]
    ) as open_url:
        assert reports._fetch(URL) == SUMMARY.decode()

    response.__exit__.assert_called_once()
    assert open_url.call_count == 2


def test_fetch_propagates_second_transport_failure() -> None:
    second = TimeoutError("second failure")
    with (
        patch.object(
            reports.urllib.request,
            "urlopen",
            side_effect=[TimeoutError("first failure"), second],
        ) as open_url,
        pytest.raises(TimeoutError, match="second failure") as exc,
    ):
        reports._fetch(URL)

    assert exc.value is second
    assert open_url.call_count == 2


@pytest.mark.parametrize("status", [403, 404, 500, 503])
def test_fetch_does_not_retry_http_errors(status: int) -> None:
    error = urllib.error.HTTPError(URL, status, "HTTP failure", None, None)
    with (
        patch.object(reports.urllib.request, "urlopen", side_effect=error) as open_url,
        pytest.raises(urllib.error.HTTPError, match="HTTP failure") as exc,
    ):
        reports._fetch(URL)

    assert exc.value is error
    open_url.assert_called_once()


def test_invalid_report_content_still_fails_without_retry() -> None:
    with (
        patch.object(
            reports.urllib.request, "urlopen", return_value=io.BytesIO(b"not a report")
        ) as open_url,
        pytest.raises(AssertionError, match="missing the Summary section"),
    ):
        reports.test_validation_report_is_published(
            "example", "https://dynamical.org/catalog/example/validation/"
        )

    open_url.assert_called_once()
