from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal

from importer.bfs import Municipality
from importer.elcom import TARIFF_YEAR, Tariff
from importer.errors import SourceError

# ElCom rounds every value to three decimals, so the published total may be off
# by one unit in the last place. Anything larger means the row is wrong.
SUM_TOLERANCE = Decimal("0.001")


def check_tariffs_found(tariffs: Sequence[Tariff]) -> None:
    # Every per-row check passes on zero rows. Without this, an unpublished
    # tariff year or a changed IRI in the query would look like a valid import.
    if not tariffs:
        raise SourceError(f"ElCom: no tariffs found for H4, {TARIFF_YEAR}, standard")


def check_unique_pairs(tariffs: Iterable[Tariff]) -> None:
    # A duplicate would count as a second operator and set the flag wrongly.
    seen: set[tuple[int, int]] = set()
    for t in tariffs:
        pair = (t.municipality_bfs_number, t.operator.elcom_id)
        if pair in seen:
            raise SourceError(
                f"ElCom: municipality {pair[0]}, grid operator {pair[1]} appears twice"
            )
        seen.add(pair)


def check_municipality_numbers(
    tariffs: Iterable[Tariff], municipalities: Mapping[int, Municipality]
) -> None:
    unknown = sorted({t.municipality_bfs_number for t in tariffs} - municipalities.keys())
    if unknown:
        numbers = ", ".join(str(number) for number in unknown)
        raise SourceError(f"ElCom: municipality numbers not in the BFS snapshot: {numbers}")


def check_sums(tariffs: Iterable[Tariff]) -> None:
    for t in tariffs:
        difference = abs(t.total - t.sum_of_parts())
        if difference > SUM_TOLERANCE:
            raise SourceError(
                f"ElCom: municipality {t.municipality_bfs_number}, grid operator "
                f"{t.operator.elcom_id} ({t.operator.name}): total {t.total} differs by "
                f"{difference} from the sum of its parts"
            )
