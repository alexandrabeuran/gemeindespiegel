import pytest
import requests
import responses
from responses import matchers

from importer.errors import SourceError
from importer.fetch import TIMEOUT_SECONDS, fetch_text

URL = "https://example.org/data"


def test_returns_the_body_as_utf8(http_mock: responses.RequestsMock) -> None:
    http_mock.get(URL, body="Zürich".encode(), content_type="text/plain")

    assert fetch_text("BFS", "GET", URL) == "Zürich"


def test_sends_a_timeout(http_mock: responses.RequestsMock) -> None:
    # The mock only answers if the request carries the timeout.
    timeout = matchers.request_kwargs_matcher({"timeout": TIMEOUT_SECONDS})
    http_mock.get(URL, body="ok", match=[timeout])

    assert fetch_text("BFS", "GET", URL) == "ok"


def test_a_timeout_stops_the_import(http_mock: responses.RequestsMock) -> None:
    http_mock.get(URL, body=requests.Timeout("read timed out"))

    with pytest.raises(SourceError, match="BFS: request failed: read timed out"):
        fetch_text("BFS", "GET", URL)


def test_an_error_status_stops_the_import(http_mock: responses.RequestsMock) -> None:
    http_mock.post(URL, status=503)

    with pytest.raises(SourceError, match="ElCom: request failed: 503"):
        fetch_text("ElCom", "POST", URL)


def test_no_request_leaves_the_test_run() -> None:
    # Guards acceptance criterion 3: the autouse mock rejects unregistered URLs.
    with pytest.raises(SourceError, match="Connection refused"):
        fetch_text("BFS", "GET", "https://www.agvchapp.bfs.admin.ch/api/communes/snapshot")
