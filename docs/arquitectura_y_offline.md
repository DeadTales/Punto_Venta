# Conexiones, concurrencia y operación sin internet

## Decisión de conexión

Una clase `Database`, instanciada una vez por aplicación/proceso, concentra configuración, engine, pool y fábrica de sesiones. Los modelos comparten `Base`. Una petición o tarea obtiene su propia sesión y transacción. Esto cumple el objetivo de centralizar el acceso sin imponer una única conexión física que serialice todo o mezcle transacciones concurrentes.

```mermaid
flowchart LR
    UI[Escritorio Flet] --> API[API FastAPI]
    API --> D[Database único por proceso]
    D --> P[Pool PostgreSQL]
    P --> S1[Sesión de petición A]
    P --> S2[Sesión de petición B]
    S1 --> DB[(Base configurada)]
    S2 --> DB
```

La venta bloquea las filas `PRODUCTO` con `SELECT ... FOR UPDATE` en orden de ID; comprueba stock, congela el precio y guarda cabecera, partidas y descuento en una sola transacción. Dos cajeros no pueden consumir la misma última unidad. Los reintentos se identifican con UUID y hash del contenido. El backend obtiene empleado y permisos de la sesión, no del cuerpo enviado por el escritorio.

El pool es por proceso, no por máquina ni por todos los workers. Cinco workers con pool 5 y overflow 5 pueden consumir hasta 50 conexiones. Las URL normales `postgresql://` se normalizan a `postgresql+asyncpg://`; `sslmode` se adapta al parámetro `ssl` del driver. La URL y las credenciales no se imprimen.

## Modo local primero

Para continuar operando cuando cae internet, **PostgreSQL y la API deben estar disponibles en el local**. El frontend siempre apunta a la misma API local, incluso cuando sí hay internet. No se intenta cambiar de base en medio de una venta ni se repite automáticamente una escritura en otra base tras un timeout: la primera podría haberse confirmado.

```mermaid
flowchart LR
    F[Flet de la sucursal] --> L[API local FastAPI]
    L --> PG[(PostgreSQL local)]
    PG --> O[Cola persistente sync_outbox]
    O --> W[Worker con reintentos]
    W -->|HTTPS + X-Sync-Key| C[API central]
    C --> CL[(PostgreSQL / Supabase)]
    CL --> R[Recibos de eventos por UUID]
```

Instalar `asyncpg` no instala PostgreSQL. Usa PostgreSQL 15+ como servicio del sistema o un contenedor administrado por el equipo. Conserva tus entornos virtuales separados: el entorno backend ejecuta la API local; el frontend sólo necesita HTTP. El extra `frontend/requirements-offline.txt` sirve si decides ejecutar ambos desde un mismo entorno.

Configuración de la API local en `backend/.env`:

```dotenv
DATABASE_MODE=local
LOCAL_DATABASE_URL=postgresql+asyncpg://pos:PASSWORD_LOCAL@127.0.0.1:5432/pos
JWT_SECRET=SECRETO_ALEATORIO_DE_AL_MENOS_32_CARACTERES
SYNC_API_URL=https://api-central.ejemplo.com
SYNC_KEY=SECRETO_COMPARTIDO_ALEATORIO_DE_AL_MENOS_32_CARACTERES
SYNC_INTERVAL=30
```

La API central usa `DATABASE_MODE=cloud`, su `DATABASE_URL`, un `JWT_SECRET` propio y el mismo `SYNC_KEY`. Su `SYNC_API_URL` queda vacío. El secreto de sincronización pertenece a los servidores, nunca al escritorio. La nube debe ser accesible por HTTPS.

## Aprovisionamiento inicial

1. Aplica la migración 04 en el catálogo central existente **antes de generar una copia local**. Agrega UUID a categorías, clientes, empleados, productos y ventas sin reemplazar sus PK SERIAL.
2. Aprovisiona la base local con una copia consistente del catálogo central, preservando UUID, claves, empleados, hashes, métodos de pago y secuencias. Usa las herramientas de respaldo/restauración de PostgreSQL con una copia revisada por el equipo. No regeneres UUID en cada instalación ni copies productos por nombre o ID local.
3. Para una instalación de prueba totalmente nueva puedes usar `init-db` + `bootstrap` en cada lado: la categoría General y el administrador del bootstrap tienen UUID deterministas comunes. El resto de los registros requiere aprovisionamiento compartido. No ejecutes bootstrap para duplicar administradores de una base existente.
4. Configura `DATABASE_MODE=local`, inicia la API en la sucursal y usa `POS_MODE=api` en Flet. Prueba primero con bases separadas de desarrollo. En la operación de esta primera versión, todas las cajas de esa sucursal deben consumir **la misma API/base local**.

No se modificó ni se conectó ninguna base real del usuario durante la implementación. Los `.env` existentes se conservaron. Las migraciones se entregan para ejecución explícita.

## Qué sincroniza esta versión

| Operación | Persistencia local | Envío central |
| --- | --- | --- |
| Alta de productos desde formulario/Excel | Lote entero y outbox en la misma transacción | `inventory.imported`, conserva UUID y existencia inicial |
| Alta de categorías | Categoría local | La importación transporta su identidad; crea la categoría central si no existe y no hay colisión de nombre |
| Venta | Venta, partidas, stock y outbox en la misma transacción | `sale.completed`, precio congelado y descuento transaccional en nube |
| Consulta de catálogos/reportes | Lectura de la base seleccionada | No genera eventos |
| Clientes/empleados, edición/borrado de productos, ajustes de stock, cancelaciones y turnos | No implementados como escrituras operativas en este alcance | No se replican |

La cola se procesa en orden. Un bloqueo asesor de PostgreSQL permite sólo un publicador local a la vez. La API central registra `sync_receipt` **en la misma transacción** que los cambios. Si se pierde la respuesta después del commit, repetir el UUID devuelve `already_applied`. La cola sólo se marca `sent` después de una confirmación reconocida. Se envían hasta 25 eventos por ciclo, con timeout por petición; los siguientes esperan el próximo ciclo o el botón manual.

Si la red falla, el evento sigue `pending` en disco y se reintenta. Si el proceso se reinicia, la cola continúa. Si la nube tiene stock insuficiente, un UUID de catálogo incompatible o una colisión de código, el evento pasa a `conflict` y bloquea los siguientes. La venta local ya realizada sigue registrada; no se borra ni se cambia silenciosamente su importe.

`Configuración` muestra pendientes/conflictos y permite enviar ahora. Tras corregir la causa en el sistema central, Supervisor/Admin puede reintentar el evento con el **mismo UUID y payload**. Esto no fusiona ni modifica eventos: un conflicto real de existencias requiere conciliación del responsable, no cambiar el mensaje para forzar su aceptación.

## Límites que quedan para una réplica completa

Esta es una sincronización **de salida** para altas de inventario y ventas, no una réplica bidireccional general ni un sistema terminado de múltiples sucursales. Los cambios hechos directamente en la nube no se descargan automáticamente al local. No mantengas dos bases activas como autoridades del mismo inventario esperando una fusión automática.

Antes de habilitar ventas independientes entre varias sucursales, cambios simultáneos de catálogo o descarga incremental se necesitan existencias por sucursal, movimientos de inventario, versiones de entidades, política de conflictos, aprovisionamiento seguro y auditoría. Los siete documentos base no definen esas entidades. Los turnos y cortes también requieren tablas adicionales; el maquetado los identifica como simulados.

La independencia de dos bases desconectadas impide garantizar stock global en tiempo real. Aquí se evita stock negativo en cada base y se registra el conflicto central cuando corresponde. Los pendientes y conflictos deben quedar resueltos antes de reemplazar la base local por otro respaldo.

## Validación realizada

Las pruebas de integración crean bases aisladas PostgreSQL, sin escribir en bases existentes, y verifican sesiones separadas, rollback, venta concurrente de la última unidad, reintentos de venta, importación atómica, migración repetible, permisos de sesión, sincronización con confirmación perdida y bloqueo de cola por conflicto de stock. Las pruebas de Excel comprueban formato, ceros iniciales, fórmulas, duplicados y precisión decimal.

Resultado de la suite de esta implementación: **28 pruebas aprobadas**, incluidas las de PostgreSQL real. Se usó un entorno de pruebas temporal; no se modificaron los dos entornos virtuales del usuario.
