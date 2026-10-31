import os
from datetime import date

import psycopg

from importer.database import database_settings, import_data
from importer.errors import ConfigError, SourceError
from importer.job import format_summary, read_data, summarize


def main() -> None:
    try:
        # Settings first: a typo in .env should not cost a full download.
        settings = database_settings(os.environ)
        data = read_data(date.today())
        deleted = import_data(settings, data)
    except (ConfigError, SourceError) as error:
        # A str exit code is printed to stderr and exits with status 1.
        raise SystemExit(f"importer: {error}") from error
    # psycopg.Error's constructor takes Any; that is library typing, not unchecked source data.
    except psycopg.Error as error:  # type: ignore[misc]
        raise SystemExit(f"importer: database: {error}") from error
    print(format_summary(summarize(data, deleted)))
