# Migraciones

Desde la raíz, con el entorno backend, ejecuta `python -m backend.src.cli migrate`. El comando prepara las tablas iniciales si faltan y aplica 04, 05 y 06 en una sola transacción, bajo un bloqueo para evitar migraciones simultáneas.

- `04_conexion_y_sincronizacion.sql`: UUID y cola de sincronización.
- `05_ajustes_inventario.sql`: auditoría e idempotencia de ajustes de stock.
- `06_operacion_completa.sql`: empleados activos, versión de sesiones, turnos de caja, impuestos incluidos, nombres congelados de productos y cancelaciones auditadas.

Las migraciones pueden repetirse y conservan registros existentes. Las bases nuevas creadas con `python -m backend.src.cli init-db` incluyen los modelos actuales. El comando `migrate` también actualiza bases que ya tienen las siete tablas originales.

El inicio de la API no modifica el esquema automáticamente. Consulta [la guía de operación](../../docs/operacion.md).
