from dataclasses import asdict
from collections import Counter
import asyncio
from uuid import uuid4

from sqlalchemy import select
from shared.inventory_excel import parse_inventory

from .models import Category, Product
from ..sync.service import enqueue


async def validate_import(session, data):
    preview = await asyncio.to_thread(parse_inventory, data)
    if preview.errors:
        return preview
    names = {r.categoria for r in preview.rows}
    categories = Counter((await session.scalars(select(Category.nombre).where(Category.nombre.in_(names)))).all())
    codes = [r.codigo_barras for r in preview.rows if r.codigo_barras]
    existing = set((await session.scalars(select(Product.codigo_barras).where(Product.codigo_barras.in_(codes)))).all()) if codes else set()
    for row in preview.rows:
        if row.categoria not in categories:
            preview.errors.append({"fila": row.fila, "columna": "categoria", "mensaje": "La categoría no existe. Créala primero o corrige el nombre."})
        elif categories[row.categoria] > 1:
            preview.errors.append({"fila": row.fila, "columna": "categoria", "mensaje": "Hay varias categorías con ese nombre. Resuelve la ambigüedad antes de importar."})
        if row.codigo_barras in existing:
            preview.errors.append({"fila": row.fila, "columna": "codigo_barras", "mensaje": "El código ya está registrado. Esta carga sólo crea productos nuevos."})
    return preview


async def import_inventory(session, data, queue_sync=False):
    preview = await validate_import(session, data)
    if preview.errors:
        return preview
    # Una transacción externa abarca todos los productos y el evento de salida.
    categories = {c.nombre: c for c in (await session.scalars(select(Category))).all()}
    products = []
    for row in preview.rows:
        values = asdict(row)
        values.pop("fila")
        name = values.pop("categoria")
        category = categories[name]
        product = Product(**values, id_categoria=category.id_categoria, sync_id=uuid4())
        session.add(product)
        products.append({**row.json(), "sync_id": str(product.sync_id),
                         "category_sync_id": str(category.sync_id)})
    await session.flush()
    if queue_sync:
        await enqueue(session, "inventory.imported", {"products": products})
    return preview
