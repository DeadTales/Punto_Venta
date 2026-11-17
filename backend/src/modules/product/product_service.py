from fastapi import HTTPException

from ..catalog.catalog_repository import get_required
from ..catalog.catalog_service import catalog_snapshot, record_catalog_change
from ..category.category_repository import CategoryRepository
from .product_model import Product
from .product_repository import ProductRepository


async def save_product(session, body, identifier=None, queue_sync=False, sync_id=None):
    # Un bloqueo compartido evita borrar la categoría durante el alta.
    category = await CategoryRepository(session).get_for_product(body.id_categoria)

    if category is None:
        raise HTTPException(422, "Selecciona una categoría existente")

    record = (
        await get_required(session, Product, identifier, lock=True)
        if identifier is not None
        else Product()
    )
    before = await catalog_snapshot(session, record) if identifier is not None else None

    if body.codigo_barras:
        barcode_exists = await ProductRepository(session).barcode_exists(
            body.codigo_barras,
            excluding_id=identifier,
        )

        if barcode_exists:
            raise HTTPException(409, "El código de barras ya está registrado")

    for key, value in body.model_dump().items():
        setattr(record, key, value)

    if sync_id:
        record.sync_id = sync_id

    session.add(record)
    await record_catalog_change(session, record, before, queue_sync)

    return record
