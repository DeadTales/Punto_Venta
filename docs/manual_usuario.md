# Manual de usuario de Punto

**Sistema de punto de venta de escritorio**  
Versión del manual: 1.1 · Fecha: 16 de noviembre de 2026

Este manual explica cómo operar Punto desde sus pantallas. Está dirigido a administradores, supervisores y cajeros. La instalación y la configuración técnica se describen en [Operación del punto de venta](operacion.md).

Las capturas se obtuvieron ejecutando la interfaz del proyecto con datos ficticios. Los números y flechas señalan controles concretos y se explican en la tabla situada debajo de cada figura; la numeración vuelve a comenzar en cada imagen. Los acercamientos a formularios facilitan la lectura de los campos. Las opciones visibles pueden variar según tu rol y el tamaño de la ventana. Las pantallas de acceso y sesión también se ilustran con datos ficticios, sin utilizar cuentas ni contraseñas reales.

## Contenido

1. Acceso y permisos.
2. Navegación por el sistema.
3. Apertura del turno.
4. Registro y cobro de ventas.
5. Consulta, descarga y cancelación de tickets.
6. Clientes.
7. Inventario y categorías.
8. Importación de productos desde Excel.
9. Cierre y consulta de caja.
10. Usuarios y permisos de acceso.
11. Reportes.
12. Configuración personal e impresoras.
13. Problemas frecuentes.
14. Guía rápida de una jornada.
15. Glosario.

## 1. Acceso y permisos

### Antes de comenzar

- Solicita al administrador tu correo de acceso y contraseña.
- Comprueba que la aplicación y su servicio estén iniciados. Si necesitas ayuda para arrancarlos, consulta al responsable del equipo.
- La configuración actual utiliza la base de datos en la nube y requiere conexión a internet para consultar y guardar operaciones.
- Los importes se muestran en pesos mexicanos (MXN). Las cantidades de productos pueden tener hasta tres decimales.

### Iniciar sesión

1. Abre Punto.
2. Escribe tu correo y contraseña en la pantalla de bienvenida.
3. Pulsa **Entrar al sistema**. También puedes pulsar **Enter** desde el campo de contraseña.
4. Comprueba tu nombre y rol en la parte inferior del menú lateral.

Si la cuenta está desactivada o los datos son incorrectos, no podrás entrar. Pide al administrador que revise el acceso. Este manual no contiene contraseñas.

<!-- manual-figure:login:start -->
### Figura 01. Inicio de sesión

![Figura 01. Inicio de sesión](manual/anotadas/login.svg)

[Abrir captura original](manual/capturas/login.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Correo:** escribe el correo de acceso que te entregó el administrador. |
| 2 | **Contraseña:** captura tu contraseña; no se muestra en esta imagen. |
| 3 | **Mostrar contraseña:** el icono del ojo permite revisar lo escrito. |
| 4 | **Entrar al sistema:** valida los datos e inicia la sesión. |

<!-- manual-figure:login:end -->

### Qué puede hacer cada rol

| Función | Administrador | Supervisor | Cajero |
| --- | --- | --- | --- |
| Consultar productos y categorías | Sí | Sí | Sí |
| Crear, editar y eliminar productos y categorías; ajustar e importar inventario | Sí | Sí | No |
| Consultar, crear y editar clientes | Sí | Sí | Sí |
| Eliminar clientes sin ventas | Sí | Sí | No |
| Abrir su turno, cobrar y cerrar su caja | Sí | Sí | Sí |
| Consultar tickets, descargar PDF e imprimir | Sí | Sí | Sí |
| Cancelar ventas, sujeto al estado del turno | Sí | Sí | No |
| Administrar empleados y consultar el reporte de usuarios | Sí | No | No |
| Consultar reportes de ventas, clientes y reposición | Sí | Sí | Sí |
| Consultar historial de turnos | Todos | Todos | Los propios |
| Cambiar su correo, contraseña, apariencia e impresora | Sí | Sí | Sí |

Los permisos también se validan al guardar. Algunas acciones pueden estar ocultas o deshabilitadas según el rol. Los registros con historial tienen restricciones adicionales para su eliminación.

### Cerrar sesión

Pulsa **Salir** en el menú lateral. Esto termina tu acceso; no sustituye el cierre de caja. Cierra primero tu turno si estás terminando la jornada. Si existe un cobro sin confirmación, resuélvelo antes de salir.

<!-- manual-figure:sesion:start -->
### Figura 02. Controles de una sesión activa

![Figura 02. Controles de una sesión activa](manual/anotadas/sesion.svg)

[Abrir captura original](manual/capturas/sesion.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Actualizar:** vuelve a consultar los datos del servicio. |
| 2 | **Modo de conexión:** identifica la operación configurada; aquí se ilustra con datos ficticios. |
| 3 | **Cuenta y rol:** verifica qué empleado está utilizando el equipo. |
| 4 | **Salir:** termina la sesión; no sustituye el cierre del turno. |
| 5 | **Volver:** regresa a la vista anterior cuando hay historial. |

<!-- manual-figure:sesion:end -->

## 2. Navegación por el sistema

| Sección | Para qué sirve |
| --- | --- |
| Caja | Consultar el resumen de inicio y abrir o cerrar turnos desde Corte. |
| Carrito | Buscar productos, preparar una venta y cobrar. |
| Tickets | Consultar el historial y abrir comprobantes. |
| Inventario | Consultar productos, categorías, existencias y ajustes. |
| Clientes | Mantener el directorio de compradores. |
| Reportes | Consultar resultados y exportarlos. |
| Usuarios | Administrar empleados; disponible para Administrador. |
| Configuración | Cambiar preferencias, datos de acceso e impresora. |

La ruta que aparece encima del título indica dónde estás. La flecha **←** permite volver a la vista anterior visitada. Aparece cuando hay historial y ese historial se limpia al cerrar sesión. Regresar de vista no cancela una operación ya guardada.

El buscador superior **Ir a una vista…** localiza pantallas por nombre. Usa **Ctrl + K** para enfocarlo, escribe una búsqueda y pulsa **Enter**. Si hay varias coincidencias, selecciona la que necesitas.

El botón de actualización, junto al buscador superior, vuelve a consultar los datos del servicio. Úsalo para ver cambios realizados desde otro equipo. Las tablas anchas permiten desplazamiento horizontal; **Anterior** y **Siguiente** cambian de página cuando corresponda.

El indicador **API · nube** identifica la operación conectada a la base de datos remota. **API · base local** indica un servicio con base local. **DEMO · datos ficticios** identifica una demostración: sus cambios de negocio están en memoria y se pierden al reiniciar. La impresión física también funciona en demo si la solicitas.

<!-- manual-figure:inicio:start -->
### Figura 03. Mapa de la pantalla principal

![Figura 03. Mapa de la pantalla principal](manual/anotadas/inicio.svg)

[Abrir captura original](manual/capturas/inicio.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Menú principal:** Caja, Carrito, Tickets, Inventario, Clientes, Reportes y Usuarios abren sus respectivas vistas. |
| 2 | **Configuración:** abre las preferencias, datos de acceso y periféricos. |
| 3 | **Buscar vistas:** escribe un nombre y pulsa Enter; Ctrl + K enfoca el campo. |
| 4 | **Indicador de modo:** DEMO identifica datos ficticios para practicar. |
| 5 | **Pestañas Inicio y Corte:** alternan entre el resumen y la operación de caja. |
| 6 | **Nueva venta:** abre el Carrito para preparar un cobro. |
| 7 | **Indicadores:** resumen ventas, tickets, promedio y alertas de existencias. |
| 8 | **Actividad de ventas:** muestra la tendencia de los últimos siete días. |
| 9 | **Ver corte de caja:** abre el estado y cierre del turno. |
| 10 | **Revisar inventario:** permite consultar existencias y alertas. |
| 11 | **Ver reporte:** abre los resultados de ventas. |
| 12 | **Cuenta:** identifica al empleado y su rol actual. |

<!-- manual-figure:inicio:end -->

<!-- manual-figure:buscar_vista:start -->
### Figura 04. Resultados del buscador de vistas

![Figura 04. Resultados del buscador de vistas](manual/anotadas/buscar_vista.svg)

[Abrir captura original](manual/capturas/buscar_vista.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Inventario:** abre el listado de productos. |
| 2 | **Categorías:** abre las familias de productos. |
| 3 | **Ajustes:** abre los movimientos de existencias. |

<!-- manual-figure:buscar_vista:end -->

## 3. Apertura del turno

Debes tener un turno abierto para cobrar ventas.

1. Entra en **Caja** y selecciona **Corte**.
2. Pulsa **Abrir caja**.
3. Captura el **Fondo inicial**: el efectivo que hay físicamente al comenzar, por ejemplo `500.00`.
4. Pulsa **Abrir turno**.
5. Comprueba que el estado cambie a **Abierta** y que el fondo sea correcto.

Sólo puede existir un turno abierto por empleado. Si el sistema indica que ya tienes uno, revisa ese turno antes de intentar abrir otro.

<!-- manual-figure:caja_cerrada:start -->
### Figura 05. Caja antes de abrir un turno

![Figura 05. Caja antes de abrir un turno](manual/anotadas/caja_cerrada.svg)

[Abrir captura original](manual/capturas/caja_cerrada.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Abrir caja:** abre el formulario del fondo inicial. |
| 2 | **Estado:** Cerrada indica que debes abrir tu turno antes de cobrar. |
| 3 | **Fondo, efectivo y tickets:** muestran valores del turno cuando está abierto. |
| 4 | **Turnos registrados:** conserva los cierres anteriores para consultarlos. |

<!-- manual-figure:caja_cerrada:end -->

<!-- manual-figure:abrir_caja:start -->
### Figura 06. Formulario de apertura

![Figura 06. Formulario de apertura](manual/anotadas/abrir_caja.svg)

[Abrir captura original](manual/capturas/abrir_caja.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Fondo inicial:** escribe el efectivo físico con el que inicias el turno. |
| 2 | **Cancelar:** cierra el formulario sin abrir el turno. |
| 3 | **Abrir turno:** confirma el fondo y habilita los cobros. |

<!-- manual-figure:abrir_caja:end -->

## 4. Registro y cobro de ventas

### Preparar el carrito

1. Abre **Carrito**, o pulsa **Nueva venta** desde el inicio de Caja.
2. Escribe el nombre o código de barras en el buscador del catálogo.
3. Selecciona el producto que deseas agregar. Cada selección añade una unidad.
4. Si utilizas un lector que funciona como teclado, enfoca el buscador, escanea y pulsa **Enter** si el lector no lo hace automáticamente.
5. Repite el proceso con los demás productos.

Para cambiar una cantidad, escribe el valor en la fila del producto y pulsa **Enter**. Por ejemplo, `1.250` representa una unidad y cuarto para un producto vendido a granel. La cantidad debe ser mayor que cero y no superar la existencia disponible.

Usa el icono **×** para quitar un producto o **Vaciar carrito** para retirar todos. Antes de cobrar, elige un cliente registrado o conserva **Público general**. Revisa productos, cantidades, cliente y total.

<!-- manual-figure:carrito:start -->
### Figura 07. Preparación de una venta

![Figura 07. Preparación de una venta](manual/anotadas/carrito.svg)

[Abrir captura original](manual/capturas/carrito.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Buscar o escanear:** localiza productos por nombre o código. |
| 2 | **Agregar:** el botón + o la tarjeta añaden una unidad del producto. |
| 3 | **Cliente:** selecciona un cliente registrado o Público general. |
| 4 | **Cantidad:** escribe el valor y pulsa Enter para aplicarlo. |
| 5 | **Quitar:** retira esa partida del carrito. |
| 6 | **Total:** revisa el importe y el desglose de impuesto incluido. |
| 7 | **Cobrar venta:** abre el formulario de pago. |
| 8 | **Vaciar carrito:** quita todos los productos de la venta en preparación. |

<!-- manual-figure:carrito:end -->

### Cobrar

1. Pulsa **Cobrar venta**.
2. Selecciona el **Método de pago**.
3. Si elegiste **Efectivo**, escribe el **Efectivo recibido** y revisa el cambio calculado. Debe alcanzar para cubrir el total.
4. Pulsa **Confirmar cobro** una vez y espera la respuesta.
5. Al confirmarse, comprueba el número de ticket y abre su detalle para descargarlo o imprimirlo.

Ejemplo: dos productos de $25.00 y uno de $15.00 suman $65.00. Si recibes $100.00, el cambio es $35.00.

Los precios del catálogo son finales. Si el negocio tiene impuesto configurado, el sistema muestra su desglose como impuesto incluido. Elegir Tarjeta o Transferencia registra el método utilizado; el cobro bancario se realiza por el medio externo que use el negocio.

<!-- manual-figure:cobrar:start -->
### Figura 08. Formulario de cobro

![Figura 08. Formulario de cobro](manual/anotadas/cobrar.svg)

[Abrir captura original](manual/capturas/cobrar.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Total:** confirma cuánto debe pagar el cliente. |
| 2 | **Método de pago:** selecciona Efectivo, Tarjeta o Transferencia según corresponda. |
| 3 | **Efectivo recibido:** captura el importe entregado; debe cubrir el total. |
| 4 | **Cambio:** indica cuánto debes devolver al cliente. |
| 5 | **Volver:** regresa al carrito sin confirmar el cobro. |
| 6 | **Confirmar cobro:** registra la venta y abre su comprobante al confirmarse. |

<!-- manual-figure:cobrar:end -->

### Si el cobro queda sin confirmación

Si aparece un aviso de cobro sin confirmación, pulsa de nuevo **Cobrar venta** y reintenta **Confirmar cobro**. El sistema conserva la misma operación para evitar duplicarla. Mientras se resuelve, no cambies el carrito, no cierres sesión ni reinicies la aplicación. Si el problema persiste, solicita ayuda al responsable y revisa Tickets antes de intentar registrar otra venta equivalente.

La existencia se vuelve a comprobar al guardar. Si otro empleado vendió las últimas unidades, actualiza los datos, revisa las cantidades y atiende el mensaje del sistema.

## 5. Tickets: consultar, descargar, imprimir y cancelar

### Buscar un comprobante

1. Abre **Tickets**. El título de la pantalla es **Historial y tickets**.
2. Escribe el número del ticket o el nombre del cliente en **Ticket o cliente**.
3. Si deseas limitar el periodo, llena **Desde** y **Hasta** con formato `AAAA-MM-DD`, por ejemplo `2026-11-16`.
4. Pulsa **Filtrar**. El inicio no debe ser posterior al final; las fechas indicadas se incluyen en la búsqueda.
5. Usa **Anterior** y **Siguiente** para recorrer resultados.
6. Pulsa **Ver ticket** en la venta que necesitas.

Para ampliar la consulta, borra el texto o las fechas y vuelve a filtrar. La lista muestra número, fecha, cliente, total y estado. El detalle incluye las partidas, cantidades, importes, empleado y método de pago.

<!-- manual-figure:tickets:start -->
### Figura 09. Búsqueda e historial de tickets

![Figura 09. Búsqueda e historial de tickets](manual/anotadas/tickets.svg)

[Abrir captura original](manual/capturas/tickets.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Ticket o cliente:** filtra por número de comprobante o nombre del comprador. |
| 2 | **Desde:** fecha inicial con formato AAAA-MM-DD. |
| 3 | **Hasta:** fecha final incluida en la consulta. |
| 4 | **Filtrar:** aplica las fechas y el texto de búsqueda. |
| 5 | **Tabla de ventas:** muestra ticket, fecha, cliente, total y estado. |
| 6 | **Ver ticket:** abre las partidas y acciones del comprobante elegido. |
| 7 | **Paginación:** Anterior y Siguiente recorren resultados; el contador indica cuántos hay. |

<!-- manual-figure:tickets:end -->

### Descargar o imprimir

- **Descargar PDF:** elige la carpeta y guarda el archivo propuesto, por ejemplo `ticket_25.pdf`.
- **Imprimir:** envía el comprobante a la impresora configurada en ese equipo.
- **Cerrar:** regresa al historial.

Si falla la impresión después de confirmar el cobro, la venta sigue registrada. Corrige la impresora y vuelve a imprimir desde Tickets. El comprobante emitido es un ticket de venta; no es una factura fiscal CFDI.

<!-- manual-figure:ticket:start -->
### Figura 10. Detalle y acciones de un ticket

![Figura 10. Detalle y acciones de un ticket](manual/anotadas/ticket.svg)

[Abrir captura original](manual/capturas/ticket.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Número y estado:** verifica el comprobante y si está completado o cancelado. |
| 2 | **Datos de la venta:** fecha, empleado y cliente. |
| 3 | **Partidas:** revisa productos, cantidades, precios e importes. |
| 4 | **Total y método:** confirma el importe y cómo se registró el pago. |
| 5 | **Cerrar:** vuelve al historial. |
| 6 | **Cancelar venta:** disponible para Administrador y Supervisor. |
| 7 | **Descargar PDF:** guarda una copia del comprobante en el equipo. |
| 8 | **Imprimir:** envía el ticket a la impresora configurada. |

<!-- manual-figure:ticket:end -->

### Cancelar una venta

Esta acción requiere Administrador o Supervisor.

1. Abre el comprobante mediante **Ver ticket**.
2. Revisa que sea la venta correcta y pulsa **Cancelar venta**.
3. Escribe el **Motivo de cancelación**.
4. Pulsa **Confirmar cancelación** y espera el resultado.
5. Comprueba el estado **Cancelada** en el historial.

La cancelación afecta a toda la venta, conserva el comprobante y devuelve sus cantidades al inventario. Si la venta pertenece a un turno cerrado, no se permite cancelarla. El sistema no procesa una devolución bancaria; coordina el reembolso con el procedimiento del negocio.

Ante una respuesta incierta, reintenta desde el mismo formulario. No registres un ajuste adicional para devolver esas existencias: la cancelación ya realiza esa devolución.

<!-- manual-figure:cancelar_venta:start -->
### Figura 11. Formulario de cancelación

![Figura 11. Formulario de cancelación](manual/anotadas/cancelar_venta.svg)

[Abrir captura original](manual/capturas/cancelar_venta.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Ticket e importe:** comprueba que cancelarás la venta correcta. |
| 2 | **Aviso:** la cancelación devuelve existencias y conserva el historial. |
| 3 | **Motivo:** explica por qué se cancela la venta. |
| 4 | **Volver:** abandona el formulario sin cancelar la venta. |
| 5 | **Confirmar cancelación:** registra la cancelación completa del ticket. |

<!-- manual-figure:cancelar_venta:end -->

## 6. Clientes

### Registrar o editar

1. Entra en **Clientes** y pulsa **Nuevo cliente**.
2. Captura el **Nombre**. Correo, teléfono y RFC o identificación fiscal son opcionales.
3. Pulsa **Guardar** y comprueba que aparezca en la lista.

Para editar, busca al cliente por nombre, correo o identificación y pulsa el icono de lápiz. Cambia los datos y guarda. Si no aparece en el selector del carrito, usa el botón superior para actualizar datos.

No es obligatorio crear un cliente para vender: utiliza **Público general** cuando corresponda. El RFC sirve para identificar al comprador; registrarlo no genera una factura fiscal.

<!-- manual-figure:clientes:start -->
### Figura 12. Directorio de clientes

![Figura 12. Directorio de clientes](manual/anotadas/clientes.svg)

[Abrir captura original](manual/capturas/clientes.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Nuevo cliente:** abre el formulario de registro. |
| 2 | **Buscar:** encuentra clientes por nombre, correo o identificación. |
| 3 | **Registros:** indica el número de clientes cargados. |
| 4 | **Datos del cliente:** nombre, correo, teléfono e identificación fiscal. |
| 5 | **Editar:** abre los datos del cliente para corregirlos. |
| 6 | **Eliminar:** solicita borrar un cliente sin ventas; requiere permiso. |

<!-- manual-figure:clientes:end -->

<!-- manual-figure:cliente_formulario:start -->
### Figura 13. Formulario de cliente

![Figura 13. Formulario de cliente](manual/anotadas/cliente_formulario.svg)

[Abrir captura original](manual/capturas/cliente_formulario.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Nombre:** dato obligatorio del cliente. |
| 2 | **Correo:** contacto opcional. |
| 3 | **Teléfono:** contacto opcional. |
| 4 | **RFC o identificación fiscal:** dato opcional; no genera una factura. |
| 5 | **Cancelar:** descarta la captura sin guardar. |
| 6 | **Guardar:** registra los datos del cliente. |

<!-- manual-figure:cliente_formulario:end -->

### Eliminar

Administrador y Supervisor pueden pulsar el icono de eliminación y confirmar. Sólo se permite eliminar clientes sin ventas registradas. Si el cliente tiene historial, conserva el registro y corrige sus datos mediante edición.

## 7. Inventario y categorías

Todos los roles pueden consultar el inventario. Crear, modificar, eliminar, ajustar e importar requiere Administrador o Supervisor.

### Consultar existencias

1. Entra en **Inventario**.
2. Busca por nombre o código de barras.
3. Selecciona una categoría para limitar resultados.
4. Activa **Stock bajo** para ver productos cuya existencia es igual o inferior a su stock mínimo.
5. Revisa costo, precio, margen y existencia. Usa la paginación para consultar más productos.

<!-- manual-figure:inventario:start -->
### Figura 14. Consulta y acciones del inventario

![Figura 14. Consulta y acciones del inventario](manual/anotadas/inventario.svg)

[Abrir captura original](manual/capturas/inventario.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Categorías:** administra las familias de productos. |
| 2 | **Ajustes:** registra entradas, mermas y correcciones. |
| 3 | **Importar Excel:** abre la carga de productos nuevos. |
| 4 | **Nuevo producto:** abre el formulario de alta. |
| 5 | **Buscar y categoría:** filtran el catálogo por texto y familia. |
| 6 | **Stock bajo:** muestra existencias iguales o menores al mínimo. |
| 7 | **Costo, precio, margen y stock:** permiten revisar cada producto antes de operar. |
| 8 | **Añadir al carrito:** prepara una venta con ese producto. |
| 9 | **Editar:** cambia los datos del producto, excepto la existencia. |
| 10 | **Ajustar:** abre un movimiento de inventario del producto. |
| 11 | **Eliminar:** solicita la baja sólo si el historial lo permite. |

<!-- manual-figure:inventario:end -->

<!-- manual-figure:inventario_pie:start -->
### Figura 15. Controles al final del inventario

![Figura 15. Controles al final del inventario](manual/anotadas/inventario_pie.svg)

[Abrir captura original](manual/capturas/inventario_pie.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Paginación:** Anterior y Siguiente recorren productos y muestran el total de coincidencias. |
| 2 | **Nueva categoría:** acceso adicional al alta de familias de productos. |
| 3 | **Aviso de importación:** recuerda que Excel agrega productos nuevos. |

<!-- manual-figure:inventario_pie:end -->

### Crear una categoría

1. Pulsa **Categorías** desde Inventario.
2. Selecciona **Nueva categoría**.
3. Escribe un nombre y, si lo deseas, una descripción.
4. Pulsa **Guardar categoría**.

El icono de lápiz permite editar y el de papelera permite solicitar la eliminación. Una categoría con productos no puede eliminarse; primero cambia esos productos a otra categoría. La flecha superior permite regresar a la vista anterior.

<!-- manual-figure:categorias:start -->
### Figura 16. Listado de categorías

![Figura 16. Listado de categorías](manual/anotadas/categorias.svg)

[Abrir captura original](manual/capturas/categorias.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Nueva categoría:** abre el formulario de alta. |
| 2 | **Nombre, descripción y productos:** muestran cómo se organiza el catálogo. |
| 3 | **Editar:** cambia el nombre o descripción de la categoría. |
| 4 | **Eliminar:** sólo permite borrar categorías sin productos asociados. |

<!-- manual-figure:categorias:end -->

<!-- manual-figure:categoria_formulario:start -->
### Figura 17. Formulario de categoría

![Figura 17. Formulario de categoría](manual/anotadas/categoria_formulario.svg)

[Abrir captura original](manual/capturas/categoria_formulario.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Nombre:** identifica la familia de productos. |
| 2 | **Descripción:** agrega una explicación opcional. |
| 3 | **Cancelar:** cierra sin guardar cambios. |
| 4 | **Guardar categoría:** valida y registra la información. |

<!-- manual-figure:categoria_formulario:end -->

### Crear o editar un producto

1. En Inventario pulsa **Nuevo producto**.
2. Captura nombre y categoría.
3. Agrega código de barras y descripción si los utilizas. El código debe ser único; conserva sus ceros iniciales.
4. Indica costo unitario y precio de venta, con hasta dos decimales.
5. Captura existencia inicial y stock mínimo, con hasta tres decimales y valores no negativos.
6. Pulsa **Guardar producto**.

Para editar datos, utiliza el lápiz de la fila. La existencia de un producto existente se modifica mediante **Ajustes**, no desde la edición. Un producto con ventas o ajustes registrados no puede eliminarse.

<!-- manual-figure:producto_formulario:start -->
### Figura 18. Formulario de producto

![Figura 18. Formulario de producto](manual/anotadas/producto_formulario.svg)

[Abrir captura original](manual/capturas/producto_formulario.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Código de barras:** opcional y único; conserva ceros iniciales. |
| 2 | **Nombre:** identifica el producto en catálogo y tickets. |
| 3 | **Categoría:** selecciona una familia existente. |
| 4 | **Descripción:** información adicional opcional. |
| 5 | **Costo unitario:** indica cuánto cuesta adquirir una unidad. |
| 6 | **Precio de venta:** importe final cobrado al cliente. |
| 7 | **Existencia inicial:** cantidad al crear el producto; después utiliza Ajustes. |
| 8 | **Stock mínimo:** umbral de alerta para reposición. |
| 9 | **Cancelar:** descarta el formulario. |
| 10 | **Guardar producto:** valida y registra el artículo. |

<!-- manual-figure:producto_formulario:end -->

<!-- manual-figure:eliminar_producto:start -->
### Figura 19. Confirmación de eliminación

![Figura 19. Confirmación de eliminación](manual/anotadas/eliminar_producto.svg)

[Abrir captura original](manual/capturas/eliminar_producto.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Registro:** revisa qué producto vas a eliminar. |
| 2 | **Restricciones:** los registros con historial no pueden eliminarse. |
| 3 | **Cancelar:** conserva el producto. |
| 4 | **Eliminar:** solicita la baja; el sistema vuelve a validar las restricciones. |

<!-- manual-figure:eliminar_producto:end -->

### Ajustar existencias

1. Entra en **Inventario → Ajustes**, o utiliza la acción de ajuste de un producto.
2. Busca el producto y pulsa **Ajustar**.
3. En **Cantidad del movimiento**, escribe una cantidad positiva para una entrada o negativa para una salida.
4. Escribe un motivo claro: recepción, merma, daño o corrección de conteo.
5. Pulsa **Aplicar ajuste** y comprueba la existencia resultante.

Ejemplo: si hay 12 unidades y se dañaron 2, escribe `-2`; la existencia resultante será 10. Para aumentar de 12 a 15, escribe `3`, no `15`: el campo indica el movimiento que se suma a la existencia vigente. El resultado nunca puede ser negativo.

Si no se confirma la respuesta, reintenta **Aplicar ajuste** desde el mismo formulario para confirmar la misma operación.

<!-- manual-figure:ajustes:start -->
### Figura 20. Selección de producto para ajustar

![Figura 20. Selección de producto para ajustar](manual/anotadas/ajustes.svg)

[Abrir captura original](manual/capturas/ajustes.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Buscar:** escribe nombre o código; puedes escanear y pulsar Enter. |
| 2 | **Existencia:** consulta el stock antes de elegir el movimiento. |
| 3 | **Ajustar:** abre el formulario del producto de esa fila. |

<!-- manual-figure:ajustes:end -->

<!-- manual-figure:ajuste_formulario:start -->
### Figura 21. Formulario de ajuste de existencias

![Figura 21. Formulario de ajuste de existencias](manual/anotadas/ajuste_formulario.svg)

[Abrir captura original](manual/capturas/ajuste_formulario.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Producto y existencia:** confirma sobre qué artículo aplicarás el movimiento. |
| 2 | **Cantidad del movimiento:** positiva para entrada y negativa para salida; no es la existencia final. |
| 3 | **Motivo:** explica la recepción, merma o corrección. |
| 4 | **Cancelar:** cierra sin registrar el ajuste. |
| 5 | **Aplicar ajuste:** guarda el movimiento y actualiza el stock. |

<!-- manual-figure:ajuste_formulario:end -->

## 8. Importar productos desde Excel

La importación agrega productos nuevos. Para modificar existencias de productos ya registrados, utiliza Ajustes.

1. Abre **Inventario → Importar Excel**.
2. Pulsa **Descargar plantilla** y guarda el archivo.
3. Llena la hoja **Inventario** con una fila por producto nuevo.
4. Conserva los encabezados y usa nombres de categorías que ya existan.
5. Guarda el archivo en formato `.xlsx`.
6. En Punto pulsa **Seleccionar Excel** y revisa la vista previa.
7. Si hay errores, corrige las filas y columnas indicadas y selecciona el archivo nuevamente.
8. Si la validación es correcta, pulsa **Confirmar importación**.

| Columna de la plantilla | Qué escribir |
| --- | --- |
| codigo_barras | Código opcional como texto; no lo repitas y conserva ceros iniciales. |
| nombre | Nombre del producto. |
| categoria | Nombre de una categoría existente. |
| descripcion | Descripción opcional. |
| precio_compra | Costo unitario, hasta dos decimales. |
| precio_venta | Precio final de venta, hasta dos decimales. |
| stock_actual | Existencia inicial, hasta tres decimales. |
| stock_minimo | Umbral de alerta, hasta tres decimales. |

El límite es de 5 MB y 5,000 productos. No utilices fórmulas. Si una fila falla, no se guarda ninguna. La vista previa presenta hasta 10 filas y hasta 30 errores, pero la validación y el guardado abarcan todo el archivo. Los códigos de barras ya existentes se rechazan.

<!-- manual-figure:importar:start -->
### Figura 22. Asistente de importación antes de elegir un archivo

![Figura 22. Asistente de importación antes de elegir un archivo](manual/anotadas/importar.svg)

[Abrir captura original](manual/capturas/importar.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Instrucciones:** explican el orden de descarga, llenado, revisión y confirmación. |
| 2 | **Descargar plantilla:** guarda el Excel con los encabezados correctos. |
| 3 | **Seleccionar Excel:** abre el selector de archivos .xlsx. |
| 4 | **Archivo seleccionado:** aquí aparecerá el nombre del documento elegido. |
| 5 | **Cerrar:** abandona el asistente sin importar. |
| 6 | **Confirmar importación:** permanece deshabilitado hasta validar un archivo. |

<!-- manual-figure:importar:end -->

<!-- manual-figure:importar_validado:start -->
### Figura 23. Vista previa de una importación válida

![Figura 23. Vista previa de una importación válida](manual/anotadas/importar_validado.svg)

[Abrir captura original](manual/capturas/importar_validado.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Nombre de archivo:** comprueba que hayas elegido el documento correcto. |
| 2 | **Resultado de validación:** indica cuántos productos están listos para importar. |
| 3 | **Vista previa:** revisa producto, categoría, precio y existencia antes de guardar. |
| 4 | **Confirmar importación:** guarda el lote validado; si falla una fila, no se guarda ninguna. |
| 5 | **Cerrar:** permite salir sin confirmar la carga. |

<!-- manual-figure:importar_validado:end -->

## 9. Cierre y consulta de caja

### Cerrar el turno

1. Comprueba que tus cobros estén confirmados.
2. Entra en **Caja → Corte**.
3. Revisa el **Fondo inicial**, **Efectivo esperado** y número de tickets.
4. Cuenta físicamente el efectivo de la caja.
5. Pulsa **Cerrar caja**.
6. Reemplaza el valor de **Efectivo contado** con tu conteo real y agrega notas si hay alguna diferencia.
7. Pulsa **Confirmar cierre**.
8. Comprueba que la caja figure como **Cerrada** y revisa la diferencia guardada.

El efectivo esperado es el fondo inicial más las ventas completadas en efectivo del turno. Los cobros con tarjeta o transferencia no se suman al efectivo físico.

Ejemplo: un fondo de $500.00 más $750.00 vendidos en efectivo da $1,250.00 esperados. Si cuentas $1,240.00, la diferencia es de -$10.00. Una diferencia positiva indica más efectivo contado que esperado.

El sistema propone el efectivo esperado en el formulario; verifica el conteo antes de confirmar. Un turno cerrado conserva sus importes y sus ventas ya no pueden cancelarse. Para seguir cobrando después del cierre, abre un turno nuevo.

### Consultar turnos anteriores

En **Turnos registrados**, revisa apertura, estado, efectivo esperado, contado y diferencia. El Cajero consulta sus propios turnos; Administrador y Supervisor pueden consultar el historial de todos.

<!-- manual-figure:corte:start -->
### Figura 24. Estado y conciliación de caja

![Figura 24. Estado y conciliación de caja](manual/anotadas/corte.svg)

[Abrir captura original](manual/capturas/corte.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Cerrar caja:** abre el formulario de conteo físico. |
| 2 | **Estado:** indica si tu turno está abierto. |
| 3 | **Fondo inicial:** efectivo registrado al abrir el turno. |
| 4 | **Efectivo esperado:** fondo más ventas completadas en efectivo del turno. |
| 5 | **Tickets del turno:** número de comprobantes, incluidos los cancelados. |
| 6 | **Historial:** muestra apertura, estado, efectivo esperado, contado y diferencia. |

<!-- manual-figure:corte:end -->

<!-- manual-figure:cerrar_caja:start -->
### Figura 25. Formulario de cierre de turno

![Figura 25. Formulario de cierre de turno](manual/anotadas/cerrar_caja.svg)

[Abrir captura original](manual/capturas/cerrar_caja.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Efectivo contado:** reemplaza el valor propuesto por el conteo físico real. |
| 2 | **Notas del cierre:** explica diferencias o incidencias si corresponde. |
| 3 | **Cancelar:** conserva abierto el turno sin confirmar el cierre. |
| 4 | **Confirmar cierre:** guarda contado, esperado y diferencia y termina el turno. |

<!-- manual-figure:cerrar_caja:end -->

## 10. Usuarios y permisos de acceso

Esta sección está disponible para Administrador.

### Crear un empleado

1. Abre **Usuarios** y pulsa **Nuevo usuario**.
2. Captura nombre, apellidos, correo y teléfono opcional.
3. Selecciona **Cajero**, **Supervisor** o **Administrador**.
4. Mantén **Acceso activo** habilitado para permitir el inicio de sesión.
5. Define una **Contraseña inicial** de al menos 12 caracteres y hasta 72 bytes. Los caracteres acentuados pueden ocupar más de un byte.
6. Pulsa **Guardar** y entrega las credenciales al empleado por un medio privado.

<!-- manual-figure:usuarios:start -->
### Figura 26. Administración de usuarios

![Figura 26. Administración de usuarios](manual/anotadas/usuarios.svg)

[Abrir captura original](manual/capturas/usuarios.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Nuevo usuario:** abre el alta de un empleado. |
| 2 | **Buscar:** localiza al empleado por sus datos. |
| 3 | **Rol:** identifica si la cuenta es Administrador, Supervisor o Cajero. |
| 4 | **Editar:** cambia datos, rol, estado o contraseña de otra cuenta. |
| 5 | **Desactivar:** retira el acceso y conserva el historial. |

<!-- manual-figure:usuarios:end -->

<!-- manual-figure:usuario_formulario:start -->
### Figura 27. Formulario de empleado

![Figura 27. Formulario de empleado](manual/anotadas/usuario_formulario.svg)

[Abrir captura original](manual/capturas/usuario_formulario.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Nombre y apellidos:** identifican al empleado. |
| 2 | **Correo:** será su identificador de acceso. |
| 3 | **Teléfono:** contacto opcional. |
| 4 | **Rol:** define los permisos de la cuenta. |
| 5 | **Acceso activo:** habilita o impide iniciar sesión. |
| 6 | **Contraseña inicial:** mínimo 12 caracteres; al editar es opcional si no se cambia. |
| 7 | **Mostrar contraseña:** revisa el dato capturado mediante el icono del ojo. |
| 8 | **Cancelar:** descarta los cambios del formulario. |
| 9 | **Guardar:** valida y registra al empleado. |

<!-- manual-figure:usuario_formulario:end -->

### Editar o desactivar

Usa el lápiz para editar un empleado. Si dejas vacía **Nueva contraseña (opcional)**, conserva su contraseña actual. Usa **Acceso activo** o la acción **Desactivar empleado** para retirar el acceso sin borrar el historial.

Cambiar correo, contraseña, rol o estado invalida las sesiones anteriores de esa cuenta. No puedes desactivar tu propia cuenta ni quitarte el rol Administrador; debe permanecer al menos un administrador activo. Para cambiar tu propio correo o contraseña, utiliza Configuración.

<!-- manual-figure:desactivar_usuario:start -->
### Figura 28. Confirmación de desactivación

![Figura 28. Confirmación de desactivación](manual/anotadas/desactivar_usuario.svg)

[Abrir captura original](manual/capturas/desactivar_usuario.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Empleado:** confirma a quién retirarás el acceso. |
| 2 | **Conservación del historial:** las ventas anteriores permanecen registradas. |
| 3 | **Cancelar:** conserva el acceso actual. |
| 4 | **Desactivar:** confirma la baja de acceso del empleado. |

<!-- manual-figure:desactivar_usuario:end -->

## 11. Reportes

1. Abre **Reportes**.
2. Selecciona la pestaña y el periodo: **Últimos 7 días** o **Últimos 30 días**.
3. Revisa los indicadores y utiliza **Anterior** o **Siguiente** para recorrer la tabla.
4. Pulsa **Exportar CSV**, elige una carpeta y guarda el archivo.

| Pestaña | Información |
| --- | --- |
| Ventas | Tickets, fechas, métodos de pago e importes del periodo. |
| Clientes | Cantidad de ventas, importe y promedio por cliente; incluye Público general. |
| Usuarios | Resultados por empleado; requiere Administrador. |
| Predicciones | Unidades vendidas, promedio diario, existencia y reposición sugerida. |

Los resultados de ventas excluyen las canceladas. La exportación incluye todas las filas del reporte, no sólo la página visible. La gráfica de tendencia conserva los últimos siete días aunque selecciones un periodo de 30 días para el reporte.

La reposición sugerida busca cubrir el mayor valor entre el stock mínimo y siete días de demanda media, descontando la existencia actual. Es una estimación basada en ventas del periodo; revisa temporadas, entregas y necesidades del negocio antes de comprar mercancía.

<!-- manual-figure:reporte_ventas:start -->
### Figura 29. Panel de reportes

![Figura 29. Panel de reportes](manual/anotadas/reporte_ventas.svg)

[Abrir captura original](manual/capturas/reporte_ventas.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Periodo:** selecciona los últimos 7 o 30 días. |
| 2 | **Exportar CSV:** guarda todas las filas del reporte seleccionado. |
| 3 | **Pestañas:** Ventas, Clientes, Usuarios y Predicciones cambian el análisis; Usuarios requiere Administrador. |
| 4 | **Indicadores:** resumen importes, operaciones, promedio y clientes. |
| 5 | **Tendencia:** gráfica de los últimos siete días. |
| 6 | **Tabla:** muestra el detalle del reporte; desplázate hacia abajo para sus controles finales. |

<!-- manual-figure:reporte_ventas:end -->

<!-- manual-figure:reporte_tabla:start -->
### Figura 30. Paginación del reporte y acceso a tickets

![Figura 30. Paginación del reporte y acceso a tickets](manual/anotadas/reporte_tabla.svg)

[Abrir captura original](manual/capturas/reporte_tabla.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Paginación:** recorre las páginas del reporte sin cambiar el periodo. |
| 2 | **Historial y tickets:** permite abrir los comprobantes desde el reporte de ventas. |

<!-- manual-figure:reporte_tabla:end -->

<!-- manual-figure:reporte_predicciones:start -->
### Figura 31. Reposición sugerida

![Figura 31. Reposición sugerida](manual/anotadas/reporte_predicciones.svg)

[Abrir captura original](manual/capturas/reporte_predicciones.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Unidades vendidas y promedio diario:** resumen la demanda del periodo. |
| 2 | **Existencia:** cantidad disponible de cada producto. |
| 3 | **Reposición:** cantidad sugerida para cubrir el objetivo de stock. |
| 4 | **Ejemplo:** el café sugiere reponer 2 unidades porque tiene 8 y su mínimo es 10. |

<!-- manual-figure:reporte_predicciones:end -->

## 12. Configuración personal e impresoras

### Apariencia

Abre **Configuración → Aspectos** y elige **Tema claro** o **Tema oscuro**. La preferencia se conserva en ese equipo.

<!-- manual-figure:aspectos:start -->
### Figura 32. Apariencia y estado de conexión

![Figura 32. Apariencia y estado de conexión](manual/anotadas/aspectos.svg)

[Abrir captura original](manual/capturas/aspectos.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Pestañas de configuración:** Periféricos, Aspectos, Contraseña y Correo. |
| 2 | **Tema claro:** aplica y conserva una apariencia clara en este equipo. |
| 3 | **Tema oscuro:** aplica y conserva una apariencia oscura en este equipo. |
| 4 | **Conexión y sincronización:** muestra el modo y los eventos pendientes. |
| 5 | **Sincronizar ahora:** se habilita en una instalación con sincronización configurada; en demo está deshabilitado. |

<!-- manual-figure:aspectos:end -->

### Contraseña y correo

En **Configuración → Contraseña**, captura tu contraseña actual, la nueva y su confirmación; pulsa **Cambiar contraseña**. La nueva debe cumplir el mínimo de 12 caracteres y el límite de 72 bytes.

En **Configuración → Correo**, confirma tu contraseña actual, escribe el nuevo correo y pulsa **Guardar correo**. Utiliza ese correo para los siguientes accesos.

Al guardar estos cambios se renueva tu sesión actual y se invalidan las anteriores. Si olvidaste la contraseña, solicita su recuperación al administrador; no hay un envío automático de recuperación por correo.

<!-- manual-figure:contrasena:start -->
### Figura 33. Cambio de contraseña propia

![Figura 33. Cambio de contraseña propia](manual/anotadas/contrasena.svg)

[Abrir captura original](manual/capturas/contrasena.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Contraseña actual:** confirma tu identidad antes del cambio. |
| 2 | **Nueva contraseña:** escribe la nueva clave de acceso. |
| 3 | **Confirmar:** repite exactamente la nueva contraseña. |
| 4 | **Mostrar:** los iconos del ojo revelan temporalmente los campos que lo permiten. |
| 5 | **Cambiar contraseña:** guarda el cambio y renueva la sesión actual. |

<!-- manual-figure:contrasena:end -->

<!-- manual-figure:correo:start -->
### Figura 34. Cambio del correo de acceso

![Figura 34. Cambio del correo de acceso](manual/anotadas/correo.svg)

[Abrir captura original](manual/capturas/correo.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Contraseña actual:** confirma tu identidad. |
| 2 | **Nuevo correo de acceso:** sustituye el correo actual por el que utilizarás al entrar. |
| 3 | **Guardar correo:** actualiza el acceso y renueva la sesión. |

<!-- manual-figure:correo:end -->

### Impresora

1. Abre **Configuración → Periféricos**.
2. En **Conexión**, selecciona USB, Serial / COM o Red / Ethernet.
3. Captura los datos de tu dispositivo según la tabla siguiente. Solicítalos al responsable de la instalación si no los conoces.
4. Decide si se debe **Cortar papel al terminar**, cuando el modelo lo admita.
5. Pulsa **Guardar configuración** y después **Imprimir prueba**.

| Conexión | Datos necesarios |
| --- | --- |
| USB | Identificador del fabricante y del producto; por ejemplo, valores con formato `0x04b8`. |
| Serial / COM | Puerto o dispositivo y velocidad en baudios. |
| Red / Ethernet | Dirección de la impresora y puerto de red. |

La impresora debe ser compatible con ESC/POS y contar con los controladores o permisos necesarios. Verifica alimentación, papel y conexión antes de imprimir. La configuración de impresora se guarda en cada equipo.

Los lectores de códigos que funcionan como teclado se utilizan directamente en el buscador del Carrito; no necesitan configurarse como impresoras.

<!-- manual-figure:perifericos:start -->
### Figura 35. Impresora USB

![Figura 35. Impresora USB](manual/anotadas/perifericos.svg)

[Abrir captura original](manual/capturas/perifericos.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Conexión:** elige USB, Serial / COM o Red / Ethernet. |
| 2 | **Fabricante:** escribe el identificador USB proporcionado para tu modelo. |
| 3 | **Producto:** escribe el identificador USB del dispositivo. |
| 4 | **Cortar papel:** habilita el corte si el equipo lo admite. |
| 5 | **Guardar configuración:** conserva los parámetros de este equipo. |
| 6 | **Imprimir prueba:** envía un comprobante físico; verifica papel y conexión. |
| 7 | **Sincronización:** consulta el modo y la disponibilidad de envío de pendientes. |

<!-- manual-figure:perifericos:end -->

<!-- manual-figure:perifericos_serial:start -->
### Figura 36. Impresora Serial / COM

![Figura 36. Impresora Serial / COM](manual/anotadas/perifericos_serial.svg)

[Abrir captura original](manual/capturas/perifericos_serial.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Conexión Serial / COM:** muestra los parámetros de un dispositivo serial. |
| 2 | **Puerto o dispositivo:** escribe el puerto asignado, por ejemplo COM3. |
| 3 | **Baudios:** debe coincidir con la velocidad configurada en la impresora. |
| 4 | **Guardar e imprimir prueba:** conserva los parámetros y comprueba la conexión. |

<!-- manual-figure:perifericos_serial:end -->

<!-- manual-figure:perifericos_red:start -->
### Figura 37. Impresora de red

![Figura 37. Impresora de red](manual/anotadas/perifericos_red.svg)

[Abrir captura original](manual/capturas/perifericos_red.png). Datos ficticios; los números corresponden a la tabla siguiente.

| N.º | Elemento y función |
| --- | --- |
| 1 | **Conexión Red / Ethernet:** muestra los datos de una impresora de red. |
| 2 | **Dirección:** utiliza la dirección real de tu impresora; la imagen contiene una dirección de ejemplo. |
| 3 | **Puerto de red:** debe coincidir con el puerto de impresión configurado. |
| 4 | **Guardar e imprimir prueba:** conserva los datos y envía una prueba física. |

<!-- manual-figure:perifericos_red:end -->

### Conexión y sincronización

Este panel muestra el modo de conexión y, si hay una instalación local preparada, los eventos pendientes o en conflicto. La configuración actual con base en la nube no permite continuar guardando ventas sin internet. Una instalación local requiere preparación del responsable técnico; seleccionar demo no activa una operación local real.

Si se muestran conflictos de sincronización, informa al responsable antes de reintentar. No recrees las ventas o ajustes manualmente en otra base para intentar sincronizarlos.

## 13. Problemas frecuentes

| Situación | Qué hacer |
| --- | --- |
| No puedo iniciar sesión | Revisa correo y contraseña. Solicita al administrador que confirme que la cuenta está activa. |
| La sesión expiró o fue invalidada | Vuelve a iniciar sesión. Si un cobro quedó sin confirmar, informa al responsable para revisar el ticket antes de repetirlo. |
| No se puede conectar al servicio | Comprueba internet y solicita verificar que el servicio esté iniciado. No cambies a demo para registrar ventas reales. |
| Cobrar venta está deshabilitado | Agrega productos y abre tu turno en Caja → Corte. |
| No hay stock suficiente | Actualiza los datos y revisa la cantidad. Un Supervisor o Administrador debe revisar cualquier diferencia física de inventario. |
| No se encuentra un código de barras | Revisa el código y sus ceros iniciales. Busca por nombre o solicita revisar el catálogo. |
| No aparecen tickets | Borra filtros, revisa el formato y orden de las fechas y actualiza los datos. |
| Una escritura se guardó, pero el catálogo no se actualizó | Pulsa el botón superior de actualización antes de la siguiente venta. Evita repetir la operación que ya fue confirmada. |
| Un cobro, ajuste o cierre no tuvo confirmación | Reintenta desde el mismo formulario, conservando los datos. Si persiste, pide ayuda antes de iniciar otra operación equivalente. |
| No puedo cancelar una venta | Revisa tu rol, el estado de la venta y si su turno ya se cerró. |
| No puedo eliminar un registro | Puede tener historial relacionado o estar fuera de tus permisos. Utiliza edición o desactivación cuando corresponda. |
| Excel tiene errores | Revisa la fila, columna y explicación indicadas. Corrige el archivo y vuelve a seleccionarlo. |
| La impresora falla | Revisa papel, alimentación, conexión y configuración; utiliza Imprimir prueba. Reimprime el ticket sin repetir la venta. |

Al pedir soporte, indica la pantalla, el texto del mensaje y el número de ticket o turno cuando exista. No envíes contraseñas.

## 14. Guía rápida de una jornada

1. Inicia sesión con tu cuenta y comprueba que estés en operación real.
2. Actualiza los datos y abre tu turno con el fondo inicial contado.
3. Revisa que la impresora y el lector funcionen.
4. Registra productos, cantidades y cliente en el carrito.
5. Cobra, espera la confirmación y entrega el ticket.
6. Consulta Tickets para reimprimir; solicita autorización operativa al responsable cuando necesites una cancelación.
7. Resuelve cualquier operación sin confirmación antes de terminar.
8. Cuenta el efectivo, registra el cierre y revisa la diferencia.
9. Cierra sesión mediante Salir.

## 15. Glosario

| Término | Significado |
| --- | --- |
| Carrito | Lista de productos y cantidades que preparas antes del cobro. |
| Ticket | Comprobante de una venta registrada. |
| Turno | Periodo de operación de caja de un empleado, desde apertura hasta cierre. |
| Fondo inicial | Efectivo que se registra al abrir un turno. |
| Efectivo esperado | Fondo inicial más ventas completadas en efectivo del turno. |
| Diferencia de caja | Efectivo contado menos efectivo esperado. |
| Existencia o stock | Cantidad disponible de un producto. |
| Stock mínimo | Cantidad que activa una alerta de reposición al alcanzarla o quedar por debajo. |
| Ajuste | Entrada o salida de inventario acompañada de un motivo. |
| CSV | Archivo de tabla que puede abrirse en una hoja de cálculo. |
| Demo | Modo con datos ficticios en memoria para practicar. |

Para instalación, recuperación administrativa de cuentas y soporte técnico, consulta [Operación del punto de venta](operacion.md).
