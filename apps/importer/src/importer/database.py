from collections.abc import Mapping
from dataclasses import dataclass

import psycopg
from psycopg.conninfo import make_conninfo

from importer.elcom import TARIFF_YEAR
from importer.errors import ConfigError
from importer.job import ImportData

# Fail fast when the database is down instead of waiting for the OS timeout.
CONNECT_TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    user: str
    password: str
    dbname: str

    def conninfo(self) -> str:
        # make_conninfo quotes values, so a password with spaces or quotes still works.
        return make_conninfo(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            dbname=self.dbname,
            connect_timeout=CONNECT_TIMEOUT_SECONDS,
        )


# Same variables, defaults and messages as the API (apps/api/src/database/database-options.ts),
# so one .env serves both.
def database_settings(env: Mapping[str, str]) -> DatabaseSettings:
    return DatabaseSettings(
        host=env.get("POSTGRES_HOST", "localhost"),
        port=_port(env),
        user=_required(env, "POSTGRES_USER"),
        password=_required(env, "POSTGRES_PASSWORD"),
        dbname=_required(env, "POSTGRES_DB"),
    )


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name)
    if not value:
        raise ConfigError(f"Missing environment variable {name}, see .env.example")
    return value


def _port(env: Mapping[str, str]) -> int:
    raw = env.get("POSTGRES_PORT", "5432")
    # isdigit rejects signs and decimals that int() would accept; isascii rejects
    # digits like "²" that isdigit accepts but int() does not.
    if not (raw.isascii() and raw.isdigit()) or int(raw) == 0:
        raise ConfigError(f'POSTGRES_PORT must be a port number, got "{raw}"')
    return int(raw)


def import_data(settings: DatabaseSettings, data: ImportData) -> int:
    """Replaces the data of TARIFF_YEAR; returns the number of deleted municipalities.

    Everything runs in one transaction: on any error the database keeps the
    data of the previous run.
    """
    with (
        psycopg.connect(settings.conninfo()) as conn,
        conn.transaction(),
        conn.cursor() as cur,
    ):
        # Foreign keys are NO ACTION, so rows are written parents first and
        # deleted children first.
        cantons = {m.canton.bfs_number: m.canton for m in data.municipalities.values()}
        cur.executemany(
            """
            insert into canton (bfs_number, abbreviation, name) values (%s, %s, %s)
            on conflict (bfs_number) do update
            set abbreviation = excluded.abbreviation, name = excluded.name
            """,
            [(c.bfs_number, c.abbreviation, c.name) for c in cantons.values()],
        )
        cur.executemany(
            """
            insert into municipality (bfs_number, name, canton_bfs_number) values (%s, %s, %s)
            on conflict (bfs_number) do update
            set name = excluded.name, canton_bfs_number = excluded.canton_bfs_number
            """,
            [(m.bfs_number, m.name, m.canton.bfs_number) for m in data.municipalities.values()],
        )
        operators = {t.operator.elcom_id: t.operator for t in data.tariffs}
        cur.executemany(
            """
            insert into grid_operator (elcom_id, name) values (%s, %s)
            on conflict (elcom_id) do update set name = excluded.name
            """,
            [(o.elcom_id, o.name) for o in operators.values()],
        )

        # Replacing the whole year is simpler than diffing it and also removes
        # tariffs that ElCom no longer publishes.
        cur.execute("delete from tariff where tariff_year = %s", (TARIFF_YEAR,))
        cur.execute("delete from municipality_price where tariff_year = %s", (TARIFF_YEAR,))

        # Municipalities gone from the BFS snapshot (mergers) take their prices
        # of all years with them; other years are otherwise never touched.
        current = list(data.municipalities)
        cur.execute("delete from tariff where municipality_bfs_number <> all(%s)", (current,))
        cur.execute(
            "delete from municipality_price where municipality_bfs_number <> all(%s)", (current,)
        )
        cur.execute("delete from municipality where bfs_number <> all(%s)", (current,))
        deleted = cur.rowcount

        cur.executemany(
            """
            insert into tariff (municipality_bfs_number, grid_operator_elcom_id, tariff_year,
                                total, energy, grid_usage, levies, grid_surcharge, metering)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    t.municipality_bfs_number,
                    t.operator.elcom_id,
                    TARIFF_YEAR,
                    t.total,
                    t.energy,
                    t.grid_usage,
                    t.levies,
                    t.grid_surcharge,
                    t.metering,
                )
                for t in data.tariffs
            ],
        )
        cur.executemany(
            """
            insert into municipality_price
                (municipality_bfs_number, tariff_year, average_total, multiple_operators)
            values (%s, %s, %s, %s)
            """,
            [
                (p.municipality_bfs_number, TARIFF_YEAR, p.average_total, p.multiple_operators)
                for p in data.prices.values()
            ],
        )

        # Cantons stay: they hardly ever change and nothing else would remove them.
        cur.execute(
            """
            delete from grid_operator g
            where not exists (select 1 from tariff t where t.grid_operator_elcom_id = g.elcom_id)
            """
        )
    return deleted
