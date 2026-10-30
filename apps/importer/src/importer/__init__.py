from datetime import date

from importer.errors import SourceError
from importer.job import format_summary, read_data, summarize


def main() -> None:
    try:
        data = read_data(date.today())
    except SourceError as error:
        # A str exit code is printed to stderr and exits with status 1.
        raise SystemExit(f"importer: {error}") from error
    print(format_summary(summarize(data)))
