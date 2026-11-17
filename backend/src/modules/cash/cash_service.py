from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select

from ..catalog.catalog_repository import get_required
from ..entities import PaymentMethod, Sale
from ..sale.service import fingerprint, lock_operation
from .cash_model import CashShift


async def current_shift(session, employee_id, lock=False):
    statement = select(CashShift).where(
        CashShift.id_empleado == employee_id, CashShift.estado == "Abierta"
    )

    if lock:
        statement = statement.with_for_update()

    return await session.scalar(statement)


async def expected_cash(session, shift):
    cash_sales = await session.scalar(
        select(func.coalesce(func.sum(Sale.total), 0))
        .join(PaymentMethod, Sale.id_metodo_pago == PaymentMethod.id_metodo_pago)
        .where(
            Sale.id_turno == shift.id_turno,
            Sale.estado == "Completada",
            PaymentMethod.nombre == "Efectivo",
        )
    )

    return shift.fondo_inicial + Decimal(cash_sales)


async def shift_response(session, shift):
    if shift is None:
        return None

    fields = (
        "id_turno",
        "operation_id",
        "id_empleado",
        "estado",
        "apertura",
        "cierre",
        "fondo_inicial",
        "efectivo_contado",
        "diferencia",
        "notas",
    )
    response = {name: getattr(shift, name) for name in fields}
    response["efectivo_esperado"] = (
        await expected_cash(session, shift)
        if shift.estado == "Abierta"
        else shift.efectivo_esperado
    )

    return response


async def open_shift(session, body, employee):
    await lock_operation(session, body.operation_id)
    await lock_operation(session, "cash-employee:" + str(employee.sync_id))
    digest = fingerprint(
        {**body.model_dump(mode="json"), "employee": str(employee.sync_id)}
    )
    existing = await session.scalar(
        select(CashShift).where(CashShift.operation_id == body.operation_id)
    )

    if existing is not None:
        if existing.request_hash != digest:
            raise HTTPException(
                409, "La operación de apertura ya se usó con otros datos"
            )

        return existing

    if await current_shift(session, employee.id_empleado) is not None:
        raise HTTPException(409, "Ya tienes un turno abierto")

    shift = CashShift(
        operation_id=body.operation_id,
        request_hash=digest,
        id_empleado=employee.id_empleado,
        fondo_inicial=body.fondo_inicial,
        estado="Abierta",
    )
    session.add(shift)
    await session.flush()

    return shift


async def close_shift(session, identifier, body, employee):
    await lock_operation(session, body.operation_id)
    shift = await get_required(session, CashShift, identifier, lock=True)

    if shift.id_empleado != employee.id_empleado and employee.rol not in {
        "Administrador",
        "Supervisor",
    }:
        raise HTTPException(403, "No puedes cerrar la caja de otro empleado")

    digest = fingerprint(
        {
            **body.model_dump(mode="json"),
            "employee": str(employee.sync_id),
            "shift": identifier,
        }
    )

    if shift.estado == "Cerrada":
        if shift.close_operation_id != body.operation_id or shift.close_hash != digest:
            raise HTTPException(409, "El turno ya está cerrado")

        return shift

    shift.efectivo_esperado = await expected_cash(session, shift)
    shift.efectivo_contado = body.efectivo_contado
    shift.diferencia = body.efectivo_contado - shift.efectivo_esperado
    shift.notas = body.notas
    shift.estado = "Cerrada"
    shift.cierre = datetime.now()
    shift.close_operation_id = body.operation_id
    shift.close_hash = digest
    await session.flush()

    return shift
