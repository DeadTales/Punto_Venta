from fastapi import HTTPException

from shared.catalog import adjusted_stock

from ..catalog.catalog_repository import get_required
from ..product.product_model import Product
from ..sale.service import fingerprint, lock_operation
from ..sync.service import enqueue
from .inventory_model import StockAdjustment


async def adjust_stock(session, identifier, body, employee, queue_sync=False):
    await lock_operation(session, body.operation_id)
    digest = fingerprint(
        {
            **body.model_dump(mode="json"),
            "product": identifier,
            "employee": str(employee.sync_id),
        }
    )
    existing = await session.get(StockAdjustment, body.operation_id)

    if existing:
        if existing.request_hash != digest:
            raise HTTPException(409, "La clave de operación ya se usó con otros datos")

        return existing

    product = await get_required(session, Product, identifier, lock=True)

    try:
        new_stock = adjusted_stock(product.stock_actual, body.cantidad)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

    record = StockAdjustment(
        operation_id=body.operation_id,
        id_producto=identifier,
        id_empleado=employee.id_empleado,
        cantidad=body.cantidad,
        motivo=body.motivo,
        stock_anterior=product.stock_actual,
        stock_nuevo=new_stock,
        request_hash=digest,
    )
    session.add(record)
    product.stock_actual = new_stock
    await session.flush()

    if queue_sync:
        await enqueue(
            session,
            "inventory.adjusted",
            {
                **body.model_dump(mode="json"),
                "product_sync_id": str(product.sync_id),
                "employee_sync_id": str(employee.sync_id),
                "stock_anterior": str(record.stock_anterior),
            },
        )

    return record
