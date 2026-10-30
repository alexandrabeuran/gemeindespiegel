import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from importer.errors import SourceError
from importer.fetch import fetch_text

LINDAS_SPARQL_URL = "https://ld.admin.ch/query"
TARIFF_YEAR = 2027
MUNICIPALITY_PREFIX = "https://ld.admin.ch/municipality/"
OPERATOR_PREFIX = "https://energy.ld.admin.ch/elcom/electricityprice/operator/"

# One row per grid operator and municipality for profile H4, product "standard".
TARIFF_QUERY = f"""
PREFIX cube: <https://cube.link/>
PREFIX schema: <http://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX dim: <https://energy.ld.admin.ch/elcom/electricityprice/dimension/>
SELECT ?municipality ?operator ?operatorName
       ?total ?energy ?gridusage ?charge ?aidfee ?meteringrate
WHERE {{
  <https://energy.ld.admin.ch/elcom/electricityprice> cube:observationSet/cube:observation ?obs .
  ?obs dim:period "{TARIFF_YEAR}"^^xsd:gYear ;
       dim:category <https://energy.ld.admin.ch/elcom/electricityprice/category/H4> ;
       dim:product <https://energy.ld.admin.ch/elcom/electricityprice/product/standard> ;
       dim:municipality ?municipality ;
       dim:operator ?operator ;
       dim:total ?total ;
       dim:energy ?energy ;
       dim:gridusage ?gridusage ;
       dim:charge ?charge ;
       dim:aidfee ?aidfee ;
       dim:meteringrate ?meteringrate .
  ?operator schema:name ?operatorName .
}}
ORDER BY ?municipality ?operator
"""


@dataclass(frozen=True)
class GridOperator:
    elcom_id: int
    name: str


@dataclass(frozen=True)
class Tariff:
    """Prices in Rp./kWh, exactly as published by ElCom."""

    municipality_bfs_number: int
    operator: GridOperator
    total: Decimal
    energy: Decimal
    grid_usage: Decimal
    levies: Decimal
    grid_surcharge: Decimal
    metering: Decimal

    def sum_of_parts(self) -> Decimal:
        return self.energy + self.grid_usage + self.levies + self.grid_surcharge + self.metering


def fetch_tariffs() -> str:
    return fetch_text(
        "ElCom",
        "POST",
        LINDAS_SPARQL_URL,
        headers={"Accept": "application/sparql-results+json"},
        data={"query": TARIFF_QUERY},
    )


def parse_tariffs(text: str) -> list[Tariff]:
    return [_tariff(index, row) for index, row in enumerate(_bindings(text), start=1)]


# json.loads returns Any. The helpers below check every step with isinstance so
# that only verified str values leave this module, never Any.
def _bindings(text: str) -> list[object]:
    try:
        document: object = json.loads(text)
    except json.JSONDecodeError:
        document = None
    if isinstance(document, dict):
        results = document.get("results")
        if isinstance(results, dict):
            bindings = results.get("bindings")
            if isinstance(bindings, list):
                return bindings
    raise SourceError("ElCom: response is not SPARQL JSON")


def _tariff(index: int, row: object) -> Tariff:
    def decimal(name: str) -> Decimal:
        try:
            value = Decimal(_value(index, row, name))
        except InvalidOperation:
            value = Decimal("NaN")
        if not value.is_finite():
            raise SourceError(f"ElCom: row {index}: invalid {name}")
        return value

    return Tariff(
        municipality_bfs_number=_id(index, row, "municipality", MUNICIPALITY_PREFIX),
        operator=GridOperator(
            elcom_id=_id(index, row, "operator", OPERATOR_PREFIX),
            name=_value(index, row, "operatorName"),
        ),
        total=decimal("total"),
        energy=decimal("energy"),
        grid_usage=decimal("gridusage"),
        levies=decimal("charge"),
        grid_surcharge=decimal("aidfee"),
        metering=decimal("meteringrate"),
    )


def _value(index: int, row: object, name: str) -> str:
    if isinstance(row, dict):
        term = row.get(name)
        if isinstance(term, dict):
            value = term.get("value")
            if isinstance(value, str):
                return value
    raise SourceError(f"ElCom: row {index}: missing {name}")


def _id(index: int, row: object, name: str, prefix: str) -> int:
    # The id is the last path segment of the URI, e.g. .../municipality/261.
    uri = _value(index, row, name)
    number = uri.removeprefix(prefix)
    # isascii: isdigit alone accepts characters like "²" that int() rejects.
    if number == uri or not (number.isascii() and number.isdigit()):
        raise SourceError(f"ElCom: row {index}: invalid {name} {uri!r}")
    return int(number)
