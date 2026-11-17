from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ...core.config.db_config import get_session
from ...core.security import current_user, roles
from ..catalog.catalog_dependencies import should_queue_sync
from ..catalog.catalog_repository import get_required
from ..catalog.catalog_service import delete_record
from .product_model import Product
from .product_repository import ProductRepository
from .product_schema import ProductCreate, ProductResponse, ProductUpdate
from .product_service import save_product

router = APIRouter(
    prefix="/api", tags=["Inventario"], dependencies=[Depends(current_user)]
)
managers = roles("Administrador", "Supervisor")


@router.get("/products", response_model=list[ProductResponse])
async def products(
    q: str = "",
    low_stock: bool = False,
    category_id: int | None = Query(None, gt=0),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session=Depends(get_session, scope="function"),
):
    return await ProductRepository(session).search(
        q.strip(), low_stock, limit, offset, category_id
    )


@router.get("/products/low-stock", response_model=list[ProductResponse])
async def low_stock(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session=Depends(get_session, scope="function"),
):
    return await ProductRepository(session).search(
        low_stock=True, limit=limit, offset=offset
    )


@router.get("/products/barcode/{code:path}", response_model=ProductResponse)
async def barcode(code: str, session=Depends(get_session, scope="function")):
    product = await ProductRepository(session).get_by_barcode(code.strip())

    if product is None:
        raise HTTPException(404, "No existe un producto con ese código de barras")

    return product


@router.get("/products/{identifier}", response_model=ProductResponse)
async def product(identifier: int, session=Depends(get_session, scope="function")):
    return await get_required(session, Product, identifier)


@router.post(
    "/products",
    dependencies=[Depends(managers)],
    status_code=201,
    response_model=ProductResponse,
)
async def create_product(
    body: ProductCreate,
    request: Request,
    session=Depends(get_session, scope="function"),
):
    return await save_product(session, body, queue_sync=should_queue_sync(request))


@router.put(
    "/products/{identifier}",
    dependencies=[Depends(managers)],
    response_model=ProductResponse,
)
async def update_product(
    identifier: int,
    body: ProductUpdate,
    request: Request,
    session=Depends(get_session, scope="function"),
):
    return await save_product(session, body, identifier, should_queue_sync(request))


@router.delete("/products/{identifier}", dependencies=[Depends(managers)])
async def delete_product(
    identifier: int, request: Request, session=Depends(get_session, scope="function")
):
    return await delete_record(session, Product, identifier, should_queue_sync(request))
