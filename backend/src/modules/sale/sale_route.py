from datetime import date, datetime, time, timedelta
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from shared.receipts import receipt_pdf

from ...core.config.db_config import get_session
from ...core.security import current_user, roles
from ..catalog.catalog_dependencies import should_queue_sync
from ..entities import Sale
from .sale_schema import CancelSaleInput, SaleInput
from .sale_service import cancel_sale, sale_detail
from .service import create_sale

router = APIRouter(
    prefix="/api/sales", tags=["Ventas"], dependencies=[Depends(current_user)]
)


@router.get("")
async def sales(
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session=Depends(get_session, scope="function"),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "El inicio debe ser anterior al final del periodo")

    statement = select(Sale).order_by(Sale.fecha_hora.desc(), Sale.id_venta.desc())

    if date_from:
        statement = statement.where(
            Sale.fecha_hora >= datetime.combine(date_from, time.min)
        )

    if date_to:
        statement = statement.where(
            Sale.fecha_hora < datetime.combine(date_to + timedelta(days=1), time.min)
        )

    records = (await session.scalars(statement.limit(limit).offset(offset))).all()
    fields = (
        "id_venta",
        "id_cliente",
        "id_empleado",
        "id_metodo_pago",
        "id_turno",
        "fecha_hora",
        "total",
        "estado",
        "subtotal",
        "impuesto",
        "tasa_impuesto",
    )

    return [{name: getattr(record, name) for name in fields} for record in records]


@router.post("", status_code=201)
async def register_sale(
    body: SaleInput,
    request: Request,
    user=Depends(current_user),
    session=Depends(get_session, scope="function"),
):
    sale = await create_sale(
        session,
        body,
        user,
        should_queue_sync(request),
        request.app.state.settings.tax_rate,
        require_shift=True,
    )

    return {
        "id_venta": sale.id_venta,
        "sync_id": str(sale.sync_id),
        "total": str(sale.total),
        "subtotal": str(sale.subtotal),
        "impuesto": str(sale.impuesto),
        "estado": sale.estado,
    }


@router.get("/{identifier}")
async def detail(identifier: int, session=Depends(get_session, scope="function")):
    return await sale_detail(session, identifier)


@router.post("/{identifier}/cancel")
async def cancel(
    identifier: int,
    body: CancelSaleInput,
    request: Request,
    user=Depends(roles("Administrador", "Supervisor")),
    session=Depends(get_session, scope="function"),
):
    await cancel_sale(session, identifier, body, user, should_queue_sync(request))

    return await sale_detail(session, identifier)


@router.get("/{identifier}/receipt")
async def receipt(
    identifier: int, request: Request, session=Depends(get_session, scope="function")
):
    sale = await sale_detail(session, identifier)
    pdf = receipt_pdf(sale, request.app.state.settings.business_name)

    return StreamingResponse(
        BytesIO(pdf),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="ticket_{identifier}.pdf"'
        },
    )
