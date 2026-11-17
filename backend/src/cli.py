"""Preparación explícita de bases nuevas; no se ejecuta al iniciar la API."""

import argparse
import asyncio
from getpass import getpass
from uuid import NAMESPACE_URL, uuid5

import bcrypt
from sqlalchemy import select

from .core.config.db_config import Base, Database
from .core.config.settings import Settings
from .core.migrations import migrate
from .core.security import hash_password
from .modules.cash import cash_model  # noqa: F401
from .modules.entities import Category, Employee, PaymentMethod
from .modules.inventory import inventory_model  # noqa: F401


async def prepare(command, email=None):
    database = Database(Settings.from_env())

    try:
        if command == "migrate":
            applied = await migrate(database)
            print("Migraciones verificadas y aplicadas en una sola transacción:")

            for filename in applied:
                print(filename)

            return

        if command == "reset-password":
            if not email:
                raise ValueError("Indica --email con la cuenta que deseas recuperar")

            password = getpass("Nueva contraseña (mínimo 12 caracteres): ")
            password_hash = await hash_password(password)

            async with database.session() as session:
                from sqlalchemy import func

                employee = await session.scalar(
                    select(Employee)
                    .where(func.lower(Employee.correo) == email.strip().lower())
                    .with_for_update()
                )

                if employee is None:
                    raise ValueError("No existe una cuenta con ese correo")

                employee.password_hash = password_hash
                employee.token_version += 1

            print("Contraseña actualizada. Las sesiones anteriores quedaron revocadas.")

            return

        if command == "init-db":
            async with database.engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)

            print(
                "Tablas creadas si no existían. Las bases existentes requieren la migración SQL."
            )

            return

        password = getpass(
            "Contraseña inicial para admin@pos.local (mínimo 12 caracteres): "
        )

        if len(password) < 12 or len(password.encode()) > 72:
            raise ValueError("Usa de 12 a 72 bytes para la contraseña")

        async with database.session() as session:
            if not await session.scalar(
                select(Category).where(Category.nombre == "General")
            ):
                session.add(
                    Category(
                        nombre="General",
                        sync_id=uuid5(NAMESPACE_URL, "pos:category:general"),
                    )
                )

            names = ("Efectivo", "Tarjeta Débito", "Tarjeta Crédito", "Transferencia")

            for name in names:
                if not await session.scalar(
                    select(PaymentMethod).where(PaymentMethod.nombre == name)
                ):
                    session.add(PaymentMethod(nombre=name))

            if await session.scalar(
                select(Employee).where(Employee.correo == "admin@pos.local")
            ):
                raise ValueError(
                    "El administrador ya existe; no se modificó su contraseña"
                )

            session.add(
                Employee(
                    nombre="Administrador",
                    apellido="Principal",
                    correo="admin@pos.local",
                    rol="Administrador",
                    password_hash=bcrypt.hashpw(
                        password.encode(), bcrypt.gensalt()
                    ).decode(),
                    sync_id=uuid5(NAMESPACE_URL, "pos:employee:admin@pos.local"),
                )
            )

        print(
            "Catálogos y administrador inicial creados. No se generaron ventas ni productos ficticios."
        )
    finally:
        await database.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=["init-db", "bootstrap", "migrate", "reset-password"]
    )
    parser.add_argument("--email", help="Cuenta para reset-password")
    arguments = parser.parse_args()
    asyncio.run(prepare(arguments.command, arguments.email))
