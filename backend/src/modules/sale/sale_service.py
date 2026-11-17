"""Consultas de comprobantes y cancelación auditada de ventas."""

from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select

from ..cash.cash_model import CashShift
from ..catalog.catalog_repository import get_required
from ..entities import Client, Employee, PaymentMethod, Product, Sale, SaleDetail
from .service import fingerprint, lock_operation


async def sale_detail(session, identifier):
    sale = await get_required(session, Sale, identifier)
    employee = await session.get(Employee, sale.id_empleado)
    client = await session.get(Client, sale.id_cliente) if sale.id_cliente else None
    method = await session.get(PaymentMethod, sale.id_metodo_pago)
    rows = (
        await session.execute(
            select(SaleDetail, Product)
            .join(Product, SaleDetail.id_producto == Product.id_producto)
            .where(SaleDetail.id_venta == identifier)
            .order_by(SaleDetail.id_detalle_venta)
        )
    ).all()
    fields = (
        "id_venta",
        "sync_id",
        "id_cliente",
        "id_empleado",
        "id_metodo_pago",
        "id_turno",
        "fecha_hora",
        "estado",
        "total",
        "tasa_impuesto",
        "impuesto",
        "cancel_motivo",
        "cancelado_en",
        "cancelado_por",
    )
    result = {name: getattr(sale, name) for name in fields}
    result.update(
        empleado=f"{employee.nombre} {employee.apellido}",
        cliente=client.nombre if client else "Público general",
        metodo_pago=method.nombre,
        subtotal=sale.total - sale.impuesto,
        items=[
            {
                "id_producto": product.id_producto,
                "nombre": detail.nombre_producto or product.nombre,
                "codigo_barras": detail.codigo_barras or product.codigo_barras,
                "cantidad": detail.cantidad,
                "precio_unitario_venta": detail.precio_unitario_venta,
                "subtotal": detail.subtotal,
            }
            for detail, product in rows
        ],
    )

    return result


async def cancel_sale(session, identifier, body, employee, queue_sync=False):
    await lock_operation(session, body.operation_id)
    sale = await get_required(session, Sale, identifier)
    shift = None

    if sale.id_turno is not None:
        shift = await get_required(session, CashShift, sale.id_turno, lock=True)

    sale = await get_required(session, Sale, identifier, lock=True)
    digest = fingerprint(
        {
            **body.model_dump(mode="json"),
            "sale": str(sale.sync_id),
            "employee": str(employee.sync_id),
        }
    )

    if sale.estado == "Cancelada":
        if sale.cancel_operation_id != body.operation_id or sale.cancel_hash != digest:
            raise HTTPException(409, "La venta ya está cancelada")

        return sale

    if shift is not None and shift.estado != "Abierta":
        raise HTTPException(
            409, "El turno de esa venta ya cerró; no se puede alterar su corte"
        )

    details = (
        await session.scalars(
            select(SaleDetail).where(SaleDetail.id_venta == identifier)
        )
    ).all()
    quantities = {detail.id_producto: detail.cantidad for detail in details}
    products = (
        await session.scalars(
            select(Product)
            .where(Product.id_producto.in_(quantities))
            .order_by(Product.id_producto)
            .with_for_update()
        )
    ).all()

    for product in products:
        stock = product.stock_actual + quantities[product.id_producto]

        if stock > Decimal("9999999.999"):
            raise HTTPException(409, "La devolución superaría el límite de existencias")

        product.stock_actual = stock

    sale.estado = "Cancelada"
    sale.cancel_operation_id = body.operation_id
    sale.cancel_hash = digest
    sale.cancel_motivo = body.motivo
    sale.cancelado_por = employee.id_empleado
    sale.cancelado_en = datetime.now()
    await session.flush()

    if queue_sync:
        from ..sync.service import enqueue

        await enqueue(
            session,
            "sale.cancelled",
            {
                "sale_sync_id": str(sale.sync_id),
                "employee_sync_id": str(employee.sync_id),
                **body.model_dump(mode="json"),
            },
        )

    return sale


async def receive_cancellation(session, payload):
    from uuid import UUID

    from pydantic import ValidationError

    from .sale_schema import CancelSaleInput

    try:
        sale = await session.scalar(
            select(Sale).where(Sale.sync_id == UUID(payload["sale_sync_id"]))
        )
        employee = await session.scalar(
            select(Employee).where(
                Employee.sync_id == UUID(payload["employee_sync_id"])
            )
        )

        if sale is None or employee is None:
            raise HTTPException(409, "Falta la venta o el empleado en la nube")

        body = CancelSaleInput.model_validate(
            {key: payload[key] for key in CancelSaleInput.model_fields}
        )

        return await cancel_sale(session, sale.id_venta, body, employee)
    except (KeyError, TypeError, ValueError, ValidationError) as exc:
        raise HTTPException(422, "Evento de cancelación inválido") from exc
