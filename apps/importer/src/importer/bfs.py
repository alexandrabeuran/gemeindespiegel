from datetime import date
from urllib.parse import urlencode

BFS_SNAPSHOT_URL = "https://www.agvchapp.bfs.admin.ch/api/communes/snapshot"


def snapshot_url(day: date) -> str:
    # The BFS API expects DD-MM-YYYY, not ISO 8601, and useBfsCode=true so that
    # ids are the official BFS numbers that ElCom also uses.
    query = urlencode({"date": day.strftime("%d-%m-%Y"), "useBfsCode": "true"})
    return f"{BFS_SNAPSHOT_URL}?{query}"
