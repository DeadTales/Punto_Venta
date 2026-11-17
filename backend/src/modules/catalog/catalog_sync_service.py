"""Aplicación de cambios de catálogo recibidos desde una API local."""

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select

from shared.catalog import CategoryInput, ProductCreate, ProductUpdate

from ..category.category_model import Category
from ..category.category_service import save_category
from ..product.product_model import Product
from ..product.product_service import save_product
from ..sale.service import lock_operation
from .catalog_schema import CatalogChangeInput
from .catalog_service import catalog_snapshot, delete_record


async def receive_catalog(session, payload):
    try:
        change = CatalogChangeInput.model_validate(payload)
        model = Category if change.entity == "category" else Product
        sync_id = change.sync_id
        before = change.before
        after = change.after

        if model is Category:
            await lock_operation(session, "category-names")

        # Comparar sólo campos modificados evita sobreescribir stock durante una edición.
        record = await session.scalar(
            select(model).where(model.sync_id == sync_id).with_for_update()
        )

        if before is None:
            if record:
                raise HTTPException(409, "La identidad del catálogo ya existe")
        elif record is None:
            raise HTTPException(409, "El registro del catálogo ya no existe en la nube")
        else:
            current = await catalog_snapshot(session, record)
            keys = (
                before.keys()
                if after is None
                else [key for key in before if before[key] != after.get(key)]
            )

            for key in keys:
                current_value = current.get(key)
                expected_value = before[key]

                if key in {
                    "precio_compra",
                    "precio_venta",
                    "stock_actual",
                    "stock_minimo",
                }:
                    current_value = Decimal(current_value)
                    expected_value = Decimal(expected_value)

                if current_value != expected_value:
                    raise HTTPException(
                        409,
                        "El catálogo cambió en la nube; concilia los cambios antes de sincronizar",
                    )

            if after is not None:
                after = {**current, **{key: after[key] for key in keys}}

        if after is None:
            return await delete_record(
                session,
                model,
                record.id_categoria if model is Category else record.id_producto,
            )

        values = dict(after)

        if model is Category:
            return await save_category(
                session,
                CategoryInput.model_validate(values),
                record.id_categoria if record else None,
                sync_id=sync_id,
            )

        category = await session.scalar(
            select(Category).where(
                Category.sync_id == UUID(values.pop("category_sync_id"))
            )
        )

        if not category:
            raise HTTPException(409, "Falta la categoría compartida en la nube")

        values["id_categoria"] = category.id_categoria
        schema = ProductUpdate if record else ProductCreate

        if record:
            values.pop("stock_actual")

        return await save_product(
            session,
            schema.model_validate(values),
            record.id_producto if record else None,
            sync_id=sync_id,
        )
    except (KeyError, ValueError, TypeError, ValidationError) as exc:
        raise HTTPException(422, "Evento de catálogo inválido") from exc
