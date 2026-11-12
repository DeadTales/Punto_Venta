"""Pruebas reales. Crean/eliminan sólo bases nuevas pos_test_<UUID>.

Definir POS_TEST_DATABASE_URL con un servidor PostgreSQL DE PRUEBA cuyo usuario
pueda crear bases. Nunca se escribe en la base indicada en la URL.
"""
import asyncio
from contextlib import asynccontextmanager
from dataclasses import replace
from decimal import Decimal
import os
from pathlib import Path
from uuid import UUID, uuid4

import asyncpg
import bcrypt
import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.engine import make_url

from backend.src.core.config.db_config import Base, Database
from backend.src.core.config.settings import Settings
from backend.src.main import create_app
from backend.src.modules.entities import Category, Employee, PaymentMethod, Product, Sale, SaleDetail
from backend.src.modules.product.service import import_inventory
from backend.src.modules.sale.schemas import SaleInput
from backend.src.modules.sale.service import create_sale
from backend.src.modules.sync.models import OutboxEvent, SyncReceipt
from backend.src.modules.sync.service import EventInput, push_pending, receive_event
from test_inventory_excel import row, workbook

pytestmark = pytest.mark.skipif(not os.getenv("POS_TEST_DATABASE_URL"), reason="Requiere PostgreSQL de prueba explícito")
SECRET = "test-only-secret-32-characters-long-no-production"


@asynccontextmanager
async def database():
    source = make_url(os.environ["POS_TEST_DATABASE_URL"]).set(drivername="postgresql", database="postgres")
    control = await asyncpg.connect(source.render_as_string(hide_password=False))
    name = "pos_test_" + uuid4().hex
    await control.execute(f'CREATE DATABASE "{name}"')
    settings = Settings(database_url=source.set(database=name).render_as_string(hide_password=False), jwt_secret=SECRET)
    db = Database(settings)
    try:
        async with db.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        yield db, settings
    finally:
        await db.dispose()
        await control.execute(f'DROP DATABASE "{name}" WITH (FORCE)')
        await control.close()


async def seed(db, stock="1"):
    async with db.session() as session:
        category = Category(nombre="General", sync_id=uuid4())
        employee = Employee(nombre="Ana", apellido="Prueba", correo="ana@ejemplo.local", rol="Administrador",
            password_hash=bcrypt.hashpw(b"clave-de-prueba", bcrypt.gensalt()).decode(), sync_id=uuid4())
        method = PaymentMethod(nombre="Efectivo")
        session.add_all([category, employee, method])
        await session.flush()
        product = Product(nombre="Agua", codigo_barras="EXISTENTE", id_categoria=category.id_categoria,
            precio_compra=Decimal("6.50"), precio_venta=Decimal("12.00"),
            stock_actual=Decimal(stock), stock_minimo=Decimal(0))
        session.add(product)
        await session.flush()
        return category, employee, method, product


def test_sessions_are_distinct_and_rollback_releases_connection():
    async def scenario():
        async with database() as (db, _):
            async with db.session() as first:
                async with db.session() as second:
                    assert first is not second
                    await first.execute(select(1))
                    await second.execute(select(1))
            with pytest.raises(RuntimeError):
                async with db.session() as session:
                    session.add(Category(nombre="No debe persistir"))
                    await session.flush()
                    raise RuntimeError("rollback")
            async with db.session() as session:
                assert await session.scalar(select(func.count()).select_from(Category)) == 0
    asyncio.run(scenario())


def test_two_cashiers_cannot_sell_last_unit_twice():
    async def scenario():
        async with database() as (db, _):
            _, employee, method, product = await seed(db)
            async def sell():
                try:
                    async with db.session() as session:
                        return await create_sale(session, SaleInput(operation_id=uuid4(), id_metodo_pago=method.id_metodo_pago,
                            items=[{"id_producto": product.id_producto, "cantidad": "1"}]), employee, True)
                except HTTPException as exc:
                    return exc.status_code
            results = await asyncio.gather(sell(), sell())
            assert sum(isinstance(r, Sale) for r in results) == 1
            assert 409 in results
            async with db.session() as session:
                assert (await session.get(Product, product.id_producto)).stock_actual == 0
                assert await session.scalar(select(func.count()).select_from(Sale)) == 1
                assert await session.scalar(select(func.count()).select_from(SaleDetail)) == 1
                assert await session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
    asyncio.run(scenario())


def test_sale_retry_is_idempotent_and_different_payload_conflicts():
    async def scenario():
        async with database() as (db, _):
            _, employee, method, product = await seed(db, "5")
            body = SaleInput(operation_id=uuid4(), id_metodo_pago=method.id_metodo_pago, items=[{"id_producto": product.id_producto, "cantidad": "1.250"}])
            for _ in range(2):
                async with db.session() as session:
                    sale = await create_sale(session, body, employee, True)
                    assert sale.total == Decimal("15.00")
            with pytest.raises(HTTPException):
                async with db.session() as session:
                    body.items[0].cantidad = Decimal(2)
                    await create_sale(session, body, employee, True)
            async with db.session() as session:
                assert (await session.get(Product, product.id_producto)).stock_actual == Decimal("3.750")
                assert await session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
    asyncio.run(scenario())


def test_import_validates_whole_file_and_enqueues_in_same_transaction():
    async def scenario():
        async with database() as (db, _):
            await seed(db)
            async with db.session() as session:
                result = await import_inventory(session, workbook([row(), row(codigo_barras="EXISTENTE")]), True)
                assert result.errors
            async with db.session() as session:
                assert await session.scalar(select(func.count()).select_from(Product)) == 1
                assert await session.scalar(select(func.count()).select_from(OutboxEvent)) == 0
            with pytest.raises(RuntimeError):
                async with db.session() as session:
                    result = await import_inventory(session, workbook([row()]), True)
                    assert not result.errors
                    raise RuntimeError("simula un fallo antes del commit")
            async with db.session() as session:
                assert await session.scalar(select(func.count()).select_from(Product)) == 1
                assert await session.scalar(select(func.count()).select_from(OutboxEvent)) == 0
            async with db.session() as session:
                assert not (await import_inventory(session, workbook([row()]), True)).errors
            async with db.session() as session:
                assert await session.scalar(select(func.count()).select_from(Product)) == 2
                assert await session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
    asyncio.run(scenario())


def test_cloud_receipt_prevents_duplicate_inventory_on_retry():
    async def scenario():
        async with database() as (db, _):
            category, _, _, _ = await seed(db)
            from shared.inventory_excel import parse_inventory
            product = {**parse_inventory(workbook([row()])).rows[0].json(),
                "sync_id": str(uuid4()), "category_sync_id": str(category.sync_id)}
            event = EventInput(event_id=uuid4(), kind="inventory.imported", payload={"products": [product]})
            async with db.session() as session:
                assert (await receive_event(session, event))["status"] == "applied"
            async with db.session() as session:
                assert (await receive_event(session, event))["status"] == "already_applied"
            async with db.session() as session:
                assert await session.scalar(select(func.count()).select_from(Product)) == 2
                assert await session.scalar(select(func.count()).select_from(SyncReceipt)) == 1
    asyncio.run(scenario())


def test_local_queue_survives_lost_ack_then_syncs_inventory_and_sale_once():
    async def scenario():
        async with database() as (local, local_settings), database() as (cloud, cloud_settings):
            local_category, local_employee, method, _ = await seed(local, "5")
            cloud_category, cloud_employee, _, _ = await seed(cloud, "5")
            async with cloud.session() as session:
                (await session.get(Category, cloud_category.id_categoria)).sync_id = local_category.sync_id
                (await session.get(Employee, cloud_employee.id_empleado)).sync_id = local_employee.sync_id
            async with local.session() as session:
                assert not (await import_inventory(session, workbook([row()]), True)).errors
                product = await session.scalar(select(Product).where(Product.codigo_barras == "001234"))
                await create_sale(session, SaleInput(operation_id=uuid4(), id_metodo_pago=method.id_metodo_pago,
                    items=[{"id_producto": product.id_producto, "cantidad": "1.250"}]), local_employee, True)
            local_settings = replace(local_settings, database_mode="local", sync_url="http://cloud", sync_key=SECRET)
            app = create_app(replace(cloud_settings, sync_key=SECRET))
            async with app.router.lifespan_context(app):
                cloud_transport = httpx.ASGITransport(app=app)
                async def lost_ack(request):
                    response = await cloud_transport.handle_async_request(request)
                    await response.aread()
                    raise httpx.ReadError("ack perdido", request=request)
                result = await push_pending(local, local_settings, transport=httpx.MockTransport(lost_ack))
                assert result["status"] == "pending"
                async with local.session() as session:
                    event = await session.scalar(select(OutboxEvent).order_by(OutboxEvent.id))
                    assert event.status == "pending" and event.attempts == 1
                result = await push_pending(local, local_settings, transport=cloud_transport)
                assert result["status"] == "up_to_date" and result["sent"] == 2
                result = await push_pending(local, local_settings, transport=cloud_transport)
                assert result["sent"] == 0
            async with cloud.session() as session:
                assert await session.scalar(select(func.count()).select_from(Product)) == 2
                assert await session.scalar(select(func.count()).select_from(Sale)) == 1
                assert await session.scalar(select(func.count()).select_from(SyncReceipt)) == 2
                product = await session.scalar(select(Product).where(Product.codigo_barras == "001234"))
                assert product.stock_actual == Decimal("23.500")
                assert (await session.scalar(select(Sale))).total == Decimal("15.00")
    asyncio.run(scenario())


def test_cloud_stock_conflict_does_not_create_sale_or_receipt_and_stops_queue():
    async def scenario():
        async with database() as (local, local_settings), database() as (cloud, cloud_settings):
            local_category, local_employee, method, local_product = await seed(local, "5")
            cloud_category, cloud_employee, _, cloud_product = await seed(cloud, "0")
            async with cloud.session() as session:
                (await session.get(Category, cloud_category.id_categoria)).sync_id = local_category.sync_id
                (await session.get(Employee, cloud_employee.id_empleado)).sync_id = local_employee.sync_id
                (await session.get(Product, cloud_product.id_producto)).sync_id = local_product.sync_id
            async with local.session() as session:
                await create_sale(session, SaleInput(operation_id=uuid4(), id_metodo_pago=method.id_metodo_pago,
                    items=[{"id_producto": local_product.id_producto, "cantidad": "1"}]), local_employee, True)
            app = create_app(replace(cloud_settings, sync_key=SECRET))
            async with app.router.lifespan_context(app):
                transport = httpx.ASGITransport(app=app)
                settings = replace(local_settings, database_mode="local", sync_url="http://cloud", sync_key=SECRET)
                result = await push_pending(local, settings, transport=transport)
                assert result["status"] == "conflict"
                assert (await push_pending(local, settings, transport=transport))["status"] == "conflict"
            async with cloud.session() as session:
                assert await session.scalar(select(func.count()).select_from(Sale)) == 0
                assert await session.scalar(select(func.count()).select_from(SyncReceipt)) == 0
            async with local.session() as session:
                assert (await session.scalar(select(OutboxEvent))).attempts == 1
                assert await session.scalar(select(func.count()).select_from(Sale)) == 1
    asyncio.run(scenario())


def test_api_requires_login_and_never_exposes_password_hash():
    async def scenario():
        async with database() as (db, settings):
            await seed(db)
            app = create_app(settings)
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    assert (await client.get("/api/products")).status_code == 401
                    response = await client.post("/api/auth/login", json={"correo": "ana@ejemplo.local", "password": "clave-de-prueba"})
                    assert response.status_code == 200, response.text
                    assert "password_hash" not in response.text
                    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
                    response = await client.get("/api/products", headers=headers)
                    assert response.status_code == 200, response.text
                    assert len(response.json()) == 1
                    response = await client.post("/api/inventory/import", headers=headers, files={"file": ("test.xlsx", workbook([row()]))})
                    assert response.status_code == 201, response.text
                    assert response.json()["imported"] == 1
                    response = await client.post("/api/inventory/import", headers=headers, files={"file": ("test.xlsx", workbook([row()]))})
                    assert response.status_code == 422
                    assert len((await client.get("/api/products", headers=headers)).json()) == 2
    asyncio.run(scenario())


def test_migration_is_repeatable_on_original_schema():
    async def scenario():
        async with database() as (db, settings):
            async with db.engine.begin() as connection:
                await connection.run_sync(Base.metadata.drop_all)
            connection = await asyncpg.connect(settings.database_url)
            try:
                await connection.execute(Path("db/schema/01_tablas_iniciales.sql").read_text())
                migration = Path("db/migration/04_conexion_y_sincronizacion.sql").read_text()
                await connection.execute(migration)
                await connection.execute(migration)
            finally:
                await connection.close()
            await seed(db)
    asyncio.run(scenario())
