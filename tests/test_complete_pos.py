"""Flujos completos contra PostgreSQL aislado: usuarios, caja y tickets."""

import asyncio
from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

import httpx
from sqlalchemy import func, select
from test_postgres import SECRET, database, seed
from test_postgres import pytestmark as pytestmark

from backend.src.core.migrations import migrate
from backend.src.main import create_app
from backend.src.modules.client.client_service import save_client
from backend.src.modules.employee.employee_service import save_employee
from backend.src.modules.entities import Client, Employee, Product, Sale
from backend.src.modules.sale.sale_schema import CancelSaleInput
from backend.src.modules.sale.sale_service import cancel_sale
from backend.src.modules.sale.schemas import SaleInput
from backend.src.modules.sale.service import create_sale
from backend.src.modules.sync.service import push_pending
from shared.people import ClientInput, EmployeeCreate


async def login(client, email="ana@ejemplo.local", password="clave-de-prueba"):
    response = await client.post(
        "/api/auth/login", json={"correo": email, "password": password}
    )
    assert response.status_code == 200, response.text

    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_complete_sale_client_employee_shift_receipt_and_cancellation():
    async def scenario():
        async with database() as (db, settings):
            _, administrator, _, product = await seed(db, "5")
            app = create_app(replace(settings, tax_rate=Decimal("0.16")))

            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app), base_url="http://test"
                ) as client:
                    admin = await login(client)
                    response = await client.post(
                        "/api/clients",
                        headers=admin,
                        json={
                            "nombre": "Cliente nuevo",
                            "correo": "cliente@ejemplo.local",
                            "rfc_o_identificacion_fiscal": "RFC-PRUEBA",
                        },
                    )
                    assert response.status_code == 201, response.text
                    client_id = response.json()["id_cliente"]
                    assert (
                        len(
                            (
                                await client.get(
                                    "/api/clients",
                                    headers=admin,
                                    params={"q": "RFC-PRUEBA"},
                                )
                            ).json()
                        )
                        == 1
                    )
                    response = await client.post(
                        "/api/employees",
                        headers=admin,
                        json={
                            "nombre": "Caja",
                            "apellido": "Prueba",
                            "correo": "caja@ejemplo.local",
                            "rol": "Cajero",
                            "password": "clave-del-cajero",
                        },
                    )
                    assert response.status_code == 201, response.text
                    assert "password" not in response.text
                    employee_id = response.json()["id_empleado"]
                    cashier = await login(
                        client, "caja@ejemplo.local", "clave-del-cajero"
                    )
                    assert (
                        await client.get("/api/employees", headers=cashier)
                    ).status_code == 403
                    method_id = (
                        await client.get("/api/payment-methods", headers=cashier)
                    ).json()[0]["id_metodo_pago"]
                    body = {
                        "operation_id": str(uuid4()),
                        "id_cliente": client_id,
                        "id_metodo_pago": method_id,
                        "items": [
                            {"id_producto": product.id_producto, "cantidad": "1.250"}
                        ],
                    }
                    assert (
                        await client.post("/api/sales", headers=cashier, json=body)
                    ).status_code == 409
                    opening = {"operation_id": str(uuid4()), "fondo_inicial": "100"}
                    opened = await client.post(
                        "/api/shifts/open", headers=cashier, json=opening
                    )
                    assert opened.status_code == 201, opened.text
                    shift_id = opened.json()["id_turno"]
                    assert (
                        await client.post(
                            "/api/shifts/open", headers=cashier, json=opening
                        )
                    ).json()["id_turno"] == shift_id

                    sale_ids = []

                    for _ in range(2):
                        response = await client.post(
                            "/api/sales", headers=cashier, json=body
                        )
                        assert response.status_code == 201, response.text
                        assert response.json()["total"] == "15.00"
                        assert response.json()["impuesto"] == "2.07"
                        sale_ids.append(response.json()["id_venta"])

                    assert sale_ids[0] == sale_ids[1]
                    identifier = sale_ids[0]

                    async with db.session() as session:
                        assert (
                            await session.get(Product, product.id_producto)
                        ).stock_actual == Decimal("3.750")
                        (
                            await session.get(Product, product.id_producto)
                        ).nombre = "Nombre nuevo"

                    detail = await client.get(
                        f"/api/sales/{identifier}", headers=cashier
                    )
                    assert detail.status_code == 200, detail.text
                    assert detail.json()["items"][0]["nombre"] == "Agua"
                    receipt = await client.get(
                        f"/api/sales/{identifier}/receipt", headers=cashier
                    )
                    assert receipt.status_code == 200 and receipt.content.startswith(
                        b"%PDF-"
                    )
                    cancellation = {
                        "operation_id": str(uuid4()),
                        "motivo": "Devolución completa",
                    }
                    assert (
                        await client.post(
                            f"/api/sales/{identifier}/cancel",
                            headers=cashier,
                            json=cancellation,
                        )
                    ).status_code == 403

                    for _ in range(2):
                        response = await client.post(
                            f"/api/sales/{identifier}/cancel",
                            headers=admin,
                            json=cancellation,
                        )
                        assert response.status_code == 200, response.text
                        assert response.json()["estado"] == "Cancelada"

                    async with db.session() as session:
                        assert (
                            await session.get(Product, product.id_producto)
                        ).stock_actual == Decimal("5")
                        assert (
                            await session.scalar(select(func.count()).select_from(Sale))
                            == 1
                        )

                    closing = {
                        "operation_id": str(uuid4()),
                        "efectivo_contado": "100",
                        "notas": "Cierre de prueba",
                    }

                    for _ in range(2):
                        closed = await client.post(
                            f"/api/shifts/{shift_id}/close",
                            headers=cashier,
                            json=closing,
                        )
                        assert closed.status_code == 200, closed.text
                        assert Decimal(str(closed.json()["diferencia"])) == 0

                    assert (
                        await client.post(
                            f"/api/sales/{identifier}/cancel",
                            headers=admin,
                            json=cancellation,
                        )
                    ).status_code == 200
                    assert (
                        await client.delete(f"/api/clients/{client_id}", headers=admin)
                    ).status_code == 409
                    assert (
                        await client.delete(
                            f"/api/employees/{administrator.id_empleado}", headers=admin
                        )
                    ).status_code == 409
                    assert (
                        await client.delete(
                            f"/api/employees/{employee_id}", headers=admin
                        )
                    ).status_code == 200
                    assert (
                        await client.get("/api/auth/me", headers=cashier)
                    ).status_code == 401

    asyncio.run(scenario())


def test_account_changes_revoke_previous_tokens_and_never_echo_passwords():
    async def scenario():
        async with database() as (db, settings):
            await seed(db)
            app = create_app(settings)

            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app), base_url="http://test"
                ) as client:
                    original = await login(client)
                    invalid = await client.put(
                        "/api/auth/password",
                        headers=original,
                        json={
                            "current_password": "clave-de-prueba",
                            "new_password": "secreto",
                        },
                    )
                    assert invalid.status_code == 422 and "secreto" not in invalid.text
                    response = await client.put(
                        "/api/auth/password",
                        headers=original,
                        json={
                            "current_password": "incorrecta",
                            "new_password": "nueva-clave-segura",
                        },
                    )
                    assert response.status_code == 403
                    response = await client.put(
                        "/api/auth/password",
                        headers=original,
                        json={
                            "current_password": "clave-de-prueba",
                            "new_password": "nueva-clave-segura",
                        },
                    )
                    assert response.status_code == 200, response.text
                    updated = {
                        "Authorization": "Bearer " + response.json()["access_token"]
                    }
                    assert (
                        await client.get("/api/auth/me", headers=original)
                    ).status_code == 401
                    assert (
                        await client.get("/api/auth/me", headers=updated)
                    ).status_code == 200
                    response = await client.put(
                        "/api/auth/email",
                        headers=updated,
                        json={
                            "correo": "NUEVO@EJEMPLO.LOCAL",
                            "current_password": "nueva-clave-segura",
                        },
                    )
                    assert response.status_code == 200, response.text
                    assert response.json()["user"]["correo"] == "nuevo@ejemplo.local"
                    newest = await login(
                        client, "nuevo@ejemplo.local", "nueva-clave-segura"
                    )
                    assert (
                        await client.get("/api/auth/me", headers=updated)
                    ).status_code == 401
                    assert (
                        await client.post("/api/auth/logout", headers=newest)
                    ).status_code == 200
                    assert (
                        await client.get("/api/auth/me", headers=newest)
                    ).status_code == 401

    asyncio.run(scenario())


def test_closing_shift_serializes_a_concurrent_sale_and_freezes_cut():
    async def scenario():
        async with database() as (db, settings):
            _, _, method, product = await seed(db, "5")
            app = create_app(settings)

            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app), base_url="http://test"
                ) as client:
                    headers = await login(client)
                    response = await client.post(
                        "/api/shifts/open",
                        headers=headers,
                        json={"operation_id": str(uuid4()), "fondo_inicial": "100"},
                    )
                    shift_id = response.json()["id_turno"]
                    sale_body = {
                        "operation_id": str(uuid4()),
                        "id_metodo_pago": method.id_metodo_pago,
                        "items": [
                            {"id_producto": product.id_producto, "cantidad": "1"}
                        ],
                    }
                    sale, closing = await asyncio.gather(
                        client.post("/api/sales", headers=headers, json=sale_body),
                        client.post(
                            f"/api/shifts/{shift_id}/close",
                            headers=headers,
                            json={
                                "operation_id": str(uuid4()),
                                "efectivo_contado": "112",
                            },
                        ),
                    )
                    assert closing.status_code == 200, closing.text
                    assert sale.status_code in {201, 409}, sale.text
                    expected = (
                        Decimal("112") if sale.status_code == 201 else Decimal("100")
                    )
                    assert Decimal(str(closing.json()["efectivo_esperado"])) == expected

                    if sale.status_code == 201:
                        response = await client.post(
                            f"/api/sales/{sale.json()['id_venta']}/cancel",
                            headers=headers,
                            json={
                                "operation_id": str(uuid4()),
                                "motivo": "Intento tras cierre",
                            },
                        )
                        assert response.status_code == 409

    asyncio.run(scenario())


def test_new_people_sale_and_cancellation_sync_in_order_once():
    async def scenario():
        async with (
            database() as (local, local_settings),
            database() as (cloud, cloud_settings),
        ):
            category, admin, method, product = await seed(local, "5")
            cloud_category, cloud_admin, _, cloud_product = await seed(cloud, "5")

            async with cloud.session() as session:
                (
                    await session.get(Employee, cloud_admin.id_empleado)
                ).sync_id = admin.sync_id
                (
                    await session.get(Product, cloud_product.id_producto)
                ).sync_id = product.sync_id

            async with local.session() as session:
                client = await save_client(
                    session, ClientInput(nombre="Cliente sincronizado"), queue_sync=True
                )
                cashier = await save_employee(
                    session,
                    EmployeeCreate(
                        nombre="Caja",
                        apellido="Local",
                        correo="caja@ejemplo.local",
                        password="clave-del-cajero",
                        rol="Cajero",
                    ),
                    admin,
                    queue_sync=True,
                )
                sale = await create_sale(
                    session,
                    SaleInput(
                        operation_id=uuid4(),
                        id_cliente=client.id_cliente,
                        id_metodo_pago=method.id_metodo_pago,
                        items=[
                            {"id_producto": product.id_producto, "cantidad": "1.250"}
                        ],
                    ),
                    cashier,
                    True,
                    Decimal("0.16"),
                )
                await cancel_sale(
                    session,
                    sale.id_venta,
                    CancelSaleInput(operation_id=uuid4(), motivo="Devolución"),
                    admin,
                    True,
                )

            app = create_app(replace(cloud_settings, sync_key=SECRET))

            async with app.router.lifespan_context(app):
                transport = httpx.ASGITransport(app=app)
                settings = replace(
                    local_settings,
                    database_mode="local",
                    sync_url="http://cloud",
                    sync_key=SECRET,
                )
                assert (await push_pending(local, settings, transport=transport))[
                    "sent"
                ] == 4
                assert (await push_pending(local, settings, transport=transport))[
                    "sent"
                ] == 0

            async with cloud.session() as session:
                assert (await session.scalar(select(Sale))).estado == "Cancelada"
                assert (
                    await session.get(Product, cloud_product.id_producto)
                ).stock_actual == Decimal("5")
                assert (
                    await session.scalar(select(func.count()).select_from(Client)) == 1
                )

    asyncio.run(scenario())


def test_explicit_migrations_preserve_existing_records_and_can_run_twice():
    async def scenario():
        async with database() as (db, _):
            _, employee, method, product = await seed(db, "5")

            async with db.session() as session:
                sale = await create_sale(
                    session,
                    SaleInput(
                        operation_id=uuid4(),
                        id_metodo_pago=method.id_metodo_pago,
                        items=[{"id_producto": product.id_producto, "cantidad": "1"}],
                    ),
                    employee,
                )

            for _ in range(2):
                assert len(await migrate(db)) == 4

            async with db.session() as session:
                assert (
                    await session.get(Employee, employee.id_empleado)
                ).password_hash == employee.password_hash
                assert (
                    await session.get(Product, product.id_producto)
                ).stock_actual == Decimal("4")
                assert (await session.get(Sale, sale.id_venta)).total == Decimal("12")
                assert await session.scalar(select(func.count()).select_from(Sale)) == 1

    asyncio.run(scenario())


def test_product_demand_and_historical_pagination_use_confirmed_sales():
    async def scenario():
        async with database() as (db, settings):
            _, employee, method, product = await seed(db, "5")

            async with db.session() as session:
                for _ in range(2):
                    await create_sale(
                        session,
                        SaleInput(
                            operation_id=uuid4(),
                            id_metodo_pago=method.id_metodo_pago,
                            items=[
                                {"id_producto": product.id_producto, "cantidad": "1"}
                            ],
                        ),
                        employee,
                    )

            app = create_app(settings)

            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app), base_url="http://test"
                ) as client:
                    headers = await login(client)
                    first = await client.get(
                        "/api/sales", headers=headers, params={"limit": 1}
                    )
                    second = await client.get(
                        "/api/sales", headers=headers, params={"limit": 1, "offset": 1}
                    )
                    assert first.json()[0]["id_venta"] != second.json()[0]["id_venta"]
                    report = await client.get(
                        "/api/reports/products",
                        headers=headers,
                        params={"days": 1, "lead_days": 7},
                    )
                    assert report.status_code == 200, report.text
                    assert report.json()[0]["cantidad_vendida"] == "2.000"
                    assert report.json()[0]["reposicion_sugerida"] == "11.000"
                    assert (
                        await client.get(
                            "/api/sales",
                            headers=headers,
                            params={"date_from": "2026-12-01", "date_to": "2026-01-01"},
                        )
                    ).status_code == 422

    asyncio.run(scenario())


def test_desktop_services_complete_a_real_api_sale_and_cash_cycle():
    import pytest

    pytest.importorskip("flet")
    from test_frontend import Page

    from frontend.src.app import PosApp

    async def scenario():
        async with database() as (db, settings):
            await seed(db, "5")
            api = create_app(replace(settings, tax_rate=Decimal("0.16")))

            async with api.router.lifespan_context(api):
                app = PosApp(Page(), mode="api", base_url="http://test")
                await app.api.http.aclose()
                app.api.http = httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=api), base_url="http://test"
                )

                try:
                    app.state.user = await app.api.login(
                        "ana@ejemplo.local", "clave-de-prueba"
                    )
                    await app.reload()
                    assert not app.state.shift_open and len(app.state.products) == 1
                    await app.open_cash(
                        {"operation_id": str(uuid4()), "fondo_inicial": "100"}
                    )
                    client = await app.people.save({"nombre": "Desde escritorio"})
                    await app.products.refresh_after_write()
                    app.state.cart_client = client["id_cliente"]
                    app.add_to_cart(app.state.products[0])
                    result = await app.checkout(app.state.methods[0]["id_metodo_pago"])
                    detail = await app.sales.detail(result["id_venta"])
                    assert (
                        detail["cliente"] == "Desde escritorio"
                        and detail["items"][0]["nombre"] == "Agua"
                    )
                    assert (await app.sales.pdf(result["id_venta"])).startswith(
                        b"%PDF-"
                    )
                    await app.sales.cancel(
                        result["id_venta"],
                        {"operation_id": str(uuid4()), "motivo": "Prueba de interfaz"},
                    )
                    await app.products.refresh_after_write()
                    assert Decimal(str(app.state.products[0]["stock_actual"])) == 5
                    closed = await app.close_cash(
                        {"operation_id": str(uuid4()), "efectivo_contado": "100"}
                    )
                    assert (
                        not app.state.shift_open
                        and Decimal(str(closed["diferencia"])) == 0
                    )
                finally:
                    await app.api.close()

    asyncio.run(scenario())
