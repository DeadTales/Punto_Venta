from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config.db_config import Base


class Repository:
    """Punto de acceso común para repositorios; la transacción pertenece al caller."""

    def __init__(self, session: AsyncSession, model: type[Base]):
        self.session = session
        self.model = model

    async def get(self, identifier: int):
        return await self.session.get(self.model, identifier)

    async def list(self, limit: int = 100, offset: int = 0):
        return list((await self.session.scalars(
            select(self.model).order_by(*self.model.__table__.primary_key.columns)
            .offset(offset).limit(limit)
        )).all())

    async def add(self, **values):
        record = self.model(**values)
        self.session.add(record)
        await self.session.flush()
        return record
