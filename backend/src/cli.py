"""Preparación explícita de bases nuevas; no se ejecuta al iniciar la API."""
import argparse
import asyncio
from getpass import getpass
from uuid import NAMESPACE_URL, uuid5

import bcrypt
from sqlalchemy import select

from .core.config.db_config import Base, Database
from .core.config.settings import Settings
from .modules.entities import Category, Employee, PaymentMethod
from .modules.sync import models  # Registra tablas de sincronización en metadata.


async def prepare(command):
    database = Database(Settings.from_env())
    try:
        if command == "init-db":
            async with database.engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            print("Tablas creadas si no existían. Las bases existentes requieren la migración SQL.")
            return
        password = getpass("Contraseña inicial para admin@pos.local (mínimo 12 caracteres): ")
        if len(password) < 12 or len(password.encode()) > 72:
            raise ValueError("Usa de 12 a 72 bytes para la contraseña")
        async with database.session() as session:
            if not await session.scalar(select(Category).where(Category.nombre == "General")):
                session.add(Category(nombre="General", sync_id=uuid5(NAMESPACE_URL, "pos:category:general")))
            names = ("Efectivo", "Tarjeta Débito", "Tarjeta Crédito", "Transferencia")
            for name in names:
                if not await session.scalar(select(PaymentMethod).where(PaymentMethod.nombre == name)):
                    session.add(PaymentMethod(nombre=name))
            if await session.scalar(select(Employee).where(Employee.correo == "admin@pos.local")):
                raise ValueError("El administrador ya existe; no se modificó su contraseña")
            session.add(Employee(nombre="Administrador", apellido="Principal", correo="admin@pos.local", rol="Administrador",
                password_hash=bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
                sync_id=uuid5(NAMESPACE_URL, "pos:employee:admin@pos.local")))
        print("Catálogos y administrador inicial creados. No se generaron ventas ni productos ficticios.")
    finally:
        await database.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["init-db", "bootstrap"])
    asyncio.run(prepare(parser.parse_args().command))
