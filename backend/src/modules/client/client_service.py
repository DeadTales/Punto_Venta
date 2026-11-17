from fastapi import HTTPException
from sqlalchemy import select

from ..catalog.catalog_repository import get_required
from ..entities import Client, Sale


async def save_client(session, body, identifier=None, queue_sync=False):
    record = (
        await get_required(session, Client, identifier, lock=True)
        if identifier is not None
        else Client()
    )
    from ..people.people_sync_service import person_snapshot, queue_person_change

    before = person_snapshot(record) if identifier is not None else None

    for name, value in body.model_dump().items():
        setattr(record, name, value)

    session.add(record)
    await session.flush()

    if queue_sync:
        await queue_person_change(
            session, "client", record, before, person_snapshot(record)
        )

    return record


async def delete_client(session, identifier, queue_sync=False):
    record = await get_required(session, Client, identifier, lock=True)
    referenced = await session.scalar(
        select(Sale.id_venta).where(Sale.id_cliente == identifier).limit(1)
    )

    if referenced is not None:
        raise HTTPException(
            409, "El cliente tiene ventas registradas; conserva su historial"
        )

    if queue_sync:
        from ..people.people_sync_service import person_snapshot, queue_person_change

        await queue_person_change(
            session, "client", record, person_snapshot(record), None
        )

    await session.delete(record)
    await session.flush()

    return {"deleted": True}
