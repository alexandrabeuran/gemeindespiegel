import pytest
from psycopg.conninfo import conninfo_to_dict

from importer.database import DatabaseSettings, database_settings
from importer.errors import ConfigError

ENV = {
    "POSTGRES_HOST": "db.example",
    "POSTGRES_PORT": "5433",
    "POSTGRES_USER": "tester",
    "POSTGRES_PASSWORD": "secret",
    "POSTGRES_DB": "testdb",
}


def test_reads_all_variables() -> None:
    assert database_settings(ENV) == DatabaseSettings(
        host="db.example", port=5433, user="tester", password="secret", dbname="testdb"
    )


def test_host_and_port_default_like_the_api() -> None:
    env = {k: v for k, v in ENV.items() if k not in ("POSTGRES_HOST", "POSTGRES_PORT")}

    settings = database_settings(env)

    assert (settings.host, settings.port) == ("localhost", 5432)


@pytest.mark.parametrize("name", ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"])
@pytest.mark.parametrize("value", [None, ""])
def test_a_missing_required_variable_is_named(name: str, value: str | None) -> None:
    env = {k: v for k, v in ENV.items() if k != name}
    if value is not None:
        env[name] = value

    with pytest.raises(ConfigError, match=f"Missing environment variable {name}, see .env.example"):
        database_settings(env)


@pytest.mark.parametrize("value", ["abc", "0", "-1", "5432.5", "²"])
def test_an_invalid_port_is_named(value: str) -> None:
    with pytest.raises(ConfigError, match=f'POSTGRES_PORT must be a port number, got "{value}"'):
        database_settings({**ENV, "POSTGRES_PORT": value})


def test_conninfo_keeps_special_characters_in_the_password() -> None:
    settings = database_settings({**ENV, "POSTGRES_PASSWORD": "a b'c\\d"})

    params = conninfo_to_dict(settings.conninfo())

    assert params["password"] == "a b'c\\d"
    assert params["port"] == "5433"
