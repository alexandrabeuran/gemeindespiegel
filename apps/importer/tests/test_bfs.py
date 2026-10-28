from datetime import date

from importer.bfs import snapshot_url


def test_snapshot_url_uses_day_month_year() -> None:
    assert snapshot_url(date(2026, 3, 7)) == (
        "https://www.agvchapp.bfs.admin.ch/api/communes/snapshot?date=07-03-2026&useBfsCode=true"
    )
