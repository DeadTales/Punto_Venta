from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

from shared.inventory_excel import MAX_BYTES, template_bytes
from ...core.config.db_config import get_session
from ...core.repository import Repository
from ...core.security import current_user, roles
from .models import Category
from .repository import ProductRepository
from .service import import_inventory, validate_import
from ..sale.service import lock_operation

router = APIRouter(prefix="/api", tags=["Inventario"], dependencies=[Depends(current_user)])
managers = roles("Administrador", "Supervisor")


@router.get("/products")
async def products(q: str = "", low_stock: bool = False, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), session=Depends(get_session, scope="function")):
    return await ProductRepository(session).search(q, low_stock, limit, offset)


@router.get("/categories")
async def categories(session=Depends(get_session, scope="function")):
    return await Repository(session, Category).list(limit=500)


class CategoryInput(BaseModel):
    nombre: str = Field(min_length=1, max_length=100, pattern=r".*\S.*")
    descripcion: str | None = None


@router.post("/categories", dependencies=[Depends(managers)], status_code=201)
async def create_category(body: CategoryInput, session=Depends(get_session, scope="function")):
    name = body.nombre.strip()
    await lock_operation(session, "category-name:" + name)
    if await session.scalar(select(Category.id_categoria).where(Category.nombre == name)):
        raise HTTPException(409, "Ya existe una categoría con ese nombre")
    return await Repository(session, Category).add(nombre=name, descripcion=body.descripcion)


@router.get("/inventory/template")
async def template():
    return StreamingResponse(BytesIO(template_bytes()), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="plantilla_inventario.xlsx"'})


async def read_excel(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(422, "Selecciona un archivo .xlsx de la plantilla")
    data = await file.read(MAX_BYTES + 1)
    await file.close()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "El archivo supera 5 MB")
    return data


@router.post("/inventory/preview", dependencies=[Depends(managers)])
async def preview(file: UploadFile = File(...), session=Depends(get_session, scope="function")):
    return (await validate_import(session, await read_excel(file))).json()


@router.post("/inventory/import", dependencies=[Depends(managers)], status_code=201)
async def confirm(request: Request, file: UploadFile = File(...), session=Depends(get_session, scope="function")):
    result = await import_inventory(session, await read_excel(file), request.app.state.settings.database_mode == "local")
    if result.errors:
        raise HTTPException(422, result.json())
    return {"imported": len(result.rows), "queued": request.app.state.settings.database_mode == "local"}
