from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select

from shared.people import EmailChange, PasswordChange

from ...core.config.db_config import get_session
from ...core.security import (
    check_password,
    current_user,
    hash_password,
    issue_token,
    public_employee,
)
from ..catalog.catalog_dependencies import should_queue_sync
from ..catalog.catalog_repository import get_required
from ..entities import Employee
from ..people.people_sync_service import person_snapshot, queue_person_change
from ..sale.service import lock_operation

router = APIRouter(prefix="/api/auth", tags=["Sesión"])


async def _save_account_change(session, user, before, request):
    user.token_version += 1
    await session.flush()

    if should_queue_sync(request):
        await queue_person_change(
            session, "employee", user, before, person_snapshot(user)
        )

    return {
        "access_token": issue_token(user, request.app.state.settings.jwt_secret),
        "token_type": "bearer",
        "user": public_employee(user),
    }


@router.put("/password")
async def change_password(
    body: PasswordChange,
    request: Request,
    user=Depends(current_user),
    session=Depends(get_session, scope="function"),
):
    user = await get_required(session, Employee, user.id_empleado, lock=True)

    if not await check_password(body.current_password, user.password_hash):
        raise HTTPException(403, "La contraseña actual es incorrecta")

    before = person_snapshot(user)
    user.password_hash = await hash_password(body.new_password)

    return await _save_account_change(session, user, before, request)


@router.put("/email")
async def change_email(
    body: EmailChange,
    request: Request,
    user=Depends(current_user),
    session=Depends(get_session, scope="function"),
):
    await lock_operation(session, "employee-administration")
    user = await get_required(session, Employee, user.id_empleado, lock=True)

    if not await check_password(body.current_password, user.password_hash):
        raise HTTPException(403, "La contraseña actual es incorrecta")

    duplicate = await session.scalar(
        select(Employee.id_empleado).where(
            func.lower(Employee.correo) == body.correo,
            Employee.id_empleado != user.id_empleado,
        )
    )

    if duplicate is not None:
        raise HTTPException(409, "Ese correo ya está registrado")

    before = person_snapshot(user)
    user.correo = body.correo

    return await _save_account_change(session, user, before, request)


@router.post("/logout")
async def logout(
    request: Request,
    user=Depends(current_user),
    session=Depends(get_session, scope="function"),
):
    user = await get_required(session, Employee, user.id_empleado, lock=True)
    before = person_snapshot(user)
    user.token_version += 1
    await session.flush()

    if should_queue_sync(request):
        await queue_person_change(
            session, "employee", user, before, person_snapshot(user)
        )

    return {"logged_out": True}
