from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_, select

from ...core.config.db_config import get_session
from ...core.security import current_user, roles
from ..catalog.catalog_dependencies import should_queue_sync
from ..catalog.catalog_repository import get_required
from ..entities import Client
from .client_schema import ClientInput
from .client_service import delete_client, save_client

router = APIRouter(
    prefix="/api/clients", tags=["Clientes"], dependencies=[Depends(current_user)]
)


@router.get("")
async def clients(
    q: str = "",
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session=Depends(get_session, scope="function"),
):
    statement = select(Client).order_by(Client.nombre, Client.id_cliente)

    if q.strip():
        statement = statement.where(
            or_(
                Client.nombre.icontains(q.strip(), autoescape=True),
                Client.correo.icontains(q.strip(), autoescape=True),
                Client.rfc_o_identificacion_fiscal.icontains(
                    q.strip(), autoescape=True
                ),
            )
        )

    return list((await session.scalars(statement.limit(limit).offset(offset))).all())


@router.get("/{identifier}")
async def client(identifier: int, session=Depends(get_session, scope="function")):
    return await get_required(session, Client, identifier)


@router.post("", status_code=201)
async def create_client(
    body: ClientInput, request: Request, session=Depends(get_session, scope="function")
):
    return await save_client(session, body, queue_sync=should_queue_sync(request))


@router.put("/{identifier}")
async def update_client(
    identifier: int,
    body: ClientInput,
    request: Request,
    session=Depends(get_session, scope="function"),
):
    return await save_client(session, body, identifier, should_queue_sync(request))


@router.delete(
    "/{identifier}", dependencies=[Depends(roles("Administrador", "Supervisor"))]
)
async def remove_client(
    identifier: int, request: Request, session=Depends(get_session, scope="function")
):
    return await delete_client(session, identifier, should_queue_sync(request))
