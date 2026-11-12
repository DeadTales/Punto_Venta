# Punto · Sistema POS

API FastAPI + escritorio Flet + PostgreSQL. El maquetado funciona sin base de datos en **modo demo**; los datos ficticios están identificados y nunca se envían a la API.

## Inicializacion del proyecto

Desde la raíz del proyecto, en tu terminal con el entorno **frontend** activo:

```bash
python -m venv <name_front_venv>
source <name_front_venv>/bin/activate
pip install -r frontend/requirements.txt
python frontend/src/main.py
```

Por defecto abre en modo demo. Puedes probar navegación, clientes/usuarios de ejemplo, carrito, cobro simulado, corte simulado, importación Excel y temas claro/oscuro. Los cambios demo viven sólo en memoria. En Linux el selector de archivos de Flet requiere Zenity. [Capturas de las vistas](docs/maquetado.md) y [plantilla Excel](docs/plantilla_inventario.xlsx).

## Conectar datos reales

En tu terminal con el entorno **backend** activo, también desde la raíz:

```bash
python -m venv <name_back_venv>
source <name_back_venv>/bin/activate
pip install -r backend/requirements.txt
```

Completa la URL de PostgreSQL y genera `JWT_SECRET` como indica el ejemplo. **No reemplaces un `.env` que ya tenga tus credenciales.**

Para una **base nueva y vacía**, crea las tablas y el administrador (su contraseña se pide sin mostrarla):

```bash
python -m backend.src.cli init-db
python -m backend.src.cli bootstrap
```

Inicia la API:

```bash
uvicorn backend/src/main:app --reload --host 127.0.0.1 --port 8000
```

Swagger: <http://127.0.0.1:8000/docs>. En el entorno frontend configura `frontend/.env` a partir del ejemplo con `POS_MODE=api` y `API_BASE_URL=http://127.0.0.1:8000`. Inicia el escritorio e ingresa con tu empleado existente o `admin@pos.local` si ejecutaste bootstrap.

## Test

Pruebas unitarias y del maquetado:

```bash
pip install -r backend/requirements-dev.txt
pytest tests -q
```

Para validar también PostgreSQL define `POS_TEST_DATABASE_URL` con un servidor **de pruebas** cuyo usuario pueda crear bases. Las pruebas crean y eliminan únicamente bases nuevas `pos_test_<UUID>`. Sin esta variable se omiten las pruebas de integración. Las pruebas Flet se omiten si el entorno no tiene Flet instalado; para ejecutar todo usa un entorno de pruebas con ambos requirements.
Database project.
