import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .core.config.db_config import Database
from .core.config.settings import Settings
from .modules.auth.auth_route import router as account_router
from .modules.cash.cash_route import router as cash_router
from .modules.category.category_route import router as categories_router
from .modules.client.client_route import router as clients_router
from .modules.employee.employee_route import router as employees_router
from .modules.inventory.inventory_route import router as inventory_router
from .modules.product.product_route import router as products_router
from .modules.reports.reports_route import router as reports_router
from .modules.routes import router as api_router
from .modules.sale.sale_route import router as sales_router
from .modules.sync.service import sync_loop
from .modules.system.system_route import router as system_router


def create_app(settings: Settings | None = None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.settings = settings or Settings.from_env()
        app.state.database = Database(app.state.settings)
        task = None

        if (
            app.state.settings.database_mode == "local"
            and app.state.settings.sync_url
            and app.state.settings.sync_key
        ):
            task = asyncio.create_task(
                sync_loop(app.state.database, app.state.settings)
            )

        try:
            yield
        finally:
            if task:
                task.cancel()

                with suppress(asyncio.CancelledError):
                    await task

            await app.state.database.dispose()

    app = FastAPI(title="Punto · API POS", version="0.1.0", lifespan=lifespan)
    app.include_router(api_router)
    app.include_router(products_router)
    app.include_router(categories_router)
    app.include_router(inventory_router)
    app.include_router(clients_router)
    app.include_router(employees_router)
    app.include_router(account_router)
    app.include_router(cash_router)
    app.include_router(sales_router)
    app.include_router(system_router)
    app.include_router(reports_router)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        errors = [
            {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]

        return JSONResponse(status_code=422, content={"detail": errors})

    @app.exception_handler(IntegrityError)
    async def integrity_error(request, exc):
        return JSONResponse(
            status_code=409,
            content={
                "detail": "La operación viola una restricción (código duplicado, referencia o valor inválido). No se guardó ningún cambio."
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        return JSONResponse(
            status_code=503,
            content={
                "detail": "La base de datos no está disponible. No cambies de base ni repitas con otro identificador de operación."
            },
        )

    return app


app = create_app()
