import json
import re

import pytest
import responses
from conftest import read_fixture

from importer import main
from importer.bfs import BFS_SNAPSHOT_URL
from importer.elcom import LINDAS_SPARQL_URL


def test_prints_the_summary(
    http_mock: responses.RequestsMock, capsys: pytest.CaptureFixture[str]
) -> None:
    http_mock.get(re.compile(re.escape(BFS_SNAPSHOT_URL)), body=read_fixture("bfs-snapshot.csv"))
    http_mock.post(LINDAS_SPARQL_URL, body=read_fixture("elcom-tariffs.json"))

    main()

    assert capsys.readouterr().out == (
        "Municipalities: 6\n  with price: 5\n  without price: 1\n  with several grid operators: 1\n"
    )


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
