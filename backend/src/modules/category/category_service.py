from fastapi import HTTPException

from ..catalog.catalog_repository import get_required
from ..catalog.catalog_service import catalog_snapshot, record_catalog_change
from ..sale.service import lock_operation
from .category_model import Category
from .category_repository import CategoryRepository


async def ensure_category_name_available(session, name, identifier=None):
    # Serializa altas/renombres y comparte el criterio de normalización.
    await lock_operation(session, "category-names")
    name_exists = await CategoryRepository(session).name_exists(
        name,
        excluding_id=identifier,
    )

    if name_exists:
        raise HTTPException(409, "Ya existe una categoría con ese nombre")


async def save_category(session, body, identifier=None, queue_sync=False, sync_id=None):
    await ensure_category_name_available(session, body.nombre, identifier)
    record = (
        await get_required(session, Category, identifier, lock=True)
        if identifier is not None
        else Category()
    )
    before = await catalog_snapshot(session, record) if identifier is not None else None

    for key, value in body.model_dump().items():
        setattr(record, key, value)

    if sync_id:
        record.sync_id = sync_id

    session.add(record)
    await record_catalog_change(session, record, before, queue_sync)

    return record
