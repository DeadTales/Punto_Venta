import asyncio
from dataclasses import asdict
from uuid import uuid4

from shared.inventory_excel import parse_inventory

from ..category.category_repository import CategoryRepository
from ..product.product_model import Product
from ..product.product_repository import ProductRepository
from ..sync.service import enqueue


async def validate_import(session, data):
    preview = await asyncio.to_thread(parse_inventory, data)

    if preview.errors:
        return preview

    category_names = {row.categoria for row in preview.rows}
    category_counts = await CategoryRepository(session).count_by_names(category_names)

    barcodes = [row.codigo_barras for row in preview.rows if row.codigo_barras]
    existing_barcodes = await ProductRepository(session).existing_barcodes(barcodes)

    for row in preview.rows:
        _validate_row_references(
            row, category_counts, existing_barcodes, preview.errors
        )

    return preview


def _validate_row_references(row, category_counts, existing_barcodes, errors):
    if row.categoria not in category_counts:
        errors.append(
            {
                "fila": row.fila,
                "columna": "categoria",
                "mensaje": "La categoría no existe. Créala primero o corrige el nombre.",
            }
        )
    elif category_counts[row.categoria] > 1:
        errors.append(
            {
                "fila": row.fila,
                "columna": "categoria",
                "mensaje": "Hay varias categorías con ese nombre. Resuelve la ambigüedad antes de importar.",
            }
        )

    if row.codigo_barras in existing_barcodes:
        errors.append(
            {
                "fila": row.fila,
                "columna": "codigo_barras",
                "mensaje": "El código ya está registrado. Esta carga sólo crea productos nuevos.",
            }
        )


async def import_inventory(session, data, queue_sync=False):
    preview = await validate_import(session, data)

    if preview.errors:
        return preview

    # Una transacción externa abarca todos los productos y el evento de salida.
    categories = await CategoryRepository(session).all_by_name()
    products = []

    for row in preview.rows:
        values = asdict(row)
        values.pop("fila")
        category_name = values.pop("categoria")
        category = categories[category_name]
        product = Product(**values, id_categoria=category.id_categoria, sync_id=uuid4())
        session.add(product)
        products.append(
            {
                **row.json(),
                "sync_id": str(product.sync_id),
                "category_sync_id": str(category.sync_id),
            }
        )

    await session.flush()

    if queue_sync:
        await enqueue(session, "inventory.imported", {"products": products})

    return preview
