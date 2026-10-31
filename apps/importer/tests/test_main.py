import json
import re
import socket
from collections.abc import Iterator

import pytest
import responses
from conftest import read_fixture

from importer import main
from importer.bfs import BFS_SNAPSHOT_URL
from importer.elcom import LINDAS_SPARQL_URL


def _free_port() -> int:
    # Bound and released again, so nothing listens there while the test runs.
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port: int = sock.getsockname()[1]
        return port


@pytest.fixture(autouse=True)
def database_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # Points at a closed port: these tests must fail before or without a database.
    monkeypatch.setenv("POSTGRES_HOST", "127.0.0.1")
    monkeypatch.setenv("POSTGRES_PORT", str(_free_port()))
    monkeypatch.setenv("POSTGRES_USER", "tester")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")
    monkeypatch.setenv("POSTGRES_DB", "testdb")
    yield


def test_a_missing_password_stops_before_fetching(
    http_mock: responses.RequestsMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("POSTGRES_PASSWORD")

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == (
        "importer: Missing environment variable POSTGRES_PASSWORD, see .env.example"
    )
    assert len(http_mock.calls) == 0


def test_an_unreachable_database_exits_non_zero(http_mock: responses.RequestsMock) -> None:
    http_mock.get(re.compile(re.escape(BFS_SNAPSHOT_URL)), body=read_fixture("bfs-snapshot.csv"))
    http_mock.post(LINDAS_SPARQL_URL, body=read_fixture("elcom-tariffs.json"))

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert isinstance(exit_info.value.code, str)
    assert exit_info.value.code.startswith("importer: database: ")


def test_exits_non_zero_with_the_reason(http_mock: responses.RequestsMock) -> None:
    http_mock.get(re.compile(re.escape(BFS_SNAPSHOT_URL)), body=read_fixture("bfs-snapshot.csv"))
    http_mock.post(LINDAS_SPARQL_URL, body=read_fixture("elcom-unknown-municipality.json"))

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == (
        "importer: ElCom: municipality numbers not in the BFS snapshot: 9999"
    )


def test_an_empty_elcom_result_exits_non_zero(http_mock: responses.RequestsMock) -> None:
    http_mock.get(re.compile(re.escape(BFS_SNAPSHOT_URL)), body=read_fixture("bfs-snapshot.csv"))
    http_mock.post(LINDAS_SPARQL_URL, body='{"head": {"vars": []}, "results": {"bindings": []}}')

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert isinstance(exit_info.value.code, str)
    assert "ElCom: no tariffs found" in exit_info.value.code


def test_a_duplicate_elcom_row_exits_non_zero(http_mock: responses.RequestsMock) -> None:
    document = json.loads(read_fixture("elcom-tariffs.json"))
    document["results"]["bindings"].append(document["results"]["bindings"][0])
    http_mock.get(re.compile(re.escape(BFS_SNAPSHOT_URL)), body=read_fixture("bfs-snapshot.csv"))
    http_mock.post(LINDAS_SPARQL_URL, body=json.dumps(document))

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert isinstance(exit_info.value.code, str)
    assert "municipality 1, grid operator 486 appears twice" in exit_info.value.code
