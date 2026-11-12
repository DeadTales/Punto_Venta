"""Un gestor/pool por proceso; una sesión independiente por unidad de trabajo."""
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .settings import Settings


class Base(DeclarativeBase):
    pass


class Database:
    """Los modelos heredan Base y reciben sesiones; nunca abren conexiones.

    La instancia vive en app.state durante todo el lifespan de FastAPI.
    No se comparte AsyncSession entre peticiones ni tareas concurrentes.
    """

    def __init__(self, settings: Settings):
        url = make_url(settings.database_url)
        if url.drivername in {"postgres", "postgresql"}:
            url = url.set(drivername="postgresql+asyncpg")
        if url.drivername != "postgresql+asyncpg":
            raise ValueError("Esta aplicación requiere PostgreSQL con asyncpg")
        query = dict(url.query)
        sslmode = query.pop("sslmode", None)
        # asyncpg recibe ssl en lugar del parámetro libpq sslmode.
        if sslmode:
            query["ssl"] = sslmode
        self.engine = create_async_engine(
            url.set(query=query), pool_pre_ping=True, pool_recycle=1800,
            pool_size=settings.pool_size, max_overflow=settings.max_overflow,
            pool_timeout=10, connect_args={"timeout": 5, "command_timeout": 30},
            echo=False,
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Commit sólo al terminar; rollback y devolución al pool ante errores."""
        async with self.sessions() as session:
            async with session.begin():
                yield session

    async def dispose(self):
        await self.engine.dispose()


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.database.session() as session:
        yield session
