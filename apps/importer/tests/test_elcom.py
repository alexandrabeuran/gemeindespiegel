import json
from decimal import Decimal

import pytest
from conftest import read_fixture

from importer.elcom import MUNICIPALITY_PREFIX, GridOperator, Tariff, parse_tariffs
from importer.errors import SourceError


def test_parses_every_row_with_exact_decimals() -> None:
    tariffs = parse_tariffs(read_fixture("elcom-tariffs.json"))

    assert len(tariffs) == 7
    assert tariffs[0] == Tariff(
        municipality_bfs_number=1,
        operator=GridOperator(elcom_id=486, name="Elektrizitätswerke des Kantons Zürich (EKZ)"),
        total=Decimal("23.872"),
        energy=Decimal("11.859"),
        grid_usage=Decimal("7.900"),
        levies=Decimal("0.160"),
        grid_surcharge=Decimal("2.300"),
        metering=Decimal("1.653"),
    )


def test_keeps_one_row_per_operator() -> None:
    tariffs = parse_tariffs(read_fixture("elcom-tariffs.json"))

    elsau = [
        tariff.operator.elcom_id for tariff in tariffs if tariff.municipality_bfs_number == 219
    ]
    assert sorted(elsau) == [457, 486, 789]


def test_stops_when_the_response_is_not_json() -> None:
    with pytest.raises(SourceError, match="ElCom: response is not SPARQL JSON"):
        parse_tariffs("<html>Service unavailable</html>")


def test_stops_when_the_results_are_missing() -> None:
    with pytest.raises(SourceError, match="ElCom: response is not SPARQL JSON"):
        parse_tariffs(json.dumps({"head": {"vars": []}}))


def test_stops_when_a_price_is_undefined() -> None:
    # Older tariff years mark missing values as cube:Undefined with an empty literal.
    document = json.loads(read_fixture("elcom-tariffs.json"))
    document["results"]["bindings"][0]["meteringrate"]["value"] = ""

    with pytest.raises(SourceError, match="ElCom: row 1: invalid meteringrate"):
        parse_tariffs(json.dumps(document))


def test_stops_when_a_uri_is_not_a_municipality() -> None:
    document = json.loads(read_fixture("elcom-tariffs.json"))
    document["results"]["bindings"][0]["municipality"]["value"] = "https://example.org/x/1"

    with pytest.raises(SourceError, match="ElCom: row 1: invalid municipality"):
        parse_tariffs(json.dumps(document))


def test_stops_when_an_id_has_non_ascii_digits() -> None:
    # "²".isdigit() is True, but int("²") fails.
    document = json.loads(read_fixture("elcom-tariffs.json"))
    document["results"]["bindings"][0]["municipality"]["value"] = MUNICIPALITY_PREFIX + "²"

    with pytest.raises(SourceError, match="ElCom: row 1: invalid municipality"):
        parse_tariffs(json.dumps(document))
