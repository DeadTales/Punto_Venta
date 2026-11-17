"""Migraciones explícitas y atómicas; el arranque de la API no modifica tablas."""

from pathlib import Path

from sqlalchemy import text

MIGRATIONS = (
    "db/schema/01_tablas_iniciales.sql",
    "db/migration/04_conexion_y_sincronizacion.sql",
    "db/migration/05_ajustes_inventario.sql",
    "db/migration/06_operacion_completa.sql",
)


async def migrate(database):
    root = Path(__file__).resolve().parents[3]

    async with database.engine.begin() as connection:
        await connection.execute(text("SELECT pg_advisory_xact_lock(748201640)"))
        raw_connection = await connection.get_raw_connection()
        driver = raw_connection.driver_connection

        for relative in MIGRATIONS:
            script = (root / relative).read_text(encoding="utf-8")
            statements = "\n".join(
                line
                for line in script.splitlines()
                if line.strip().upper() not in {"BEGIN;", "COMMIT;"}
            )
            await driver.execute(statements)

    return list(MIGRATIONS)
