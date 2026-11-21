"""Cliente mínimo da Garmin Connect Personal API.

Referência: https://github.com/garmin/connect-personal-api-python
A chave pessoal é trocada por um token Bearer (JWT válido por 24 h) a cada
sincronização; como a sincronização é manual, não há cache de token.
"""

from __future__ import annotations

import datetime as dt
import io
import zipfile

import httpx

TOKEN_PATH = "/personalapitoken-service/personal-api/personal-api-key/token"
SEARCH_PATH = "/activitylist-service/activities/search/activities"
DOWNLOAD_PATH = "/download-service/files/activity/{activity_id}"
PAGE_SIZE = 100


class GarminError(RuntimeError):
    pass


class GarminClient:
    def __init__(self, api_key: str, base_url: str, transport: httpx.BaseTransport | None = None):
        self._api_key = api_key
        self._http = httpx.Client(base_url=base_url, timeout=30, transport=transport)

    def __enter__(self) -> GarminClient:
        token = self._request(
            "POST",
            TOKEN_PATH,
            headers={"Accept": "*/*", "Authorization": f"ApiKey {self._api_key}"},
        ).text.strip()
        if not token:
            raise GarminError("a Garmin não devolveu um token de acesso")
        self._http.headers["Authorization"] = f"Bearer {token}"
        return self

    def __exit__(self, *exc_info: object) -> None:
        self._http.close()

    def search_running_activities(self, start: dt.date, end: dt.date) -> list[dict]:
        activities: list[dict] = []
        while True:
            params = {
                "start": len(activities),
                "limit": PAGE_SIZE,
                "startDate": start.isoformat(),
                "endDate": end.isoformat(),
                "activityType": "running",
            }
            page = self._request("GET", SEARCH_PATH, params=params).json() or []
            activities.extend(page)
            if len(page) < PAGE_SIZE:
                return activities

    def download_fit(self, activity_id: int | str) -> bytes:
        """Baixa o arquivo original (ZIP) e devolve o FIT de dentro dele."""
        content = self._request(
            "GET",
            DOWNLOAD_PATH.format(activity_id=int(activity_id)),
            headers={"Accept": "application/zip, application/octet-stream"},
        ).content
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                name = next(n for n in archive.namelist() if n.lower().endswith(".fit"))
                return archive.read(name)
        except (zipfile.BadZipFile, StopIteration) as exc:
            raise GarminError(f"arquivo da atividade {activity_id} sem FIT") from exc

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            response = self._http.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise GarminError(f"falha de conexão com a Garmin: {exc}") from exc
        if response.status_code in (401, 403):
            raise GarminError("chave da Garmin inválida ou expirada (GARMIN_PERSONAL_API_KEY)")
        if response.is_error:
            raise GarminError(f"a Garmin respondeu {response.status_code} em {path}")
        return response
