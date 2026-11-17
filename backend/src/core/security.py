import asyncio
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select

from ..modules.entities import Employee
from .config.db_config import get_session

bearer = HTTPBearer(auto_error=False)


class Credentials(BaseModel):
    correo: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=1, max_length=72)


def public_employee(user):
    return {
        k: getattr(user, k)
        for k in (
            "id_empleado",
            "nombre",
            "apellido",
            "correo",
            "rol",
            "telefono",
            "activo",
        )
    }


def issue_token(user, secret):
    return jwt.encode(
        {
            "sub": str(user.sync_id),
            "ver": user.token_version,
            "exp": datetime.now(timezone.utc) + timedelta(hours=8),
        },
        secret,
        algorithm="HS256",
    )


async def hash_password(password):
    if not 12 <= len(password) or len(password.encode()) > 72:
        raise HTTPException(
            422, "La contraseña debe tener al menos 12 caracteres y hasta 72 bytes"
        )

    return (
        await asyncio.to_thread(bcrypt.hashpw, password.encode(), bcrypt.gensalt())
    ).decode()


async def check_password(password, password_hash):
    try:
        return await asyncio.to_thread(
            bcrypt.checkpw, password.encode(), password_hash.encode()
        )
    except ValueError:
        return False


async def authenticate(session, credentials):
    from sqlalchemy import func

    user = await session.scalar(
        select(Employee).where(
            func.lower(Employee.correo) == credentials.correo.strip().lower()
        )
    )
    valid = (
        user
        and user.activo
        and await check_password(credentials.password, user.password_hash)
    )

    if not valid:
        raise HTTPException(401, "Correo o contraseña incorrectos")

    return user


async def current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session=Depends(get_session, scope="function"),
):
    try:
        payload = jwt.decode(
            credentials.credentials if credentials else "",
            request.app.state.settings.jwt_secret,
            algorithms=["HS256"],
        )
        from uuid import UUID

        user = await session.scalar(
            select(Employee).where(Employee.sync_id == UUID(payload["sub"]))
        )
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, "Inicia sesión para continuar") from None

    if user is None or not user.activo or payload.get("ver", 0) != user.token_version:
        raise HTTPException(401, "La sesión ya no es válida")

    return user


def roles(*allowed):
    async def check(user=Depends(current_user)):
        if user.rol not in allowed:
            raise HTTPException(403, "Tu rol no permite esta operación")

        return user

    return check
