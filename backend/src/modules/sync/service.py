import asyncio
from datetime import datetime
import logging
from uuid import UUID

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select, text

from shared.inventory_excel import parse_inventory
from ..entities import Category, Product
from ..sale.schemas import SaleSnapshot
from ..sale.service import fingerprint, lock_operation, receive_sale
from .models import OutboxEvent, SyncReceipt

logger = logging.getLogger(__name__)


class EventInput(BaseModel):
    event_id: UUID
    kind: str = Field(pattern=r"^(inventory\.imported|sale\.completed)$")
    payload: dict


async def enqueue(session, kind, payload):
    session.add(OutboxEvent(kind=kind, payload=payload))
    await session.flush()


async def receive_inventory(session, payload):
    # Reutiliza el contrato Excel sin aceptar SQL ni nombres de columnas arbitrarios.
    from io import BytesIO
    from openpyxl import Workbook
    from shared.inventory_excel import HEADERS
    raw_products = payload.get("products", [])
    if not isinstance(raw_products, list) or not 1 <= len(raw_products) <= 5000:
        raise HTTPException(422, "Evento de inventario vacío o demasiado grande")
    wb = Workbook()
    wb.active.title = "Inventario"
    wb.active.append(HEADERS)
    try:
        for raw in raw_products:
            wb.active.append([raw.get(name) for name in HEADERS])
        data = BytesIO()
        wb.save(data)
        preview = await asyncio.to_thread(parse_inventory, data.getvalue())
        if preview.errors:
            raise HTTPException(422, preview.errors)
        product_ids = [UUID(raw["sync_id"]) for raw in raw_products]
        category_ids = [UUID(raw["category_sync_id"]) for raw in raw_products]
        if len(set(product_ids)) != len(product_ids):
            raise HTTPException(422, "Un UUID de producto aparece varias veces en el evento")
        codes = [r.codigo_barras for r in preview.rows if r.codigo_barras]
        if await session.scalar(select(Product.id_producto).where(Product.sync_id.in_(product_ids)).limit(1)):
            raise HTTPException(409, "El UUID del producto ya existe en otra operación")
        if codes and await session.scalar(select(Product.id_producto).where(Product.codigo_barras.in_(codes)).limit(1)):
            raise HTTPException(409, "El código de barras ya existe en la nube")
        categories = {c.sync_id: c for c in (await session.scalars(select(Category).where(Category.sync_id.in_(category_ids)))).all()}
        names = {r.categoria for r in preview.rows}
        existing_names = set((await session.scalars(select(Category.nombre).where(Category.nombre.in_(names)))).all())
        for raw, row in zip(raw_products, preview.rows, strict=True):
            product_uuid = UUID(raw["sync_id"])
            category_uuid = UUID(raw["category_sync_id"])
            category = categories.get(category_uuid)
            if not category:
                # No fusionar categorías por nombre: la identidad siempre es UUID.
                if row.categoria in existing_names:
                    raise HTTPException(409, "La categoría tiene UUID distinto. Aprovisiona el catálogo compartido.")
                category = Category(sync_id=category_uuid, nombre=row.categoria)
                session.add(category)
                await session.flush()
                categories[category_uuid] = category
                existing_names.add(row.categoria)
            from dataclasses import asdict
            values = asdict(row)
            values.pop("fila")
            values.pop("categoria")
            session.add(Product(**values, sync_id=product_uuid, id_categoria=category.id_categoria))
        await session.flush()
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(422, "Evento de inventario inválido") from exc


async def receive_event(session, event):
    digest = fingerprint({"kind": event.kind, "payload": event.payload})
    await lock_operation(session, event.event_id)
    receipt = await session.get(SyncReceipt, event.event_id)
    if receipt:
        if receipt.payload_hash != digest:
            raise HTTPException(409, "El UUID del evento ya se recibió con otros datos")
        return {"status": "already_applied"}
    if event.kind == "inventory.imported":
        await receive_inventory(session, event.payload)
    elif event.kind == "sale.completed":
        try:
            snapshot = SaleSnapshot.model_validate(event.payload)
        except ValidationError as exc:
            raise HTTPException(422, "Evento de venta inválido") from exc
        await receive_sale(session, snapshot)
    session.add(SyncReceipt(event_id=event.event_id, payload_hash=digest))
    await session.flush()
    return {"status": "applied"}


async def push_pending(database, settings, *, transport=None):
    if settings.database_mode != "local" or not settings.sync_url or not settings.sync_key:
        return {"status": "not_configured", "sent": 0}
    sent = 0
    async with httpx.AsyncClient(timeout=8, follow_redirects=False, transport=transport) as client:
        for _ in range(25):
            async with database.session() as session:
                # Sólo un publicador por base local; conserva orden entre procesos.
                locked = await session.scalar(text("SELECT pg_try_advisory_xact_lock(748201639)"))
                if not locked:
                    return {"status": "busy", "sent": sent}
                event = await session.scalar(select(OutboxEvent).where(OutboxEvent.status != "sent")
                    .order_by(OutboxEvent.id).limit(1).with_for_update())
                if not event:
                    return {"status": "up_to_date", "sent": sent}
                if event.status == "conflict":
                    return {"status": "conflict", "sent": sent}
                event.attempts += 1
                try:
                    response = await client.post(f"{settings.sync_url}/api/sync/events",
                        headers={"X-Sync-Key": settings.sync_key}, json={
                            "event_id": str(event.event_id), "kind": event.kind, "payload": event.payload,
                        })
                    if response.is_success and response.json().get("status") in {"applied", "already_applied"}:
                        event.status, event.sent_at, event.last_error = "sent", datetime.now(), None
                        sent += 1
                        continue
                    event.status = "conflict" if response.status_code in (400, 401, 403, 409, 422) else "pending"
                    # No persistir URLs, credenciales ni cuerpos HTTP de un servidor externo.
                    event.last_error = f"La nube devolvió HTTP {response.status_code}; revisar operación {event.event_id}."
                except (httpx.HTTPError, ValueError, AttributeError):
                    event.last_error = "Sin respuesta válida de la nube. Se reintentará con el mismo UUID."
                return {"status": event.status, "sent": sent}
    return {"status": "pending", "sent": sent}


async def sync_loop(database, settings):
    while True:
        try:
            await push_pending(database, settings)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Evita perder el worker si PostgreSQL local se reinicia.
            logger.warning("Sincronización pausada por un error local; se volverá a intentar.")
        await asyncio.sleep(settings.sync_interval)
