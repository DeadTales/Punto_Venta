"""Validación HTTP y roles sin conectar a una base existente."""

import asyncio
from types import SimpleNamespace

import httpx
import pytest
from test_catalog import product_values

from backend.src.core.config.db_config import get_session
from backend.src.core.security import current_user
from backend.src.main import create_app
from frontend.src.services.api_client import ApiClient, ApiError


@pytest.mark.parametrize("role", ["Administrador", "Supervisor", "Cajero"])
def test_catalog_http_rejects_invalid_values_and_cashier_writes(role):
    async def scenario():
        app = create_app()

        async def user():
            return SimpleNamespace(rol=role)

        async def session():
            yield object()  # No escritura debe llegar al repositorio en estos casos.

        app.dependency_overrides[current_user] = user
        app.dependency_overrides[get_session] = session

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            cases = [
                ("POST", "/api/products", product_values(precio_venta="0.001")),
                ("PUT", "/api/products/1", product_values()),
                ("POST", "/api/categories", {"nombre": "   "}),
                (
                    "POST",
                    "/api/products/1/stock-adjustments",
                    {
                        "operation_id": "00000000-0000-0000-0000-000000000001",
                        "cantidad": "0",
                        "motivo": "Prueba",
                    },
                ),
            ]

            for method, path, body in cases:
                response = await client.request(method, path, json=body)
                assert response.status_code == (403 if role == "Cajero" else 422), (
                    response.text
                )

            if role == "Cajero":
                for path in ["/api/products/1", "/api/categories/1"]:
                    assert (await client.delete(path)).status_code == 403

    asyncio.run(scenario())


def test_invalid_api_confirmation_remains_an_uncertain_operation():
    async def scenario():
        client = ApiClient("http://test")
        await client.http.aclose()
        client.http = httpx.AsyncClient(
            base_url="http://test",
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, text="respuesta incompleta")
            ),
        )

        try:
            with pytest.raises(ApiError) as result:
                await client.request(
                    "POST", "/api/products/1/stock-adjustments", json={}
                )

            assert result.value.status_code == 200
        finally:
            await client.close()

    asyncio.run(scenario())
