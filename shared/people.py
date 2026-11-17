"""Contratos de clientes, empleados y cambios de credenciales."""

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Password = Annotated[
    str,
    StringConstraints(min_length=12, max_length=72, strip_whitespace=False),
]


class PersonInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=150)
    telefono: str | None = Field(default=None, max_length=20)
    correo: str | None = Field(default=None, max_length=150)

    @field_validator("telefono", "correo", mode="before")
    @classmethod
    def empty_to_none(cls, value):
        return value.strip() or None if isinstance(value, str) else value

    @field_validator("correo")
    @classmethod
    def valid_email(cls, value):
        if value is not None and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Escribe un correo válido")

        return value.lower() if value else None


class ClientInput(PersonInput):
    rfc_o_identificacion_fiscal: str | None = Field(default=None, max_length=50)


class EmployeeUpdate(PersonInput):
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    correo: str = Field(min_length=3, max_length=150)
    rol: Literal["Administrador", "Supervisor", "Cajero"]
    activo: bool = True
    password: Password | None = None

    @field_validator("password")
    @classmethod
    def valid_password_bytes(cls, value):
        if value is not None and len(value.encode("utf-8")) > 72:
            raise ValueError("La contraseña admite hasta 72 bytes UTF-8")

        return value


class EmployeeCreate(EmployeeUpdate):
    password: Password


class PasswordChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: str = Field(min_length=1, max_length=72)
    new_password: Password

    @field_validator("new_password", "current_password")
    @classmethod
    def valid_password_bytes(cls, value):
        return EmployeeUpdate.valid_password_bytes(value)


class EmailChange(PersonInput):
    nombre: str = ""
    correo: str = Field(min_length=3, max_length=150)
    current_password: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(
        min_length=1, max_length=72
    )
