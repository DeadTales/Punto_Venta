from fastapi import APIRouter, Depends, Request

from ...core.config.db_config import get_session
from ...core.repository import Repository
from ...core.security import current_user, roles
from ..catalog.catalog_dependencies import should_queue_sync
from ..catalog.catalog_service import delete_record
from .category_model import Category
from .category_schema import CategoryInput, CategoryResponse
from .category_service import save_category

router = APIRouter(
    prefix="/api", tags=["Inventario"], dependencies=[Depends(current_user)]
)
managers = roles("Administrador", "Supervisor")


@router.get("/categories", response_model=list[CategoryResponse])
async def categories(session=Depends(get_session, scope="function")):
    return await Repository(session, Category).list(limit=500)


@router.post(
    "/categories",
    dependencies=[Depends(managers)],
    status_code=201,
    response_model=CategoryResponse,
)
async def create_category(
    body: CategoryInput,
    request: Request,
    session=Depends(get_session, scope="function"),
):
    return await save_category(session, body, queue_sync=should_queue_sync(request))


@router.put(
    "/categories/{identifier}",
    dependencies=[Depends(managers)],
    response_model=CategoryResponse,
)
async def update_category(
    identifier: int,
    body: CategoryInput,
    request: Request,
    session=Depends(get_session, scope="function"),
):
    return await save_category(session, body, identifier, should_queue_sync(request))


@router.delete("/categories/{identifier}", dependencies=[Depends(managers)])
async def delete_category(
    identifier: int, request: Request, session=Depends(get_session, scope="function")
):
    return await delete_record(
        session, Category, identifier, should_queue_sync(request)
    )
