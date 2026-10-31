import os
import re
import subprocess
from collections.abc import Callable, Iterator
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest
import responses
from conftest import read_fixture
from testcontainers.community.postgres import PostgresContainer

from importer import main
from importer.bfs import BFS_SNAPSHOT_URL
from importer.database import DatabaseSettings, import_data
from importer.elcom import LINDAS_SPARQL_URL
from importer.job import read_data

pytestmark = pytest.mark.integration

type Row = tuple[object, ...]

# Same image as compose.yaml, so the test sees the database the app runs on.
POSTGRES_IMAGE = "postgres:18.6-alpine"
REPO_ROOT = Path(__file__).resolve().parents[3]
TABLES = ("tariff", "municipality_price", "municipality", "grid_operator", "canton")

# The tariff id is an identity column that changes on every import, so it is
# left out when whole tables are compared.
SNAPSHOT_QUERIES = {
    "canton": "select bfs_number, abbreviation, name from canton order by 1",
    "municipality": "select bfs_number, name, canton_bfs_number from municipality order by 1",
    "grid_operator": "select elcom_id, name from grid_operator order by 1",
    "tariff": """
        select municipality_bfs_number, grid_operator_elcom_id, tariff_year,
               total, energy, grid_usage, levies, grid_surcharge, metering
        from tariff order by 1, 2, 3""",
    "municipality_price": "select * from municipality_price order by 1, 2",
}


@pytest.fixture(scope="session")
def database() -> Iterator[DatabaseSettings]:
    with PostgresContainer(POSTGRES_IMAGE, driver=None) as container:
        settings = DatabaseSettings(
            host=container.get_container_host_ip(),
            port=int(container.get_exposed_port(5432)),
            user=container.username,
            password=container.password,
            dbname=container.dbname,
        )
        # The schema belongs to the API, so the test runs its real migrations.
        subprocess.run(
            ["pnpm", "exec", "nx", "run", "api:migrate", "--skip-nx-cache"],
            cwd=REPO_ROOT,
            env={**os.environ, **_env(settings)},
            check=True,
        )
        yield settings


@pytest.fixture
def connection(database: DatabaseSettings) -> Iterator[psycopg.Connection[Row]]:
    with psycopg.connect(database.conninfo(), autocommit=True) as conn:
        conn.execute(f"truncate {', '.join(TABLES)}")
        yield conn


@pytest.fixture
def run_import(
    database: DatabaseSettings,
    http_mock: responses.RequestsMock,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> Callable[[], str]:
    for name, value in _env(database).items():
        monkeypatch.setenv(name, value)
    http_mock.get(re.compile(re.escape(BFS_SNAPSHOT_URL)), body=read_fixture("bfs-snapshot.csv"))
    http_mock.post(LINDAS_SPARQL_URL, body=read_fixture("elcom-tariffs.json"))

    def run() -> str:
        main()
        return capsys.readouterr().out

    return run


def test_imports_municipalities_and_prices(
    connection: psycopg.Connection[Row], run_import: Callable[[], str]
) -> None:
    out = run_import()

    rows = connection.execute(
        """
        select m.bfs_number, c.abbreviation, p.average_total, p.multiple_operators
        from municipality m
        join canton c on c.bfs_number = m.canton_bfs_number
        left join municipality_price p
          on p.municipality_bfs_number = m.bfs_number and p.tariff_year = 2027
        where m.bfs_number in (1, 219, 261, 499)
        order by 1
        """
    ).fetchall()
    assert rows == [
        (1, "ZH", Decimal("23.8720"), False),
        (219, "ZH", Decimal("26.3133"), True),
        (261, "ZH", Decimal("24.6320"), False),
        (499, "BE", None, None),
    ]
    assert _count(connection, "tariff") == 7
    assert out == (
        "Municipalities: 6\n"
        "  with price: 5\n"
        "  without price: 1\n"
        "  with several grid operators: 1\n"
        "  deleted: 0\n"
    )


def test_a_second_import_gives_the_same_rows(
    connection: psycopg.Connection[Row], run_import: Callable[[], str]
) -> None:
    first_out = run_import()
    first = _snapshot(connection)

    second_out = run_import()

    assert _snapshot(connection) == first
    assert second_out == first_out


def test_keeps_tariffs_of_other_years(
    connection: psycopg.Connection[Row], run_import: Callable[[], str]
) -> None:
    run_import()
    connection.execute(
        """
        insert into tariff (municipality_bfs_number, grid_operator_elcom_id, tariff_year,
                            total, energy, grid_usage, levies, grid_surcharge, metering)
        values (1, 486, 2026, 30, 10, 10, 5, 2.3, 2.7)
        """
    )
    connection.execute("insert into municipality_price values (1, 2026, 30, false)")

    run_import()

    assert connection.execute(
        "select total from tariff where municipality_bfs_number = 1 and tariff_year = 2026"
    ).fetchall() == [(Decimal("30.0000"),)]
    assert connection.execute(
        "select average_total from municipality_price where tariff_year = 2026"
    ).fetchall() == [(Decimal("30.0000"),)]


def test_deletes_municipalities_missing_from_bfs_with_all_their_prices(
    connection: psycopg.Connection[Row], run_import: Callable[[], str]
) -> None:
    connection.execute("insert into canton values (1, 'ZH', 'Zürich')")
    connection.execute("insert into municipality values (9998, 'Gone', 1)")
    connection.execute("insert into grid_operator values (99999, 'Only serves Gone')")
    for year in (2026, 2027):
        connection.execute(
            """
            insert into tariff (municipality_bfs_number, grid_operator_elcom_id, tariff_year,
                                total, energy, grid_usage, levies, grid_surcharge, metering)
            values (9998, 99999, %s, 30, 10, 10, 5, 2.3, 2.7)
            """,
            (year,),
        )
        connection.execute("insert into municipality_price values (9998, %s, 30, false)", (year,))

    out = run_import()

    for table, column in [
        ("municipality", "bfs_number"),
        ("tariff", "municipality_bfs_number"),
        ("municipality_price", "municipality_bfs_number"),
    ]:
        assert connection.execute(f"select 1 from {table} where {column} = 9998").fetchall() == []
    # Its only tariffs went with the municipality, so step 5 removes the operator too.
    assert connection.execute("select 1 from grid_operator where elcom_id = 99999").fetchall() == []
    assert out.endswith("  deleted: 1\n")


def test_deletes_grid_operators_without_tariffs(
    connection: psycopg.Connection[Row], run_import: Callable[[], str]
) -> None:
    connection.execute("insert into grid_operator values (99998, 'No tariff')")

    run_import()

    assert connection.execute("select 1 from grid_operator where elcom_id = 99998").fetchall() == []
    assert _count(connection, "grid_operator") == 5


def test_a_failed_import_leaves_the_database_unchanged(
    database: DatabaseSettings,
    connection: psycopg.Connection[Row],
    run_import: Callable[[], str],
) -> None:
    run_import()
    # Step 3 would delete this municipality, so a missing rollback shows up.
    connection.execute("insert into municipality values (9998, 'Gone', 1)")
    before = _snapshot(connection)
    data = read_data(date.today())
    # Municipality 9997 is not in the data, so step 1 never writes it and the
    # insert in step 4 fails on its foreign key, after steps 1 to 3 have run.
    broken = replace(data.tariffs[0], municipality_bfs_number=9997)

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        import_data(database, replace(data, tariffs=[*data.tariffs, broken]))

    assert _snapshot(connection) == before


def _env(settings: DatabaseSettings) -> dict[str, str]:
    return {
        "POSTGRES_HOST": settings.host,
        "POSTGRES_PORT": str(settings.port),
        "POSTGRES_USER": settings.user,
        "POSTGRES_PASSWORD": settings.password,
        "POSTGRES_DB": settings.dbname,
    }


def _snapshot(connection: psycopg.Connection[Row]) -> dict[str, list[Row]]:
    return {
        table: connection.execute(query).fetchall() for table, query in SNAPSHOT_QUERIES.items()
    }


def _count(connection: psycopg.Connection[Row], table: str) -> int:
    row = connection.execute(f"select count(*) from {table}").fetchone()
    assert row is not None
    count = row[0]
    assert isinstance(count, int)
    return count
