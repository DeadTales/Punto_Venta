from uuid import UUID

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select

from shared.people import ClientInput, EmployeeUpdate

from ..entities import Client, Employee, Sale
from ..sale.service import lock_operation

CLIENT_FIELDS = ("nombre", "telefono", "correo", "rfc_o_identificacion_fiscal")
EMPLOYEE_FIELDS = (
    "nombre",
    "apellido",
    "correo",
    "telefono",
    "rol",
    "activo",
    "token_version",
    "password_hash",
)


def person_snapshot(record):
    fields = CLIENT_FIELDS if isinstance(record, Client) else EMPLOYEE_FIELDS

    return {name: getattr(record, name) for name in fields}


async def queue_person_change(session, entity, record, before, after):
    from ..sync.service import enqueue

    await enqueue(
        session,
        "people.changed",
        {
            "entity": entity,
            "sync_id": str(record.sync_id),
            "before": before,
            "after": after,
        },
    )


async def receive_person(session, payload):
    try:
        model = {"client": Client, "employee": Employee}[payload["entity"]]
        sync_id = UUID(payload["sync_id"])
        before, after = payload["before"], payload["after"]
        await lock_operation(
            session,
            "employee-administration"
            if model is Employee
            else "client:" + str(sync_id),
        )
        record = await session.scalar(
            select(model).where(model.sync_id == sync_id).with_for_update()
        )

        if (
            before is None
            and record is not None
            or before is not None
            and (record is None or person_snapshot(record) != before)
        ):
            raise HTTPException(
                409, "Los datos maestros cambiaron en la nube; concilia el registro"
            )

        if after is None:
            if model is Employee or record is None:
                raise HTTPException(
                    422, "La baja de empleados debe ser una desactivación"
                )

            if await session.scalar(
                select(Sale.id_venta)
                .where(Sale.id_cliente == record.id_cliente)
                .limit(1)
            ):
                raise HTTPException(409, "El cliente tiene ventas en la nube")

            await session.delete(record)

            return

        values = dict(after)

        if model is Employee:
            expected = set(EMPLOYEE_FIELDS)

            if (
                set(values) != expected
                or not isinstance(values["token_version"], int)
                or values["token_version"] < 0
            ):
                raise ValueError

            password_hash = values.pop("password_hash")
            version = values.pop("token_version")
            import re

            if not re.fullmatch(r"\$2[aby]\$\d\d\$[./A-Za-z0-9]{53}", password_hash):
                raise ValueError

            values = EmployeeUpdate.model_validate(values).model_dump(
                exclude={"password"}
            )
            values.update(password_hash=password_hash, token_version=version)
        else:
            values = ClientInput.model_validate(values).model_dump()

        if record is None:
            record = model(sync_id=sync_id)
            session.add(record)

        for name, value in values.items():
            setattr(record, name, value)

        await session.flush()
    except (KeyError, ValueError, TypeError, ValidationError) as exc:
        raise HTTPException(422, "Evento de datos maestros inválido") from exc
