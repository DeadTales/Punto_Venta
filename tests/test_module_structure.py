"""Regresiones de imports, registro ORM y composición de rutas por dominio."""

import importlib
import pkgutil

from fastapi.routing import APIRoute
from sqlalchemy.orm import configure_mappers

from backend.src import modules
from backend.src.core.config.db_config import Base
from backend.src.main import create_app


def _api_routes(router):
    for route in router.routes:
        if isinstance(route, APIRoute):
            yield route
            continue

        included_router = getattr(route, "original_router", None)

        if included_router is not None:
            yield from _api_routes(included_router)


def test_domain_imports_register_each_table_once():
    for module_info in pkgutil.walk_packages(
        modules.__path__,
        prefix=modules.__name__ + ".",
    ):
        importlib.import_module(module_info.name)

    configure_mappers()

    expected_tables = {
        "categoria",
        "cliente",
        "empleado",
        "metodo_pago",
        "producto",
        "venta",
        "detalle_venta",
        "ajuste_inventario",
        "sync_outbox",
        "sync_receipt",
        "turno_caja",
    }
    registered_tables = set(Base.metadata.tables)
    mapped_tables = [mapper.local_table.name for mapper in Base.registry.mappers]

    assert registered_tables == expected_tables
    assert len(mapped_tables) == len(set(mapped_tables))

    for table in Base.metadata.sorted_tables:
        for foreign_key in table.foreign_keys:
            assert foreign_key.column.table.metadata is Base.metadata


def test_domain_routes_preserve_the_public_api_without_duplicates():
    expected_methods = {
        "/api/health": {"get"},
        "/api/auth/login": {"post"},
        "/api/auth/me": {"get"},
        "/api/clients": {"get", "post"},
        "/api/clients/{identifier}": {"get", "put", "delete"},
        "/api/employees": {"get", "post"},
        "/api/employees/{identifier}": {"get", "put", "delete"},
        "/api/auth/password": {"put"},
        "/api/auth/email": {"put"},
        "/api/auth/logout": {"post"},
        "/api/sales/{identifier}": {"get"},
        "/api/sales/{identifier}/cancel": {"post"},
        "/api/sales/{identifier}/receipt": {"get"},
        "/api/shifts": {"get"},
        "/api/shifts/current": {"get"},
        "/api/shifts/open": {"post"},
        "/api/shifts/{identifier}/close": {"post"},
        "/api/config": {"get"},
        "/api/reports/products": {"get"},
        "/api/payment-methods": {"get"},
        "/api/sales": {"get", "post"},
        "/api/sync/status": {"get"},
        "/api/sync/push": {"post"},
        "/api/sync/outbox/{event_id}/retry": {"post"},
        "/api/sync/events": {"post"},
        "/api/products": {"get", "post"},
        "/api/products/low-stock": {"get"},
        "/api/products/barcode/{code}": {"get"},
        "/api/products/{identifier}": {"get", "put", "delete"},
        "/api/categories": {"get", "post"},
        "/api/categories/{identifier}": {"put", "delete"},
        "/api/products/{identifier}/stock-adjustments": {"get", "post"},
        "/api/inventory/template": {"get"},
        "/api/inventory/preview": {"post"},
        "/api/inventory/import": {"post"},
    }
    app = create_app()
    schema = app.openapi()
    actual_methods = {
        path: set(operations) for path, operations in schema["paths"].items()
    }
    operations = [
        (route.path_format, method.lower())
        for route in _api_routes(app)
        for method in route.methods
    ]

    assert actual_methods == expected_methods
    assert len(operations) == sum(len(methods) for methods in expected_methods.values())
    assert len(operations) == len(set(operations))
