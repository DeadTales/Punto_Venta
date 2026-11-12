# Escritorio Flet

Desde la raíz, con el entorno frontend activo:

```bash
python -m pip install -r frontend/requirements.txt
python -m frontend.src.main
```

También admite `flet run frontend/src/main.py`. Se usa la API de Flet **1.1.2**, con selectores de archivos asíncronos y `page.show_dialog`. En Linux instala Zenity con el gestor de paquetes de tu distribución si no está disponible. [Referencia oficial del selector](https://flet.dev/docs/services/filepicker/).

`frontend/.env.example` documenta `POS_MODE=demo` (predeterminado) y `POS_MODE=api`.

- **Demo:** todos los datos son ficticios, marcados en la cabecera. Los formularios de clientes/usuarios, importaciones, carrito y cobros modifican únicamente memoria. El corte simula una apertura/cierre; no hay operaciones reales ni envío de correos ni comandos a impresoras.
- **API:** login obligatorio, catálogos, inventario, importación y cobro contra FastAPI. No se cambia silenciosamente a datos demo cuando falla la red. Clientes/usuarios se consultan en modo lectura. Las vistas que aún no tienen backend lo indican y desactivan el guardado.

No introduzcas `DATABASE_URL`, contraseñas de PostgreSQL ni `SYNC_KEY` en el frontend. `httpx` consume siempre la API; en una sucursal sin internet esa API se ejecuta localmente y conserva la misma dirección. Instalar un driver PostgreSQL no instala el servidor.

Los requirements se normalizaron a UTF-8 y dependencias directas: Flet, HTTP, validación, Excel y periféricos. SQLAlchemy/asyncpg pertenecen al entorno backend. Si necesitas que **el entorno frontend ejecute también la API local**, instala explícitamente:

```bash
python -m pip install -r frontend/requirements-offline.txt
```

Con tus dos entornos separados no hace falta ese extra: ejecuta la API local en la terminal backend y Flet en la terminal frontend. PostgreSQL se instala como servicio del sistema, independientemente de pip.

Estructura: `app.py` coordina sesión, navegación y estado; `views/` contiene pantallas; `components/ui.py` reúne estilos y componentes; `models/` contiene estado y datos demo; `services/api_client.py` centraliza HTTP. El contrato de importación vive en `shared/inventory_excel.py` para usar las mismas validaciones en demo y API.

Las preferencias visuales/periféricas duran durante la sesión. Los reportes son exploratorios sobre los registros cargados (hasta 500 ventas en API). Las predicciones muestran una media simple con su método; no simulan un modelo entrenado.
