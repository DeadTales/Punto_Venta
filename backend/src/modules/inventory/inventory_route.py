from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse

from shared.inventory_excel import MAX_BYTES, template_bytes

from ...core.config.db_config import get_session
from ...core.security import current_user, roles
from ..catalog.catalog_dependencies import should_queue_sync
from ..catalog.catalog_repository import get_required
from ..product.product_model import Product
from .inventory_import_service import import_inventory, validate_import
from .inventory_repository import InventoryRepository
from .inventory_schema import StockAdjustmentInput, stock_adjustment_response
from .inventory_service import adjust_stock

router = APIRouter(
    prefix="/api", tags=["Inventario"], dependencies=[Depends(current_user)]
)
managers = roles("Administrador", "Supervisor")


@router.post("/products/{identifier}/stock-adjustments", status_code=201)
async def stock_adjustment(
    identifier: int,
    body: StockAdjustmentInput,
    request: Request,
    user=Depends(managers),
    session=Depends(get_session, scope="function"),
):
    record = await adjust_stock(
        session, identifier, body, user, should_queue_sync(request)
    )

    return stock_adjustment_response(record)


@router.get("/products/{identifier}/stock-adjustments")
async def adjustments(
    identifier: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session=Depends(get_session, scope="function"),
):
    await get_required(session, Product, identifier)
    records = await InventoryRepository(session).list_adjustments(
        identifier, limit, offset
    )

    return [stock_adjustment_response(record) for record in records]


@router.get("/inventory/template")
async def template():
    return StreamingResponse(
        BytesIO(template_bytes()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="plantilla_inventario.xlsx"'
        },
    )


async def read_excel(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(422, "Selecciona un archivo .xlsx de la plantilla")

    data = await file.read(MAX_BYTES + 1)
    await file.close()

    if len(data) > MAX_BYTES:
        raise HTTPException(413, "El archivo supera 5 MB")

    return data


@router.post("/inventory/preview", dependencies=[Depends(managers)])
async def preview(
    file: UploadFile = File(...), session=Depends(get_session, scope="function")
):
    return (await validate_import(session, await read_excel(file))).json()


@router.post("/inventory/import", dependencies=[Depends(managers)], status_code=201)
async def confirm(
    request: Request,
    file: UploadFile = File(...),
    session=Depends(get_session, scope="function"),
):
    result = await import_inventory(
        session,
        await read_excel(file),
        request.app.state.settings.database_mode == "local",
    )

    if result.errors:
        raise HTTPException(422, result.json())

    return {
        "imported": len(result.rows),
        "queued": request.app.state.settings.database_mode == "local",
    }
