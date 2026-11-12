# Escritorio Flet

Desde la raíz, con el entorno frontend activo:

```bash
pip install -r frontend/requirements.txt
python frontend/src/main,py
```

También admite `flet run frontend/src/main.py`. Se usa la API de Flet **1.1.2**, con selectores de archivos asíncronos y `page.show_dialog`. En Linux instala Zenity con el gestor de paquetes de tu distribución si no está disponible. [Referencia oficial del selector](https://flet.dev/docs/services/filepicker/).

`frontend/.env.example` documenta `POS_MODE=demo` (predeterminado) y `POS_MODE=api`.

- **Demo:** todos los datos son ficticios, marcados en la cabecera. Los formularios de clientes/usuarios, importaciones, carrito y cobros modifican únicamente memoria. El corte simula una apertura/cierre; no hay operaciones reales ni envío de correos ni comandos a impresoras.
- **API:** login obligatorio, catálogos, inventario, importación y cobro contra FastAPI.

Los requirements se normalizaron a UTF-8 y dependencias directas: Flet, HTTP, validación, Excel y periféricos. SQLAlchemy/asyncpg pertenecen al entorno backend. Si necesitas que **el entorno frontend ejecute también la API local**, instala explícitamente:

```bash
pip install -r frontend/requirements-offline.txt
```

Estructura: `app.py` coordina sesión, navegación y estado; `views/` contiene pantallas; `components/ui.py` reúne estilos y componentes; `models/` contiene estado y datos demo; `services/api_client.py` centraliza HTTP. El contrato de importación vive en `shared/inventory_excel.py` para usar las mismas validaciones en demo y API.

Las preferencias visuales/periféricas duran durante la sesión. Los reportes son exploratorios sobre los registros cargados (hasta 500 ventas en API). Las predicciones muestran una media simple con su método; no simulan un modelo entrenado.
