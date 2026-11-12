# Punto · Sistema POS

API FastAPI + escritorio Flet + PostgreSQL, siguiendo la especificación técnica y el modelo relacional proporcionados. El maquetado funciona sin base de datos en **modo demo**; los datos ficticios están identificados y nunca se envían a la API.

## Abrir el maquetado

Desde la raíz del proyecto, en tu terminal con el entorno **frontend** activo:

```bash
python -m pip install -r frontend/requirements.txt
python -m frontend.src.main
```

Por defecto abre en modo demo. Puedes probar navegación, clientes/usuarios de ejemplo, carrito, cobro simulado, corte simulado, importación Excel y temas claro/oscuro. Los cambios demo viven sólo en memoria. En Linux el selector de archivos de Flet requiere Zenity. [Capturas de las vistas](docs/maquetado.md) y [plantilla Excel](docs/plantilla_inventario.xlsx).

## Conectar datos reales

En tu terminal con el entorno **backend** activo, también desde la raíz:

```bash
python -m pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

Completa la URL de PostgreSQL y genera `JWT_SECRET` como indica el ejemplo. **No reemplaces un `.env` que ya tenga tus credenciales.**

Para una **base nueva y vacía**, crea las tablas y el administrador (su contraseña se pide sin mostrarla):

```bash
python -m backend.src.cli init-db
python -m backend.src.cli bootstrap
```

Para una **base existente**, aplica explícitamente [la migración 04](db/migration/04_conexion_y_sincronizacion.sql). `init-db` no altera columnas existentes. El esquema original está en [01_tablas_iniciales.sql](db/schema/01_tablas_iniciales.sql); no se crearon los datos ficticios que la guía menciona en sus scripts 02/03.

Inicia la API:

```bash
python -m uvicorn backend.src.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger: <http://127.0.0.1:8000/docs>. En el entorno frontend configura `frontend/.env` a partir del ejemplo con `POS_MODE=api` y `API_BASE_URL=http://127.0.0.1:8000`. Inicia el escritorio e ingresa con tu empleado existente o `admin@pos.local` si ejecutaste bootstrap.

## Qué incluye

- Un `Database` por aplicación/proceso, un pool compartido y una `AsyncSession` por operación. Todos los modelos usan la misma `Base`; los repositorios reciben la sesión. Se libera al terminar y revierte ante errores.
- Las siete entidades originales, autenticación JWT, permisos por rol, consulta de catálogos, altas de categorías, importación atómica de productos y ventas con bloqueo de stock y reintentos idempotentes.
- Plantilla `.xlsx`, instrucciones, ejemplo independiente, vista previa, errores por fila y validación nuevamente al confirmar. Carga **productos nuevos**, no reemplaza la base ni actualiza existencias existentes.
- Todas las vistas pedidas, accesibles en uno o dos clics. Carrito e inventario conectados; reportes exploratorios calculados sobre los datos cargados.
- Base para operación local: PostgreSQL + API local y una cola persistente para enviar altas de inventario y ventas a la API central. [Alcance, configuración y límites](docs/arquitectura_y_offline.md).

El **CRUD de clientes/usuarios**, el corte contable persistido, los periféricos físicos, el cambio de contraseña/correo y las predicciones avanzadas quedan como maquetado, señalados dentro de las vistas. No se presentan como funcionalidades de producción.

## Documentación y comprobaciones

- [Conexiones, concurrencia y modo sin internet](docs/arquitectura_y_offline.md)
- [Vistas, mapa de navegación y estados del maquetado](docs/maquetado.md)
- [API y uso del gestor en nuevos módulos](backend/README.md)
- [Escritorio y dependencias locales](frontend/README.md)

Pruebas unitarias y del maquetado:

```bash
python -m pip install -r backend/requirements-dev.txt
python -m pytest tests -q
```

Para validar también PostgreSQL define `POS_TEST_DATABASE_URL` con un servidor **de pruebas** cuyo usuario pueda crear bases. Las pruebas crean y eliminan únicamente bases nuevas `pos_test_<UUID>`. Sin esta variable se omiten las pruebas de integración. Las pruebas Flet se omiten si el entorno no tiene Flet instalado; para ejecutar todo usa un entorno de pruebas con ambos requirements.
Database project.
