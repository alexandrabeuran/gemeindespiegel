from datetime import date

import pytest
from conftest import read_fixture

from importer.bfs import Canton, parse_snapshot, snapshot_url
from importer.errors import SourceError

ZURICH = Canton(bfs_number=1, abbreviation="ZH", name="Zürich")
BERN = Canton(bfs_number=2, abbreviation="BE", name="Bern / Berne")


def test_snapshot_url_uses_day_month_year() -> None:
    assert snapshot_url(date(2026, 3, 7)) == (
        "https://www.agvchapp.bfs.admin.ch/api/communes/snapshot?date=07-03-2026&useBfsCode=true"
    )


def test_parses_only_municipalities_keyed_by_bfs_number() -> None:
    municipalities = parse_snapshot(read_fixture("bfs-snapshot.csv"))

    assert sorted(municipalities) == [1, 141, 219, 261, 499, 6158]
    assert municipalities[1].name == "Aeugst am Albis"
    assert municipalities[261].name == "Zürich"


def test_finds_the_canton_through_the_district() -> None:
    municipalities = parse_snapshot(read_fixture("bfs-snapshot.csv"))

    assert municipalities[1].canton == ZURICH
    assert municipalities[261].canton == ZURICH
    assert municipalities[499].canton == BERN


def test_codes_are_looked_up_per_level() -> None:
    # Bezirk Horgen and the municipality Vionnaz share HistoricalCode 10078.
    municipalities = parse_snapshot(read_fixture("bfs-snapshot.csv"))

    assert municipalities[141].canton == ZURICH
    assert municipalities[6158].canton.abbreviation == "VS"


def test_stops_when_a_municipality_has_no_district() -> None:
    with pytest.raises(SourceError, match=r"municipality 1 \(Aeugst am Albis\) has no district"):
        parse_snapshot(read_fixture("bfs-without-district.csv"))


def test_stops_when_a_required_column_is_missing() -> None:
    text = read_fixture("bfs-snapshot.csv").replace("ShortName", "Abbreviation", 1)

    with pytest.raises(SourceError, match="missing columns: ShortName"):
        parse_snapshot(text)


def test_stops_when_the_snapshot_is_empty() -> None:
    with pytest.raises(SourceError, match="missing columns"):
        parse_snapshot("")


def test_stops_when_a_district_has_no_canton() -> None:
    with pytest.raises(SourceError, match=r"district 101 \(Bezirk Affoltern\) has no canton"):
        parse_snapshot(read_fixture("bfs-without-canton.csv"))


def test_stops_on_a_duplicate_code_within_a_level() -> None:
    text = read_fixture("bfs-snapshot.csv") + "10053,999,,,2,1,Bezirk Doppelt,Doppelt,,,,\n"

    with pytest.raises(SourceError, match="duplicate HistoricalCode 10053 on level 2"):
        parse_snapshot(text)


def test_stops_on_a_duplicate_municipality_number() -> None:
    text = read_fixture("bfs-snapshot.csv") + "99999,1,,,3,10053,Doppelt,Doppelt,,,,\n"

    with pytest.raises(SourceError, match="duplicate BfsCode 1"):
        parse_snapshot(text)


def test_stops_on_an_invalid_municipality_number() -> None:
    text = read_fixture("bfs-snapshot.csv").replace("13256,1,", "13256,one,")

    with pytest.raises(SourceError, match="invalid BfsCode 'one'"):
        parse_snapshot(text)
