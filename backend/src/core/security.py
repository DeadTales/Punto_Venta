from datetime import datetime, timedelta, timezone
from typing import Annotated
import asyncio

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select

from .config.db_config import get_session
from ..modules.entities import Employee

bearer = HTTPBearer(auto_error=False)


class Credentials(BaseModel):
    correo: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=1, max_length=72)


def public_employee(user):
    return {k: getattr(user, k) for k in (
        "id_empleado", "nombre", "apellido", "correo", "rol", "telefono"
    )}


def issue_token(user, secret):
    return jwt.encode({"sub": str(user.sync_id), "exp": datetime.now(timezone.utc) + timedelta(hours=8)}, secret, algorithm="HS256")


async def authenticate(session, credentials):
    user = await session.scalar(select(Employee).where(Employee.correo == credentials.correo.strip()))
    try:
        valid = user and await asyncio.to_thread(bcrypt.checkpw, credentials.password.encode(), user.password_hash.encode())
    except ValueError:
        valid = False
    if not valid:
        raise HTTPException(401, "Correo o contraseña incorrectos")
    return user


async def current_user(request: Request, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)], session=Depends(get_session, scope="function")):
    try:
        payload = jwt.decode(credentials.credentials if credentials else "", request.app.state.settings.jwt_secret, algorithms=["HS256"])
        from uuid import UUID
        user = await session.scalar(select(Employee).where(Employee.sync_id == UUID(payload["sub"])))
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, "Inicia sesión para continuar") from None
    if user is None:
        raise HTTPException(401, "La sesión ya no es válida")
    return user


def roles(*allowed):
    async def check(user=Depends(current_user)):
        if user.rol not in allowed:
            raise HTTPException(403, "Tu rol no permite esta operación")
        return user
    return check
