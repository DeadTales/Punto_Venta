"""Instantáneas, eventos y bajas del catálogo compartido."""

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select

from shared.catalog import ProductCreate

from ..catalog.catalog_repository import get_required
from ..category.category_model import Category
from ..entities import SaleDetail
from ..inventory.inventory_model import StockAdjustment
from ..product.product_model import Product
from ..sale.service import lock_operation
from ..sync.service import enqueue


async def catalog_snapshot(session, record):
    if isinstance(record, Category):
        return {"nombre": record.nombre, "descripcion": record.descripcion}

    values = {
        key: getattr(record, key)
        for key in ProductCreate.model_fields
        if key != "id_categoria"
    }
    values = {
        key: str(value) if isinstance(value, Decimal) else value
        for key, value in values.items()
    }
    category = await get_required(session, Category, record.id_categoria)

    return {**values, "category_sync_id": str(category.sync_id)}


async def record_catalog_change(session, record, before, queue_sync):
    await session.flush()

    if queue_sync:
        await enqueue(
            session,
            "catalog.changed",
            {
                "entity": "category" if isinstance(record, Category) else "product",
                "sync_id": str(record.sync_id),
                "before": before,
                "after": await catalog_snapshot(session, record),
            },
        )


async def delete_record(session, model, identifier, queue_sync=False):
    if model is Category:
        await lock_operation(session, "category-names")

    record = await get_required(session, model, identifier, lock=True)
    before = await catalog_snapshot(session, record)

    if model is Category:
        referenced = await session.scalar(
            select(Product.id_producto)
            .where(Product.id_categoria == identifier)
            .limit(1)
        )
        message = "No puedes eliminar una categoría que contiene productos"
    else:
        referenced = await session.scalar(
            select(SaleDetail.id_detalle_venta)
            .where(SaleDetail.id_producto == identifier)
            .limit(1)
        )
        referenced = referenced or await session.scalar(
            select(StockAdjustment.operation_id)
            .where(StockAdjustment.id_producto == identifier)
            .limit(1)
        )
        message = (
            "El producto tiene ventas o ajustes registrados; conserva su historial"
        )

    if referenced:
        raise HTTPException(409, message)

    if queue_sync:
        await enqueue(
            session,
            "catalog.changed",
            {
                "entity": "category" if model is Category else "product",
                "sync_id": str(record.sync_id),
                "before": before,
                "after": None,
            },
        )

    await session.delete(record)
    await session.flush()

    return {"deleted": True}
