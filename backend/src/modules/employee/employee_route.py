from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_, select

from ...core.config.db_config import get_session
from ...core.security import public_employee, roles
from ..catalog.catalog_dependencies import should_queue_sync
from ..catalog.catalog_repository import get_required
from ..entities import Employee
from .employee_schema import EmployeeCreate, EmployeeUpdate
from .employee_service import deactivate_employee, save_employee

administrator = roles("Administrador")
router = APIRouter(
    prefix="/api/employees", tags=["Empleados"], dependencies=[Depends(administrator)]
)


@router.get("")
async def employees(
    q: str = "",
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session=Depends(get_session, scope="function"),
):
    statement = select(Employee).order_by(Employee.nombre, Employee.id_empleado)

    if q.strip():
        statement = statement.where(
            or_(
                Employee.nombre.icontains(q.strip(), autoescape=True),
                Employee.apellido.icontains(q.strip(), autoescape=True),
                Employee.correo.icontains(q.strip(), autoescape=True),
            )
        )

    return [
        public_employee(user)
        for user in (await session.scalars(statement.limit(limit).offset(offset))).all()
    ]


@router.get("/{identifier}")
async def employee(identifier: int, session=Depends(get_session, scope="function")):
    return public_employee(await get_required(session, Employee, identifier))


@router.post("", status_code=201)
async def create_employee(
    body: EmployeeCreate,
    request: Request,
    actor=Depends(administrator),
    session=Depends(get_session, scope="function"),
):
    return public_employee(
        await save_employee(session, body, actor, queue_sync=should_queue_sync(request))
    )


@router.put("/{identifier}")
async def update_employee(
    identifier: int,
    body: EmployeeUpdate,
    request: Request,
    actor=Depends(administrator),
    session=Depends(get_session, scope="function"),
):
    return public_employee(
        await save_employee(
            session, body, actor, identifier, should_queue_sync(request)
        )
    )


@router.delete("/{identifier}")
async def delete_employee(
    identifier: int,
    request: Request,
    actor=Depends(administrator),
    session=Depends(get_session, scope="function"),
):
    return await deactivate_employee(
        session, identifier, actor, should_queue_sync(request)
    )
