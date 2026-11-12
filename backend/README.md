# Backend

Ejecutar desde la raíz: `python -m uvicorn backend.src.main:app --reload`.
Instalar `python -m pip install -r backend/requirements.txt` en el entorno backend.

`core/config/settings.py` lee exclusivamente `backend/.env` y las variables del proceso. `DATABASE_MODE` selecciona **una base fija por proceso**. No cambia una transacción de nube a local ante una desconexión.

## Conexión única y concurrencia

`core/config/db_config.py` contiene `Database` y la única `Base` declarativa. FastAPI crea una instancia durante su lifespan, la guarda en `app.state.database` y cierra el pool al apagar. La instancia administra un pool de hasta `DB_POOL_SIZE + DB_MAX_OVERFLOW` conexiones por proceso; `pool_pre_ping` descarta conexiones caducadas.

Compartir una conexión física o una sesión global entre peticiones no es seguro. SQLAlchemy establece el modelo **AsyncSession por tarea**: [documentación oficial](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#is-the-session-thread-safe-is-asyncsession-safe-to-share-in-concurrent-tasks). Si configuras varios workers, cada uno tiene su propio pool; dimensiona el total para los límites de PostgreSQL/Supabase. `dispose()` sólo se llama al apagar, nunca desde un modelo.

Los modelos describen tablas. Los repositorios reciben `AsyncSession`; no crean engines ni llaman `commit`. La dependencia común abre la transacción, hace commit antes de enviar la respuesta (`scope="function"`), rollback si hay errores y devuelve la conexión al pool:

```python
from fastapi import Depends
from backend.src.core.config.db_config import get_session
from backend.src.modules.product.repository import ProductRepository

async def consultar(session=Depends(get_session, scope="function")):
    return await ProductRepository(session).search("agua")
```

Para tareas fuera de HTTP usa `async with database.session() as session:`. Si lanzas tareas concurrentes, cada una debe abrir su propia sesión. Los nuevos modelos heredan `Base`; los modelos existentes están en `modules/entities.py`, agrupados allí para evitar definiciones duplicadas y referencias circulares. Se sustituyeron archivos vacíos con nombres como `product.model.py` por módulos importables normales (`models.py`, `repository.py`, `service.py`, `routes.py`).

## API implementada

| Ruta | Función | Acceso |
| --- | --- | --- |
| `GET /api/health` | Disponibilidad de la base seleccionada | Público, sin credenciales ni URL de DB |
| `POST /api/auth/login`, `GET /api/auth/me` | Sesión JWT / perfil seguro | Login / sesión |
| `GET /api/products` | Buscar, paginar, filtrar stock bajo | Sesión |
| `GET /api/categories`, `POST /api/categories` | Consultar / crear categorías | Sesión / Supervisor o Admin |
| `GET /api/inventory/template` | Descargar plantilla Excel | Sesión |
| `POST /api/inventory/preview` | Validar Excel y referencias | Supervisor o Admin |
| `POST /api/inventory/import` | Importar todos los productos o ninguno | Supervisor o Admin |
| `GET /api/clients`, `GET /api/employees` | Directorios | Sesión / Admin |
| `GET /api/payment-methods`, `GET /api/sales` | Catálogo e historial reciente | Sesión |
| `POST /api/sales` | Venta atómica, precio del servidor, bloqueo de stock | Sesión |
| `GET /api/sync/status` | Contadores y conflictos, sin payloads | Sesión |
| `POST /api/sync/push` | Enviar cola local en orden | Supervisor o Admin |
| `POST /api/sync/outbox/{uuid}/retry` | Reintentar tras resolver la causa | Supervisor o Admin |
| `POST /api/sync/events` | Receptor central idempotente | Secreto servidor `X-Sync-Key` |

Excel usa multipart con campo `file`. La confirmación vuelve a validar el archivo y el estado actual de la base. Los códigos existentes causan error; no se sobrescriben precios ni stock. Una carrera por el mismo código la resuelve la restricción UNIQUE con rollback completo.

El cliente genera `operation_id` UUID antes de cobrar y lo conserva si hay timeout. El servidor agrupa todos los cambios de venta en la misma transacción, bloquea productos en orden de ID para reducir deadlocks y congela el precio de cada línea. Usa `Decimal` y redondeo por línea a 2 decimales. Repetir la misma operación no vuelve a descontar stock; cambiar el contenido con el mismo UUID devuelve conflicto. El esquema no define IVA desglosado ni pagos divididos.

No se abre ni migra la base automáticamente. Para bases nuevas, `python -m backend.src.cli init-db`; para existentes, la migración SQL revisada. El bootstrap crea catálogos y un administrador con bcrypt, sin contraseña predeterminada. No hace cambios en una base real a menos que ejecutes estos comandos con su URL configurada.
