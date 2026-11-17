from fastapi import HTTPException
from sqlalchemy import select


async def get_required(session, model, identifier, lock=False):
    primary_key = list(model.__table__.primary_key.columns)[0]
    statement = select(model).where(primary_key == identifier)

    if lock:
        statement = statement.with_for_update().execution_options(
            populate_existing=True
        )

    record = await session.scalar(statement)

    if record is None:
        raise HTTPException(404, "El registro no existe")

    return record
