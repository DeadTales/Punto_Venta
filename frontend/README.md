# Escritorio Flet

Desde la raíz, con el entorno frontend activo:

```powershell
python -m pip install -r frontend/requirements.txt
python -m frontend.src.main
```

Se utiliza Flet 1.1.2 con servicios y selectores de archivos asíncronos. También admite `python frontend/src/main.py`. En Linux el selector de archivos puede requerir Zenity.

`frontend/.env` selecciona `POS_MODE=api` para los datos reales y `API_BASE_URL` para la API. `POS_MODE=demo` usa datos ficticios en memoria. Las contraseñas y los tokens no se guardan en disco.

La interfaz incluye gestión de clientes y empleados, inventario, categorías, ajustes, caja y cortes persistentes, historial de ventas, cancelaciones y tickets PDF/ESC-POS. Los reportes cargan todas las páginas y exportan el conjunto a CSV. Configuración permite cambiar correo y contraseña, guardar la apariencia y configurar impresoras USB, seriales o de red.

`app.py` coordina sesión y navegación; las vistas están en `views/`, los componentes en `components/`, los estados en `models/` y HTTP, productos, personas, tickets e impresoras en `services/`. Los contratos compartidos viven en `shared/`.

Las preferencias se guardan en `.pos_settings.json`, ignorado por Git. La impresión requiere un dispositivo compatible y su controlador; el botón Imprimir prueba envía un trabajo físico. El modo demo también permite imprimir cuando se solicita expresamente.

Consulta [la guía de operación](../docs/operacion.md). El entorno frontend no necesita credenciales PostgreSQL; `requirements-offline.txt` permite instalar el backend en el mismo entorno si se elige esa distribución.
