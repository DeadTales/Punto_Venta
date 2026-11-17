from fastapi import HTTPException
from sqlalchemy import func, select

from ...core.security import hash_password
from ..catalog.catalog_repository import get_required
from ..entities import Employee
from ..sale.service import lock_operation


async def save_employee(session, body, actor, identifier=None, queue_sync=False):
    await lock_operation(session, "employee-administration")
    actor = await get_required(session, Employee, actor.id_empleado, lock=True)

    if not actor.activo or actor.rol != "Administrador":
        raise HTTPException(403, "Tu cuenta ya no puede administrar empleados")

    record = (
        await get_required(session, Employee, identifier, lock=True)
        if identifier is not None
        else Employee()
    )

    if identifier == actor.id_empleado and (
        not body.activo or body.rol != "Administrador"
    ):
        raise HTTPException(
            409, "No puedes desactivar tu acceso ni quitarte el rol Administrador"
        )

    if identifier == actor.id_empleado and (
        body.password is not None or body.correo != record.correo
    ):
        raise HTTPException(
            409,
            "Cambia tu correo o contraseña desde Configuración para renovar la sesión",
        )

    if (
        identifier is not None
        and record.rol == "Administrador"
        and record.activo
        and (not body.activo or body.rol != "Administrador")
    ):
        other_admin = await session.scalar(
            select(Employee.id_empleado)
            .where(
                Employee.id_empleado != identifier,
                Employee.rol == "Administrador",
                Employee.activo.is_(True),
            )
            .limit(1)
        )

        if other_admin is None:
            raise HTTPException(409, "Debe permanecer al menos un Administrador activo")

    email_query = select(Employee.id_empleado).where(
        func.lower(Employee.correo) == body.correo
    )

    if identifier is not None:
        email_query = email_query.where(Employee.id_empleado != identifier)

    if await session.scalar(email_query) is not None:
        raise HTTPException(409, "Ya existe un empleado con ese correo")

    from ..people.people_sync_service import person_snapshot, queue_person_change

    before = person_snapshot(record) if identifier is not None else None

    if identifier is None:
        record.token_version = 0
    elif (record.rol, record.activo, record.correo) != (
        body.rol,
        body.activo,
        body.correo,
    ) or body.password:
        record.token_version += 1

    for name, value in body.model_dump(exclude={"password"}).items():
        setattr(record, name, value)

    if body.password is not None:
        record.password_hash = await hash_password(body.password)

    session.add(record)
    await session.flush()

    if queue_sync:
        await queue_person_change(
            session, "employee", record, before, person_snapshot(record)
        )

    return record


async def deactivate_employee(session, identifier, actor, queue_sync=False):
    from shared.people import EmployeeUpdate

    record = await get_required(session, Employee, identifier)
    values = {
        name: getattr(record, name)
        for name in ("nombre", "apellido", "correo", "telefono", "rol")
    }
    await save_employee(
        session, EmployeeUpdate(**values, activo=False), actor, identifier, queue_sync
    )

    return {"deleted": True, "deactivated": True}
