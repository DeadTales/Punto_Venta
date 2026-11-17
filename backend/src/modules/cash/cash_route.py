from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from ...core.config.db_config import get_session
from ...core.security import current_user
from .cash_model import CashShift
from .cash_schema import CloseShiftInput, OpenShiftInput
from .cash_service import close_shift, current_shift, open_shift, shift_response

router = APIRouter(
    prefix="/api/shifts", tags=["Caja"], dependencies=[Depends(current_user)]
)


@router.get("/current")
async def current(
    user=Depends(current_user), session=Depends(get_session, scope="function")
):
    return await shift_response(session, await current_shift(session, user.id_empleado))


@router.get("")
async def shifts(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user=Depends(current_user),
    session=Depends(get_session, scope="function"),
):
    statement = select(CashShift).order_by(
        CashShift.apertura.desc(), CashShift.id_turno.desc()
    )

    if user.rol == "Cajero":
        statement = statement.where(CashShift.id_empleado == user.id_empleado)

    records = (await session.scalars(statement.limit(limit).offset(offset))).all()

    return [await shift_response(session, record) for record in records]


@router.post("/open", status_code=201)
async def open_cash(
    body: OpenShiftInput,
    user=Depends(current_user),
    session=Depends(get_session, scope="function"),
):
    return await shift_response(session, await open_shift(session, body, user))


@router.post("/{identifier}/close")
async def close_cash(
    identifier: int,
    body: CloseShiftInput,
    user=Depends(current_user),
    session=Depends(get_session, scope="function"),
):
    return await shift_response(
        session, await close_shift(session, identifier, body, user)
    )
