import csv
import io
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlencode

from importer.errors import SourceError
from importer.fetch import fetch_text

BFS_SNAPSHOT_URL = "https://www.agvchapp.bfs.admin.ch/api/communes/snapshot"
REQUIRED_COLUMNS = ("HistoricalCode", "BfsCode", "Level", "Parent", "Name", "ShortName")
CANTON, DISTRICT, MUNICIPALITY = "1", "2", "3"


@dataclass(frozen=True)
class Canton:
    bfs_number: int
    abbreviation: str
    name: str


@dataclass(frozen=True)
class Municipality:
    bfs_number: int
    name: str
    canton: Canton


def snapshot_url(day: date) -> str:
    # The BFS API expects DD-MM-YYYY, not ISO 8601, and useBfsCode=true so that
    # ids are the official BFS numbers that ElCom also uses.
    query = urlencode({"date": day.strftime("%d-%m-%Y"), "useBfsCode": "true"})
    return f"{BFS_SNAPSHOT_URL}?{query}"


def fetch_snapshot(day: date) -> str:
    return fetch_text("BFS", "GET", snapshot_url(day))


def parse_snapshot(text: str) -> dict[int, Municipality]:
    # csv.reader instead of DictReader: its rows are list[str], DictReader's
    # contain Any, which would slip past mypy.
    reader = csv.reader(io.StringIO(text))
    header = next(reader, [])
    missing = [column for column in REQUIRED_COLUMNS if column not in header]
    if missing:
        raise SourceError(f"BFS: missing columns: {', '.join(missing)}")

    # Parent refers to the HistoricalCode of the level above. Codes are only
    # unique within a level (district Horgen and municipality Vionnaz are both
    # 10078), so every level gets its own lookup table.
    levels: dict[str, dict[str, dict[str, str]]] = {CANTON: {}, DISTRICT: {}, MUNICIPALITY: {}}
    for values in reader:
        # Short rows are padded so that every column has a value.
        row = dict(zip(header, values + [""] * (len(header) - len(values)), strict=False))
        level = levels.get(row["Level"])
        if level is None:
            continue
        code = row["HistoricalCode"]
        if code in level:
            raise SourceError(f"BFS: duplicate HistoricalCode {code} on level {row['Level']}")
        level[code] = row

    cantons = {
        code: Canton(_number(row), row["ShortName"], row["Name"])
        for code, row in levels[CANTON].items()
    }
    municipalities: dict[int, Municipality] = {}
    for row in levels[MUNICIPALITY].values():
        district = levels[DISTRICT].get(row["Parent"])
        if district is None:
            raise SourceError(f"BFS: municipality {_label(row)} has no district")
        canton = cantons.get(district["Parent"])
        if canton is None:
            raise SourceError(f"BFS: district {_label(district)} has no canton")
        number = _number(row)
        if number in municipalities:
            raise SourceError(f"BFS: duplicate BfsCode {number} for municipalities")
        municipalities[number] = Municipality(number, row["Name"], canton)
    return municipalities


def _number(row: dict[str, str]) -> int:
    try:
        return int(row["BfsCode"])
    except ValueError:
        raise SourceError(f"BFS: invalid BfsCode {row['BfsCode']!r}") from None


def _label(row: dict[str, str]) -> str:
    return f"{row['BfsCode']} ({row['Name']})"
