from collections.abc import Iterator
from pathlib import Path

import pytest
import responses

FIXTURES = Path(__file__).parent / "fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def http_mock() -> Iterator[responses.RequestsMock]:
    # Every test runs inside the mock, so a request to an unregistered URL fails
    # instead of silently reaching the real BFS or LINDAS servers.
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        yield mock
