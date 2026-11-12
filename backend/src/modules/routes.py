import hmac
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import func, select, text

from ..core.config.db_config import get_session
from ..core.repository import Repository
from ..core.security import Credentials, authenticate, current_user, issue_token, public_employee, roles
from .entities import Client, Employee, PaymentMethod, Sale
from .sale.schemas import SaleInput
from .sale.service import create_sale
from .sync.models import OutboxEvent
from .sync.service import EventInput, push_pending, receive_event

router = APIRouter(prefix="/api")
manager = roles("Administrador", "Supervisor")


@router.get("/health", tags=["Sistema"])
async def health(request: Request, session=Depends(get_session, scope="function")):
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database_mode": request.app.state.settings.database_mode}


@router.post("/auth/login", tags=["Sesión"])
async def login(body: Credentials, request: Request, session=Depends(get_session, scope="function")):
    user = await authenticate(session, body)
    return {"access_token": issue_token(user, request.app.state.settings.jwt_secret),
            "token_type": "bearer", "user": public_employee(user)}


@router.get("/auth/me", tags=["Sesión"])
async def me(user=Depends(current_user)):
    return public_employee(user)


@router.get("/clients", dependencies=[Depends(current_user)], tags=["Clientes"])
async def clients(session=Depends(get_session, scope="function")):
    return await Repository(session, Client).list(limit=500)


@router.get("/employees", dependencies=[Depends(roles("Administrador"))], tags=["Usuarios"])
async def employees(session=Depends(get_session, scope="function")):
    return [public_employee(user) for user in await Repository(session, Employee).list(limit=500)]


@router.get("/payment-methods", dependencies=[Depends(current_user)], tags=["Ventas"])
async def payment_methods(session=Depends(get_session, scope="function")):
    return await Repository(session, PaymentMethod).list()


@router.get("/sales", dependencies=[Depends(current_user)], tags=["Ventas"])
async def sales(session=Depends(get_session, scope="function")):
    return list((await session.scalars(select(Sale).order_by(Sale.fecha_hora.desc(), Sale.id_venta.desc()).limit(500))).all())


@router.post("/sales", status_code=201, tags=["Ventas"])
async def sale(body: SaleInput, request: Request, user=Depends(current_user), session=Depends(get_session, scope="function")):
    record = await create_sale(session, body, user, request.app.state.settings.database_mode == "local")
    return {"id_venta": record.id_venta, "sync_id": str(record.sync_id), "total": str(record.total), "estado": record.estado}


@router.get("/sync/status", dependencies=[Depends(current_user)], tags=["Sincronización"])
async def sync_status(request: Request, session=Depends(get_session, scope="function")):
    counts = dict((await session.execute(select(OutboxEvent.status, func.count()).group_by(OutboxEvent.status))).all())
    blocked = (await session.scalars(select(OutboxEvent).where(OutboxEvent.status == "conflict").order_by(OutboxEvent.id).limit(20))).all()
    settings = request.app.state.settings
    return {"database_mode": settings.database_mode, "configured": bool(settings.sync_url and settings.sync_key),
            "counts": counts, "conflicts": [{"event_id": str(e.event_id), "error": e.last_error} for e in blocked]}


@router.post("/sync/push", dependencies=[Depends(manager)], tags=["Sincronización"])
async def sync_push(request: Request):
    return await push_pending(request.app.state.database, request.app.state.settings)


@router.post("/sync/outbox/{event_id}/retry", dependencies=[Depends(manager)], tags=["Sincronización"])
async def retry_event(event_id: UUID, request: Request, session=Depends(get_session, scope="function")):
    if request.app.state.settings.database_mode != "local":
        raise HTTPException(409, "La cola de salida pertenece al backend local")
    event = await session.scalar(select(OutboxEvent).where(OutboxEvent.event_id == event_id).with_for_update())
    if not event:
        raise HTTPException(404, "Evento no encontrado")
    if event.status == "sent":
        raise HTTPException(409, "El evento ya está confirmado por la nube")
    event.status, event.last_error = "pending", None
    return {"status": "pending", "event_id": str(event.event_id)}


@router.post("/sync/events", tags=["Sincronización"])
async def sync_receive(body: EventInput, request: Request, x_sync_key: Annotated[str | None, Header()] = None, session=Depends(get_session, scope="function")):
    settings = request.app.state.settings
    if settings.database_mode != "cloud" or not settings.sync_key:
        raise HTTPException(503, "Este servidor no recibe eventos de sincronización")
    if not x_sync_key or not hmac.compare_digest(x_sync_key, settings.sync_key):
        raise HTTPException(401, "Credencial de sincronización incorrecta")
    return await receive_event(session, body)
