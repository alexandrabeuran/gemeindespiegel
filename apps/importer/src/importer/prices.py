from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from importer.elcom import Tariff

# Matches the numeric(7,4) columns in the database.
AVERAGE_PLACES = Decimal("0.0001")


@dataclass(frozen=True)
class MunicipalityPrice:
    municipality_bfs_number: int
    average_total: Decimal
    multiple_operators: bool


def average_prices(tariffs: Iterable[Tariff]) -> dict[int, MunicipalityPrice]:
    totals: defaultdict[int, list[Decimal]] = defaultdict(list)
    for t in tariffs:
        totals[t.municipality_bfs_number].append(t.total)

    # A plain mean: ElCom does not publish how many households each operator serves.
    return {
        number: MunicipalityPrice(
            municipality_bfs_number=number,
            average_total=(sum(values, Decimal(0)) / len(values)).quantize(
                AVERAGE_PLACES, rounding=ROUND_HALF_UP
            ),
            multiple_operators=len(values) > 1,
        )
        for number, values in totals.items()
    }
