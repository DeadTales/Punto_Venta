# Punto · Sistema POS

Punto de venta de escritorio con FastAPI, Flet y PostgreSQL. Incluye usuarios y clientes, catálogo e inventario, caja, ventas, cancelaciones, tickets PDF e impresión ESC/POS.

## Arranque en Windows

Desde la raíz, instala o actualiza las dependencias de los entornos existentes:

```powershell
./backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
./frontend/.venv/Scripts/python.exe -m pip install -r frontend/requirements.txt
```

Si aún no existen, créalos primero con `python -m venv backend/.venv` y `python -m venv frontend/.venv`. Conserva tus `.env` existentes. La configuración está documentada en los archivos `.env.example`.

Prepara la base de datos e inicia la API:

```powershell
./backend/.venv/Scripts/python.exe -m backend.src.cli migrate
./backend/.venv/Scripts/python.exe -m uvicorn backend.src.main:app --host 127.0.0.1 --port 8000 --reload
```

En otra terminal inicia el escritorio:

```powershell
./frontend/.venv/Scripts/python.exe -m frontend.src.main
```

`frontend/.env` selecciona `POS_MODE=api` y `API_BASE_URL=http://127.0.0.1:8000`. El modo `demo` permite probar con datos ficticios en memoria. Swagger está en <http://127.0.0.1:8000/docs>.

## Funciones

| Área | Implementación |
| --- | --- |
| Acceso | Login JWT, roles, empleados activos, cambio de correo/contraseña y revocación de sesiones |
| Clientes y empleados | Altas, consultas, búsquedas, edición y bajas con conservación del historial |
| Inventario | Productos y categorías, códigos de barras, filtros, alertas, márgenes, ajustes auditados e importación Excel |
| Caja | Apertura y cierre persistentes, conciliación de efectivo e historial por empleado |
| Ventas | Carrito, cantidades decimales, precios congelados, stock transaccional y reintentos idempotentes |
| Comprobantes | Detalle, cancelación con devolución de stock, PDF y adaptadores ESC/POS USB, serial y red |
| Reportes | Periodos, paginación histórica, CSV y sugerencias de reposición por demanda media |
| Operación local | Cola persistente de salida y recibos de sincronización por UUID |

Las impresoras se configuran y prueban desde Periféricos. El pago bancario y la facturación fiscal no forman parte del procesamiento: se registra el método de pago y se emite un ticket de venta.

## Documentación y pruebas

- [Instalación, cuentas, operación y límites](docs/operacion.md).
- [Módulo de Persona 2](docs/persona2.md).
- [Estilo y modularización](docs/code_style.md).
- [Arquitectura de conexión y sincronización](docs/arquitectura_y_offline.md).

Para una base vacía usa `python -m backend.src.cli bootstrap` después de migrar. Para recuperar una cuenta existente usa `python -m backend.src.cli reset-password --email usuario@ejemplo.com`; la contraseña se solicita sin mostrarla.

```powershell
python -m pip install -r backend/requirements-dev.txt -r frontend/requirements.txt
python -m ruff check backend frontend shared tests
python -m ruff format --check backend frontend shared tests
python -m pytest tests -q
```

Las pruebas PostgreSQL necesitan `POS_TEST_DATABASE_URL` o `POS_TEST_SCHEMA_URL` para crear bases o esquemas nuevos y aislados. Sin ellas se omiten las pruebas de integración. Las pruebas Flet necesitan sus dependencias instaladas.
