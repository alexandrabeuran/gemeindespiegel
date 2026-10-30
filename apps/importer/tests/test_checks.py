from dataclasses import replace
from decimal import Decimal

import pytest
from conftest import read_fixture

from importer.bfs import parse_snapshot
from importer.checks import (
    check_municipality_numbers,
    check_sums,
    check_tariffs_found,
    check_unique_pairs,
)
from importer.elcom import parse_tariffs
from importer.errors import SourceError


def test_known_municipality_numbers_pass() -> None:
    municipalities = parse_snapshot(read_fixture("bfs-snapshot.csv"))
    tariffs = parse_tariffs(read_fixture("elcom-tariffs.json"))

    check_municipality_numbers(tariffs, municipalities)


def test_an_unknown_municipality_number_stops_the_import() -> None:
    municipalities = parse_snapshot(read_fixture("bfs-snapshot.csv"))
    tariffs = parse_tariffs(read_fixture("elcom-unknown-municipality.json"))

    with pytest.raises(SourceError, match="not in the BFS snapshot: 9999"):
        check_municipality_numbers(tariffs, municipalities)


def test_a_difference_of_0_001_passes() -> None:
    tariffs = parse_tariffs(read_fixture("elcom-tariffs.json"))
    # Guards the fixture: it must keep real rows that differ by -0.001 and +0.001.
    differences = {t.total - t.sum_of_parts() for t in tariffs}
    assert {Decimal("-0.001"), Decimal("0.001")} <= differences

    check_sums(tariffs)


def test_a_difference_of_0_002_stops_the_import() -> None:
    tariffs = parse_tariffs(read_fixture("elcom-sum-difference-0.002.json"))

    with pytest.raises(SourceError, match=r"municipality 1, grid operator 486 .*differs by 0\.002"):
        check_sums(tariffs)


def test_a_difference_of_minus_0_002_stops_the_import() -> None:
    tariffs = parse_tariffs(read_fixture("elcom-sum-difference-0.002.json"))
    too_low = replace(tariffs[0], total=tariffs[0].total - Decimal("0.004"))

    with pytest.raises(SourceError, match=r"differs by 0\.002"):
        check_sums([too_low])


def test_an_empty_result_stops_the_import() -> None:
    # Every per-row check passes on zero rows, so emptiness needs its own check.
    with pytest.raises(SourceError, match="ElCom: no tariffs found"):
        check_tariffs_found([])


def test_tariffs_found_pass() -> None:
    check_tariffs_found(parse_tariffs(read_fixture("elcom-tariffs.json")))


def test_unique_pairs_pass() -> None:
    check_unique_pairs(parse_tariffs(read_fixture("elcom-tariffs.json")))


def test_a_duplicate_pair_stops_the_import() -> None:
    tariffs = parse_tariffs(read_fixture("elcom-tariffs.json"))

    with pytest.raises(SourceError, match="municipality 1, grid operator 486 appears twice"):
        check_unique_pairs([*tariffs, tariffs[0]])
