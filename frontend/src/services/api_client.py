"""El escritorio sólo consume HTTP; no conoce credenciales de PostgreSQL."""
import httpx


class ApiError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    def __init__(self, base_url):
        self.http = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=15, follow_redirects=False)
        self.token = None

    async def request(self, method, path, **kwargs):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        try:
            response = await self.http.request(method, path, headers=headers, **kwargs)
            if response.is_error:
                detail = response.json().get("detail", "No se pudo completar la operación")
                if isinstance(detail, dict) and "errors" in detail:
                    return detail
                raise ApiError(detail if isinstance(detail, str) else str(detail), response.status_code)
            return response.json()
        except httpx.RequestError as exc:
            raise ApiError("No hay respuesta de la API. Si trabajas sin internet, comprueba que el backend y PostgreSQL locales estén activos.") from exc

    async def login(self, email, password):
        result = await self.request("POST", "/api/auth/login", json={"correo": email, "password": password})
        self.token = result["access_token"]
        return result["user"]

    async def close(self):
        await self.http.aclose()
