"""Recepción de inventario y ajustes con identidad compartida."""

import asyncio
from dataclasses import asdict
from decimal import Decimal
from io import BytesIO
from uuid import UUID

from fastapi import HTTPException
from openpyxl import Workbook
from pydantic import ValidationError
from sqlalchemy import select

from shared.catalog import StockAdjustmentInput
from shared.inventory_excel import HEADERS, parse_inventory

from ..category.category_model import Category
from ..entities import Employee
from ..product.product_model import Product
from ..sale.service import lock_operation
from .inventory_service import adjust_stock


async def receive_inventory(session, payload):
    # Reutiliza el contrato Excel sin aceptar SQL ni nombres de columnas arbitrarios.

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
            raise HTTPException(
                422, "Un UUID de producto aparece varias veces en el evento"
            )

        codes = [r.codigo_barras for r in preview.rows if r.codigo_barras]

        if await session.scalar(
            select(Product.id_producto).where(Product.sync_id.in_(product_ids)).limit(1)
        ):
            raise HTTPException(409, "El UUID del producto ya existe en otra operación")

        if codes and await session.scalar(
            select(Product.id_producto).where(Product.codigo_barras.in_(codes)).limit(1)
        ):
            raise HTTPException(409, "El código de barras ya existe en la nube")

        categories = {
            c.sync_id: c
            for c in (
                await session.scalars(
                    select(Category).where(Category.sync_id.in_(category_ids))
                )
            ).all()
        }
        names = {r.categoria for r in preview.rows}
        existing_names = set(
            (
                await session.scalars(
                    select(Category.nombre).where(Category.nombre.in_(names))
                )
            ).all()
        )

        for raw, row in zip(raw_products, preview.rows, strict=True):
            product_uuid = UUID(raw["sync_id"])
            category_uuid = UUID(raw["category_sync_id"])
            category = categories.get(category_uuid)

            if not category:
                # No fusionar categorías por nombre: la identidad siempre es UUID.
                if row.categoria in existing_names:
                    raise HTTPException(
                        409,
                        "La categoría tiene UUID distinto. Aprovisiona el catálogo compartido.",
                    )

                category = Category(sync_id=category_uuid, nombre=row.categoria)
                session.add(category)
                await session.flush()
                categories[category_uuid] = category
                existing_names.add(row.categoria)

            values = asdict(row)
            values.pop("fila")
            values.pop("categoria")
            session.add(
                Product(
                    **values, sync_id=product_uuid, id_categoria=category.id_categoria
                )
            )

        await session.flush()
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(422, "Evento de inventario inválido") from exc


async def receive_adjustment(session, payload):
    try:
        await lock_operation(session, UUID(payload["operation_id"]))
        product = await session.scalar(
            select(Product)
            .where(Product.sync_id == UUID(payload["product_sync_id"]))
            .with_for_update()
        )
        employee = await session.scalar(
            select(Employee).where(
                Employee.sync_id == UUID(payload["employee_sync_id"])
            )
        )

        if not product or not employee:
            raise HTTPException(
                409, "Falta el producto o empleado compartido en la nube"
            )

        if product.stock_actual != Decimal(payload["stock_anterior"]):
            raise HTTPException(
                409,
                "El stock cambió en la nube; concilia las existencias antes de sincronizar",
            )

        body = StockAdjustmentInput.model_validate(
            {key: payload[key] for key in StockAdjustmentInput.model_fields}
        )

        return await adjust_stock(session, product.id_producto, body, employee)
    except (KeyError, ValueError, TypeError, ValidationError) as exc:
        raise HTTPException(422, "Evento de ajuste inválido") from exc
