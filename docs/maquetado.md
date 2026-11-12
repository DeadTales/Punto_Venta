# Maquetado de escritorio

Capturas reales del maquetado ejecutado con Flet (datos demo):

- [Caja / Inicio](previews/caja-inicio.png)
- [Carrito](previews/carrito.png)
- [Inventario](previews/inventario.png)
- [Asistente de importación](previews/importar.png)
- [Reportes / Predicciones](previews/reportes-predicciones.png)
- [Tema oscuro](previews/oscuro.png)

[Plantilla Excel lista para llenar](plantilla_inventario.xlsx). La aplicación genera la misma estructura mediante `shared.inventory_excel.template_bytes()`.

## Navegación

La barra lateral siempre muestra Caja, Carrito, Inventario, Clientes, Reportes, Usuarios y Configuración (Usuarios se oculta para roles sin permiso en modo API). Las pestañas de un grupo aparecen dentro de su vista, sin menús anidados. El campo superior busca vistas por nombre o ruta; `Ctrl + K` lo enfoca y Enter abre coincidencias.

| Vista | Acceso desde cualquier pantalla | Clics de navegación |
| --- | --- | --- |
| Caja / Inicio | Caja | 1 |
| Caja / Corte | Caja → Corte | 2 |
| Carrito | Carrito | 1 |
| Inventario | Inventario | 1 |
| Clientes | Clientes | 1 |
| Usuarios | Usuarios | 1 |
| Reportes / Ventas | Reportes | 1 |
| Reportes / Clientes, Usuarios, Predicciones | Reportes → pestaña | 2 |
| Configuración / Periféricos | Configuración | 1 |
| Configuración / Aspectos, Contraseña, Correo | Configuración → pestaña | 2 |
| Importar inventario | Inventario → Importar Excel | 2 para abrir el módulo |

La regla de menos de tres clics corresponde al acceso a vistas, no a omitir las confirmaciones de cobro o importación. A partir de 980 px se compacta la barra lateral a iconos con tooltip; el contenido usa columnas responsivas y las tablas admiten desplazamiento horizontal.

## Vistas y comportamiento

- **Caja / Inicio:** ventas del día, tickets, ticket promedio, alertas de stock, tendencia semanal y últimos tickets. Acceso directo a venta, corte e inventario.
- **Caja / Corte:** fondo de apertura, cobros en efectivo, efectivo esperado, efectivo contado y diferencia. Apertura/cierre simulado en demo. No contabiliza movimientos reales porque el esquema original no tiene turnos ni retiros.
- **Carrito:** búsqueda por nombre/código, lectura como teclado USB, cantidades decimales, cliente opcional, total y cobro con los cuatro métodos del esquema. Calcula cambio en efectivo. El backend aplica stock y precio de catálogo. No procesa una operación bancaria ni aplica IVA no definido por el modelo.
- **Inventario:** búsqueda, filtro por categoría, stock bajo, costo/precio, existencias, alta de producto/categoría y carga Excel. Los indicadores usan el catálogo cargado; el precio/stock se guarda como decimal.
- **Clientes:** nombre, contacto, RFC/identificación fiscal opcional, búsqueda y formulario demo. Público general se modela sin crear un cliente artificial.
- **Usuarios:** nombre, correo, rol, teléfono y formulario demo. Los hashes de contraseña nunca llegan a esta tabla. Acceso administrativo en API.
- **Reportes:** periodo de 7/30 días, exportación CSV, ventas por método, acumulados por cliente/usuario y proyección por media simple. Los datos API se limitan a las 500 ventas más recientes; no es un reporte contable histórico completo. La predicción es exploratoria, sin modelo entrenado ni confianza inventada.
- **Configuración:** periféricos USB/Serial/Red (maquetado), tema claro/oscuro funcional durante la sesión, formularios de contraseña/correo pendientes de API, estado real de la cola local y reintento de sincronización tras corregir conflictos.

## Flujo Excel

1. **Descargar:** `plantilla_inventario.xlsx` tiene Inventario, Instrucciones y Ejemplo separado. Los encabezados llevan comentarios de ayuda; los códigos están preformateados como texto y los campos numéricos tienen validación de Excel.
2. **Llenar:** una fila por nuevo producto, categoría existente y valores sin fórmulas. Costo/precio admiten 2 decimales; existencias, 3. Los códigos opcionales no se repiten. No se importa la hoja de ejemplo.
3. **Seleccionar y revisar:** límite de 5 MB / 5,000 filas. La vista previa muestra hasta 10 productos o 30 errores con fila, columna y corrección. Con errores se desactiva Confirmar.
4. **Confirmar:** el backend valida de nuevo contra la base actual. Si algo falla, ningún producto del lote se guarda. En local también se guarda el evento de salida en la misma transacción.

El Excel es una entrada al catálogo, no una segunda base de datos ni un reemplazo del esquema PostgreSQL. No se actualiza un producto existente por coincidencia de nombre/código: esa política podría sobrescribir existencias de ventas recientes. Para reabastecer un artículo existente se requiere implementar un movimiento de inventario separado.

## Separación de demo y datos reales

La cabecera muestra **DEMO · datos ficticios** cuando corresponde. Los formularios y cobros demo modifican memoria y desaparecen al cerrar. En modo API no hay datos demo, se requiere login, no hay fallback silencioso y los módulos sin endpoint de escritura tienen sus acciones desactivadas o identificadas como maquetado.

Login, lectura de catálogos, importación, alta de productos/categorías, ventas y estado de sincronización sí consumen API. La administración completa de usuarios/clientes, turnos/cortes, cambios de credenciales, notificación por correo, impresión y predicciones avanzadas quedan para sus módulos de negocio; las dependencias y vistas están organizadas para integrarlos.

Se comprobó el renderizado de las 14 vistas, el diálogo de importación y el tema oscuro ejecutando Flet en Firefox sin interfaz. Esto no sustituye una prueba de los selectores nativos y periféricos en el equipo de caja; no se imprimieron tickets ni se conectó hardware.
