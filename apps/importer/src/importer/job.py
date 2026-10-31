from dataclasses import dataclass
from datetime import date

from importer import bfs, elcom
from importer.bfs import Municipality
from importer.checks import (
    check_municipality_numbers,
    check_sums,
    check_tariffs_found,
    check_unique_pairs,
)
from importer.elcom import Tariff
from importer.prices import MunicipalityPrice, average_prices


@dataclass(frozen=True)
class ImportData:
    municipalities: dict[int, Municipality]
    tariffs: list[Tariff]
    prices: dict[int, MunicipalityPrice]


@dataclass(frozen=True)
class Summary:
    municipalities: int
    with_price: int
    without_price: int
    multiple_operators: int
    deleted: int


def read_data(day: date) -> ImportData:
    """Fetches both sources and runs every check before anything is written."""
    municipalities = bfs.parse_snapshot(bfs.fetch_snapshot(day))
    tariffs = elcom.parse_tariffs(elcom.fetch_tariffs())
    check_tariffs_found(tariffs)
    check_unique_pairs(tariffs)
    check_municipality_numbers(tariffs, municipalities)
    check_sums(tariffs)
    return ImportData(municipalities, tariffs, average_prices(tariffs))


def summarize(data: ImportData, deleted: int) -> Summary:
    # The number check guarantees that every price belongs to a known municipality.
    with_price = len(data.prices)
    return Summary(
        municipalities=len(data.municipalities),
        with_price=with_price,
        without_price=len(data.municipalities) - with_price,
        multiple_operators=sum(1 for p in data.prices.values() if p.multiple_operators),
        deleted=deleted,
    )


def format_summary(summary: Summary) -> str:
    return "\n".join(
        [
            f"Municipalities: {summary.municipalities}",
            f"  with price: {summary.with_price}",
            f"  without price: {summary.without_price}",
            f"  with several grid operators: {summary.multiple_operators}",
            f"  deleted: {summary.deleted}",
        ]
    )
