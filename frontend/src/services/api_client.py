"""El escritorio sólo consume HTTP; no conoce credenciales de PostgreSQL."""

import httpx

from shared.catalog import validation_message


class ApiError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    def __init__(self, base_url):
        self.http = httpx.AsyncClient(
            base_url=base_url.rstrip("/"), timeout=15, follow_redirects=False
        )
        self.token = None

    async def request(self, method, path, **kwargs):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        try:
            response = await self.http.request(method, path, headers=headers, **kwargs)

            if response.is_error:
                detail = response.json().get(
                    "detail", "No se pudo completar la operación"
                )

                if isinstance(detail, dict) and "errors" in detail:
                    return detail

                if isinstance(detail, list):
                    detail = validation_message(detail)

                raise ApiError(
                    detail if isinstance(detail, str) else str(detail),
                    response.status_code,
                )

            return response.json()
        except httpx.RequestError as exc:
            raise ApiError(
                "No hay respuesta de la API. Si trabajas sin internet, comprueba que el backend y PostgreSQL locales estén activos."
            ) from exc
        except ValueError as exc:
            raise ApiError(
                "La API devolvió una respuesta inválida. Reintenta la misma operación para confirmar el resultado.",
                response.status_code,
            ) from exc

    async def login(self, email, password):
        result = await self.request(
            "POST", "/api/auth/login", json={"correo": email, "password": password}
        )
        self.token = result["access_token"]

        return result["user"]

    async def all_pages(self, path, **params):
        records = []
        offset = 0

        while True:
            page = await self.request(
                "GET", path, params={**params, "limit": 500, "offset": offset}
            )
            records.extend(page)

            if len(page) < 500:
                return records

            offset += len(page)

    async def download(self, path):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        try:
            response = await self.http.get(path, headers=headers)
        except httpx.RequestError as exc:
            raise ApiError("No se pudo descargar el comprobante") from exc

        if response.is_error:
            try:
                detail = response.json().get(
                    "detail", "No se pudo descargar el comprobante"
                )
            except ValueError:
                detail = "No se pudo descargar el comprobante"

            raise ApiError(str(detail), response.status_code)

        return response.content

    async def close(self):
        await self.http.aclose()
