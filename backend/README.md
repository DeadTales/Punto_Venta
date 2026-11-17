# Backend

Ejecutar desde la raíz: `python -m uvicorn backend.src.main:app --reload`.
Instalar `python -m pip install -r backend/requirements.txt` en el entorno backend.

El cliente oficial `supabase` está incluido en los requirements. La API actual accede a PostgreSQL mediante SQLAlchemy/asyncpg y autentica empleados con JWT propios. Instalar el SDK no cambia esos flujos ni activa Supabase Auth.

| Variable | Función | Uso actual en la API |
| --- | --- | --- |
| `DATABASE_URL` | Conexión PostgreSQL copiada desde **Connect** en el panel | Obligatoria en modo `cloud` |
| `JWT_SECRET` | Secreto propio del POS para firmar y verificar sesiones HS256 | Obligatoria, al menos 32 caracteres |
| `SUPABASE_URL` | URL HTTPS del proyecto para el SDK | Disponible para una integración futura |
| `SUPABASE_PUBLISHABLE_KEY` | Clave publicable del SDK; su acceso depende de los permisos y políticas del proyecto | Disponible para una integración futura |
| `SUPABASE_SECRET_KEY` | Clave privada del servidor para operaciones privilegiadas | No se requiere para la implementación actual |
| `SUPABASE_JWKS_URL` | Endpoint de claves públicas para verificar JWT de Supabase Auth | No se utiliza en el login actual |

En `.env` escribe URLs sin escapes, como `https://TU_PROYECTO.supabase.co`. Las claves de la API de Supabase y la URL JWKS no sustituyen `DATABASE_URL` ni `JWT_SECRET`. La clave secreta de Supabase sólo pertenece al backend y no debe incluirse en Git. La configuración de ejemplo contiene únicamente nombres y valores de muestra.

`core/config/settings.py` lee exclusivamente `backend/.env` y las variables del proceso. `DATABASE_MODE` selecciona **una base fija por proceso**. No cambia una transacción de nube a local ante una desconexión.

## Conexión única y concurrencia

`core/config/db_config.py` contiene `Database` y la única `Base` declarativa. FastAPI crea una instancia durante su lifespan, la guarda en `app.state.database` y cierra el pool al apagar. La instancia administra un pool de hasta `DB_POOL_SIZE + DB_MAX_OVERFLOW` conexiones por proceso; `pool_pre_ping` descarta conexiones caducadas.

Compartir una conexión física o una sesión global entre peticiones no es seguro. SQLAlchemy establece el modelo **AsyncSession por tarea**: [documentación oficial](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#is-the-session-thread-safe-is-asyncsession-safe-to-share-in-concurrent-tasks). Si configuras varios workers, cada uno tiene su propio pool; dimensiona el total para los límites de PostgreSQL/Supabase. `dispose()` sólo se llama al apagar, nunca desde un modelo.

Los modelos describen tablas. Los repositorios reciben `AsyncSession`; no crean engines ni llaman `commit`. La dependencia común abre la transacción, hace commit antes de enviar la respuesta (`scope="function"`), rollback si hay errores y devuelve la conexión al pool:

```python
from fastapi import Depends
from backend.src.core.config.db_config import get_session
from backend.src.modules.product.product_repository import ProductRepository


async def consultar(session=Depends(get_session, scope="function")):
    return await ProductRepository(session).search("agua")
```

Para tareas fuera de HTTP usa `async with database.session() as session:`. Si lanzas tareas concurrentes, cada una debe abrir su propia sesión. Los modelos heredan una sola `Base`. Productos y categorías pertenecen a sus archivos de Persona 2 y se exportan desde `modules/entities.py` para conservar los imports existentes de los otros integrantes.

Los módulos nuevos usan nombres como `product_model.py`, `client_service.py`, `employee_route.py`, `cash_service.py` y `sale_route.py`. Los helpers existentes de ventas y sincronización mantienen sus imports para conservar la integración. Consulta las [reglas de estilo](../docs/code_style.md) y la [guía completa de operación](../docs/operacion.md).

## API implementada

| Ruta | Función | Acceso |
| --- | --- | --- |
| `GET /api/health` | Disponibilidad de la base seleccionada | Público, sin credenciales ni URL de DB |
| `POST /api/auth/login`, `GET /api/auth/me` | Sesión JWT / perfil seguro | Login / sesión |
| `GET /api/products`, `/api/products/{id}`, `/api/products/barcode/{code}`, `/api/products/low-stock` | Buscar, paginar, filtrar categoría/stock y consultar códigos exactos | Sesión |
| `POST /api/products`, `PUT/DELETE /api/products/{id}` | Crear, editar y eliminar productos sin historial | Supervisor o Admin |
| `GET/POST /api/products/{id}/stock-adjustments` | Historial / ajuste con UUID y motivo | Sesión / Supervisor o Admin |
| `GET/POST /api/categories`, `PUT/DELETE /api/categories/{id}` | CRUD de categorías | Sesión para lectura / Supervisor o Admin para escritura |
| `GET /api/inventory/template` | Descargar plantilla Excel | Sesión |
| `POST /api/inventory/preview` | Validar Excel y referencias | Supervisor o Admin |
| `POST /api/inventory/import` | Importar todos los productos o ninguno | Supervisor o Admin |
| `GET/POST /api/clients`, `GET/PUT/DELETE /api/clients/{id}` | Clientes y búsqueda por nombre, correo o identificación | Sesión; baja por Supervisor/Admin |
| `GET/POST /api/employees`, `GET/PUT/DELETE /api/employees/{id}` | Empleados, roles y desactivación | Administrador |
| `PUT /api/auth/password`, `PUT /api/auth/email`, `POST /api/auth/logout` | Actualizar cuenta y revocar tokens anteriores | Sesión y contraseña actual para cambios |
| `GET /api/config` | Nombre comercial y tasa de impuesto incluido | Sesión |
| `GET /api/shifts`, `GET /api/shifts/current`, `POST /api/shifts/open`, `POST /api/shifts/{id}/close` | Aperturas, cortes e historial | Turno propio; supervisión por Supervisor/Admin |
| `GET /api/sales/{id}`, `POST /api/sales/{id}/cancel`, `GET /api/sales/{id}/receipt` | Detalle, devolución de stock y PDF | Sesión; cancelación por Supervisor/Admin |
| `GET /api/reports/products` | Consumo y reposición sugerida por producto | Sesión |
| `GET /api/payment-methods`, `GET /api/sales` | Catálogo e historial reciente | Sesión |
| `POST /api/sales` | Venta atómica, precio del servidor, bloqueo de stock | Sesión |
| `GET /api/sync/status` | Contadores y conflictos, sin payloads | Sesión |
| `POST /api/sync/push` | Enviar cola local en orden | Supervisor o Admin |
| `POST /api/sync/outbox/{uuid}/retry` | Reintentar tras resolver la causa | Supervisor o Admin |
| `POST /api/sync/events` | Receptor central idempotente | Secreto servidor `X-Sync-Key` |

Excel usa multipart con campo `file`. La confirmación vuelve a validar el archivo y el estado actual de la base. Los códigos existentes causan error; no se sobrescriben precios ni stock. Una carrera por el mismo código la resuelve la restricción UNIQUE con rollback completo.

El cliente genera `operation_id` UUID antes de cobrar y lo conserva si hay timeout. El servidor agrupa todos los cambios de venta en la misma transacción, bloquea productos en orden de ID para reducir deadlocks y congela el precio de cada línea. Usa `Decimal` y redondeo por línea a 2 decimales. Repetir la misma operación no vuelve a descontar stock; cambiar el contenido con el mismo UUID devuelve conflicto. La tasa configurable `POS_TAX_RATE` desglosa el impuesto incluido sin cambiar los precios finales; por defecto es 0. Los pagos divididos y la facturación fiscal no forman parte del contrato de venta.

No se abre ni migra la base automáticamente. Para bases nuevas, `python -m backend.src.cli init-db`; para existentes, la migración SQL revisada. El bootstrap crea catálogos y un administrador con bcrypt, sin contraseña predeterminada. No hace cambios en una base real a menos que ejecutes estos comandos con su URL configurada.

## Preparación y recuperación

`python -m backend.src.cli migrate` crea las tablas faltantes y aplica 04, 05 y 06 en una transacción. Puede repetirse. `bootstrap` crea el administrador de una instalación vacía y solicita su contraseña; `reset-password --email cuenta@ejemplo.com` recupera una cuenta existente y revoca sus sesiones anteriores. El arranque de la API no ejecuta estos comandos automáticamente.

Los clientes con ventas conservan su historial; la baja de empleados desactiva el acceso. Un administrador no puede desactivarse ni quitarse su rol, y debe quedar al menos uno activo. Las cancelaciones son idempotentes y no alteran cortes cerrados. Los turnos se bloquean durante las ventas y el cierre para evitar cobros fuera del corte.
