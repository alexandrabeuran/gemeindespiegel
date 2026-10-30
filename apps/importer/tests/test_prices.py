from decimal import Decimal

from conftest import read_fixture

from importer.elcom import GridOperator, Tariff, parse_tariffs
from importer.prices import MunicipalityPrice, average_prices


def tariff(municipality: int, operator: int, total: str) -> Tariff:
    zero = Decimal(0)
    return Tariff(
        municipality_bfs_number=municipality,
        operator=GridOperator(elcom_id=operator, name=f"Operator {operator}"),
        total=Decimal(total),
        energy=zero,
        grid_usage=zero,
        levies=zero,
        grid_surcharge=zero,
        metering=zero,
    )


def test_a_single_operator_keeps_its_total() -> None:
    prices = average_prices(parse_tariffs(read_fixture("elcom-tariffs.json")))

    assert prices[1] == MunicipalityPrice(
        municipality_bfs_number=1, average_total=Decimal("23.8720"), multiple_operators=False
    )


def test_several_operators_get_the_plain_mean_and_the_flag() -> None:
    prices = average_prices(parse_tariffs(read_fixture("elcom-tariffs.json")))

    # Elsau: (26.426 + 23.872 + 28.642) / 3 = 26.31333...
    assert prices[219] == MunicipalityPrice(
        municipality_bfs_number=219, average_total=Decimal("26.3133"), multiple_operators=True
    )


def test_the_mean_is_rounded_half_up() -> None:
    # With three decimals per total, only four operators can produce an exact half:
    # 40.001 / 4 = 10.00025. Python's default (banker's) rounding would give 10.0002.
    totals = ["10.000", "10.000", "10.000", "10.001"]
    prices = average_prices([tariff(7, operator, total) for operator, total in enumerate(totals)])

    assert prices[7].average_total == Decimal("10.0003")


def test_municipalities_without_tariffs_get_no_price() -> None:
    prices = average_prices(parse_tariffs(read_fixture("elcom-tariffs.json")))

    assert 499 not in prices


def test_two_operators_already_set_the_flag() -> None:
    prices = average_prices([tariff(7, 1, "20.000"), tariff(7, 2, "21.000")])

    assert prices[7] == MunicipalityPrice(
        municipality_bfs_number=7, average_total=Decimal("20.5000"), multiple_operators=True
    )
