from collections.abc import Mapping

import requests

from importer.errors import SourceError

TIMEOUT_SECONDS = 30


def fetch_text(
    source: str,
    method: str,
    url: str,
    *,
    headers: Mapping[str, str] | None = None,
    data: Mapping[str, str] | None = None,
) -> str:
    # No retries: the job runs on demand, so a failed run is simply started again.
    try:
        response = requests.request(
            method, url, headers=headers, data=data, timeout=TIMEOUT_SECONDS
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise SourceError(f"{source}: request failed: {error}") from error
    # Both sources send UTF-8. Without a charset header requests would fall back
    # to ISO-8859-1 for text responses and garble names like "Zürich".
    response.encoding = "utf-8"
    return response.text
