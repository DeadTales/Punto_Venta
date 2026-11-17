# Operación del punto de venta

La aplicación usa FastAPI, PostgreSQL con conexión directa y el escritorio Flet. El backend controla permisos, precios, existencias, sesiones y transacciones; el escritorio consume la API con HTTP.

## Preparar una instalación

Conserva los archivos `.env` que ya tengan tus credenciales. `backend/.env.example` y `frontend/.env.example` documentan las variables.

En el backend se requieren `DATABASE_MODE=cloud`, `DATABASE_URL` con `postgresql+asyncpg://...` y SSL, y un `JWT_SECRET` aleatorio de al menos 32 caracteres. El SDK de Supabase está instalado, pero las operaciones del POS utilizan SQLAlchemy/asyncpg y JWT propios.

Desde la raíz, con el entorno backend:

```powershell
python -m backend.src.cli migrate
```

El comando crea las tablas faltantes y aplica las migraciones 04, 05 y 06 en una sola transacción. Puede repetirse y conserva los registros existentes. La API no aplica migraciones al arrancar. La migración 06 agrega empleados activos, revocación de sesiones, turnos, desglose de impuestos, nombres de productos en los tickets y auditoría de cancelaciones.

Para una instalación vacía, crea el administrador después de migrar:

```powershell
python -m backend.src.cli bootstrap
```

El usuario inicial de bootstrap es `admin@pos.local`; su contraseña se solicita sin mostrarla. En una base que ya tiene empleados utiliza sus cuentas existentes. Si necesitas recuperar una contraseña, desde la máquina que administra el backend:

```powershell
python -m backend.src.cli reset-password --email usuario@ejemplo.com
```

Este comando solicita la contraseña nueva e invalida los tokens anteriores. No imprime contraseñas ni modifica el rol de la cuenta.

## Arrancar

En una terminal con el entorno backend:

```powershell
python -m uvicorn backend.src.main:app --host 127.0.0.1 --port 8000 --reload
```

En otra terminal con el entorno frontend:

```powershell
python -m frontend.src.main
```

`frontend/.env` utiliza `POS_MODE=api` y `API_BASE_URL=http://127.0.0.1:8000`. Para probar sin backend selecciona explícitamente `POS_MODE=demo`. La API se puede explorar en `http://127.0.0.1:8000/docs`.

## Flujo de trabajo

La flecha izquierda junto a la ruta de la vista permite regresar a la pantalla anterior visitada. Aparece cuando hay historial de navegación; cerrar sesión borra ese historial.

1. Inicia sesión con un empleado activo. Administrador gestiona empleados; Administrador y Supervisor gestionan inventario y cancelaciones. Cajero consulta productos, registra clientes y cobra.
2. Crea o revisa categorías y productos. Puedes importar productos nuevos desde la plantilla Excel. Usa Ajustes para entradas y mermas de productos existentes; cada movimiento conserva motivo y empleado.
3. Abre un turno desde **Caja → Corte** e indica el fondo inicial. Sólo puede existir un turno abierto por empleado.
4. En **Carrito**, busca o escanea un código y pulsa Enter. Ajusta cantidades, selecciona cliente o Público general y el método de pago.
5. Confirma el cobro. La API guarda venta, partidas, precios congelados e inventario en una sola transacción. Un error revierte el conjunto. Ante una respuesta incierta, reintenta el mismo cobro: el UUID impide duplicar la venta.
6. Descarga o imprime el ticket. **Tickets** permite consultar todo el historial por páginas, filtrar fechas y volver a emitir comprobantes.
7. Un Administrador o Supervisor puede cancelar una venta mientras su turno siga abierto. Debe indicar el motivo. La API conserva el comprobante y devuelve las cantidades exactamente una vez. No se alteran los cortes ya cerrados.
8. Para cerrar, cuenta el efectivo. Se guardan fondo inicial, efectivo esperado, contado, diferencia, fecha y notas. El cierre se coordina con las ventas concurrentes para que ninguna quede fuera del corte.

Los cambios de contraseña, correo, permisos y estado invalidan sesiones anteriores. Cambiar tu correo o contraseña desde Configuración renueva la sesión actual. La baja de un empleado desactiva su acceso y conserva su historial. Un cliente o producto con historial no se elimina.

## Tickets e impresoras

`POS_BUSINESS_NAME` configura el encabezado. En **Configuración → Periféricos** selecciona:

- **USB:** identificadores de fabricante y producto, por ejemplo `0x04b8` y `0x0202`.
- **Serial / COM:** puerto o dispositivo y velocidad en baudios.
- **Red / Ethernet:** dirección y puerto, normalmente configurados por el fabricante.

Guarda la configuración y usa **Imprimir prueba**. El adaptador utiliza ESC/POS, cierra el dispositivo incluso si falla y permite desactivar el corte de papel. El botón Imprimir envía un trabajo físico también en demo si se pulsa expresamente. La compatibilidad final depende del modelo, controlador y conexión del equipo; las pruebas automatizadas utilizan un dispositivo simulado.

Las preferencias de impresora y apariencia se guardan en `frontend/.pos_settings.json`, excluido de Git. Los tokens de sesión y contraseñas no se guardan en ese archivo.

## Impuestos y reportes

Los precios del catálogo se consideran finales. `POS_TAX_RATE` define la fracción de impuesto incluido, con hasta cuatro decimales; el valor predeterminado `0` desactiva el desglose. La venta conserva la tasa, subtotal e impuesto que se calcularon al cobrar; cambiar la configuración no altera tickets anteriores. El ticket es un comprobante de venta, no un CFDI. Registrar Tarjeta o Transferencia indica el método utilizado; no ejecuta cargos bancarios.

Los reportes cargan todas las páginas de ventas, muestran tablas paginadas y exportan el conjunto a CSV. La reposición sugerida usa el máximo entre stock mínimo y demanda media para siete días, menos existencia actual. Excluye ventas canceladas y explica su método; no utiliza un modelo de aprendizaje automático.

## Operación local y sincronización

La conexión configurada del proyecto es directa a Supabase. Para una sucursal sin internet se necesita una API y PostgreSQL locales aprovisionados con los mismos UUID. La cola de salida soporta catálogo, importaciones, ajustes, clientes, empleados, ventas y cancelaciones. Los eventos son idempotentes y un conflicto detiene la cola para su conciliación.

Los turnos pertenecen a la base que los abrió; no se replican como cortes centralizados. La sincronización no descarga cambios de la nube ni fusiona existencias de varias sucursales. Consulta [la arquitectura de operación local](arquitectura_y_offline.md).

## Pruebas

Instala los requirements de desarrollo del backend y los del frontend en un entorno de pruebas. Ejecuta:

```powershell
python -m ruff check backend frontend shared tests
python -m ruff format --check backend frontend shared tests
python -m pytest tests -q
```

`POS_TEST_DATABASE_URL` permite crear bases nuevas de pruebas; `POS_TEST_SCHEMA_URL` permite crear esquemas nuevos con nombres `pos_test_<UUID>` en un servidor con permisos de creación de esquemas. En este segundo modo, cada conexión utiliza exclusivamente su esquema temporal y se elimina al terminar. Si no se configura ninguna variable, las pruebas PostgreSQL se omiten. No se utilizan automáticamente las tablas de trabajo de `.env` para probar ventas o cancelaciones.
