"""Referencias visuales: coordenadas sobre capturas reales de 1440 × 1080."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Marker:
    text: str
    target: tuple[int, int]
    position: tuple[int, int]


@dataclass(frozen=True)
class Figure:
    scene: str
    title: str
    before: str
    crop: tuple[int, int, int, int]
    markers: tuple[Marker, ...]


def point(text, x, y, position=None):
    return Marker(text, (x, y), position or (x - 40, y))


FIGURES = (
    Figure(
        "login",
        "Inicio de sesión",
        "### Qué puede hacer cada rol",
        (220, 130, 550, 490),
        (
            point(
                "Correo: escribe el correo de acceso que te entregó el administrador.",
                275,
                302,
                (243, 302),
            ),
            point(
                "Contraseña: captura tu contraseña; no se muestra en esta imagen.",
                275,
                370,
                (243, 370),
            ),
            point(
                "Mostrar contraseña: el icono del ojo permite revisar lo escrito.",
                555,
                370,
                (610, 370),
            ),
            point(
                "Entrar al sistema: valida los datos e inicia la sesión.",
                360,
                468,
                (478, 468),
            ),
        ),
    ),
    Figure(
        "sesion",
        "Controles de una sesión activa",
        "## 2. Navegación por el sistema",
        (0, 0, 1440, 1080),
        (
            point(
                "Actualizar: vuelve a consultar los datos del servicio.",
                1283,
                42,
                (1283, 86),
            ),
            point(
                "Modo de conexión: identifica la operación configurada; aquí se ilustra con datos ficticios.",
                1375,
                42,
                (1375, 86),
            ),
            point(
                "Cuenta y rol: verifica qué empleado está utilizando el equipo.",
                110,
                1003,
                (190, 1003),
            ),
            point(
                "Salir: termina la sesión; no sustituye el cierre del turno.",
                45,
                1046,
                (145, 1046),
            ),
            point(
                "Volver: regresa a la vista anterior cuando hay historial.",
                272,
                126,
                (326, 126),
            ),
        ),
    ),
    Figure(
        "inicio",
        "Mapa de la pantalla principal",
        "## 3. Apertura del turno",
        (0, 0, 1440, 1080),
        (
            point(
                "Menú principal: Caja, Carrito, Tickets, Inventario, Clientes, Reportes y Usuarios abren sus respectivas vistas.",
                108,
                322,
                (205, 322),
            ),
            point(
                "Configuración: abre las preferencias, datos de acceso y periféricos.",
                112,
                969,
                (205, 969),
            ),
            point(
                "Buscar vistas: escribe un nombre y pulsa Enter; Ctrl + K enfoca el campo.",
                1090,
                42,
                (1090, 89),
            ),
            point(
                "Indicador de modo: DEMO identifica datos ficticios para practicar.",
                1336,
                42,
                (1336, 89),
            ),
            point(
                "Pestañas Inicio y Corte: alternan entre el resumen y la operación de caja.",
                346,
                246,
                (346, 211),
            ),
            point(
                "Nueva venta: abre el Carrito para preparar un cobro.",
                1340,
                176,
                (1340, 222),
            ),
            point(
                "Indicadores: resumen ventas, tickets, promedio y alertas de existencias.",
                810,
                320,
                (810, 272),
            ),
            point(
                "Actividad de ventas: muestra la tendencia de los últimos siete días.",
                620,
                505,
                (620, 459),
            ),
            point(
                "Ver corte de caja: abre el estado y cierre del turno.",
                1142,
                692,
                (1265, 692),
            ),
            point(
                "Revisar inventario: permite consultar existencias y alertas.",
                1145,
                742,
                (1270, 742),
            ),
            point(
                "Ver reporte: abre los resultados de ventas.", 1338, 842, (1338, 796)
            ),
            point(
                "Cuenta: identifica al empleado y su rol actual.",
                110,
                1044,
                (205, 1044),
            ),
        ),
    ),
    Figure(
        "buscar_vista",
        "Resultados del buscador de vistas",
        "## 3. Apertura del turno",
        (475, 20, 500, 235),
        (
            point("Inventario: abre el listado de productos.", 533, 113, (500, 113)),
            point("Categorías: abre las familias de productos.", 533, 155, (500, 155)),
            point(
                "Ajustes: abre los movimientos de existencias.", 533, 197, (500, 197)
            ),
        ),
    ),
    Figure(
        "caja_cerrada",
        "Caja antes de abrir un turno",
        "## 4. Registro y cobro de ventas",
        (235, 145, 1190, 570),
        (
            point(
                "Abrir caja: abre el formulario del fondo inicial.",
                1349,
                200,
                (1349, 245),
            ),
            point(
                "Estado: Cerrada indica que debes abrir tu turno antes de cobrar.",
                390,
                326,
                (485, 326),
            ),
            point(
                "Fondo, efectivo y tickets: muestran valores del turno cuando está abierto.",
                940,
                326,
                (940, 276),
            ),
            point(
                "Turnos registrados: conserva los cierres anteriores para consultarlos.",
                487,
                565,
                (487, 610),
            ),
        ),
    ),
    Figure(
        "abrir_caja",
        "Formulario de apertura",
        "## 4. Registro y cobro de ventas",
        (430, 390, 580, 300),
        (
            point(
                "Fondo inicial: escribe el efectivo físico con el que inicias el turno.",
                495,
                520,
                (455, 520),
            ),
            point(
                "Cancelar: cierra el formulario sin abrir el turno.",
                770,
                617,
                (770, 574),
            ),
            point(
                "Abrir turno: confirma el fondo y habilita los cobros.",
                886,
                617,
                (886, 574),
            ),
        ),
    ),
    Figure(
        "carrito",
        "Preparación de una venta",
        "### Cobrar",
        (240, 145, 1185, 910),
        (
            point(
                "Buscar o escanear: localiza productos por nombre o código.",
                275,
                340,
                (250, 340),
            ),
            point(
                "Agregar: el botón + o la tarjeta añaden una unidad del producto.",
                768,
                410,
                (768, 368),
            ),
            point(
                "Cliente: selecciona un cliente registrado o Público general.",
                980,
                344,
                (1095, 344),
            ),
            point(
                "Cantidad: escribe el valor y pulsa Enter para aplicarlo.",
                1078,
                467,
                (1078, 419),
            ),
            point("Quitar: retira esa partida del carrito.", 1246, 467, (1302, 467)),
            point(
                "Total: revisa el importe y el desglose de impuesto incluido.",
                1294,
                650,
                (1294, 600),
            ),
            point("Cobrar venta: abre el formulario de pago.", 936, 738, (1063, 738)),
            point(
                "Vaciar carrito: quita todos los productos de la venta en preparación.",
                940,
                788,
                (1065, 788),
            ),
        ),
    ),
    Figure(
        "cobrar",
        "Formulario de cobro",
        "### Si el cobro queda sin confirmación",
        (430, 265, 580, 550),
        (
            point(
                "Total: confirma cuánto debe pagar el cliente.", 498, 389, (455, 389)
            ),
            point(
                "Método de pago: selecciona Efectivo, Tarjeta o Transferencia según corresponda.",
                495,
                457,
                (455, 457),
            ),
            point(
                "Efectivo recibido: captura el importe entregado; debe cubrir el total.",
                495,
                523,
                (455, 523),
            ),
            point(
                "Cambio: indica cuánto debes devolver al cliente.", 495, 580, (455, 580)
            ),
            point(
                "Volver: regresa al carrito sin confirmar el cobro.",
                724,
                749,
                (724, 711),
            ),
            point(
                "Confirmar cobro: registra la venta y abre su comprobante al confirmarse.",
                859,
                749,
                (978, 749),
            ),
        ),
    ),
    Figure(
        "tickets",
        "Búsqueda e historial de tickets",
        "### Descargar o imprimir",
        (240, 145, 1185, 910),
        (
            point(
                "Ticket o cliente: filtra por número de comprobante o nombre del comprador.",
                275,
                300,
                (250, 300),
            ),
            point("Desde: fecha inicial con formato AAAA-MM-DD.", 830, 300, (830, 252)),
            point(
                "Hasta: fecha final incluida en la consulta.", 1015, 300, (1015, 252)
            ),
            point(
                "Filtrar: aplica las fechas y el texto de búsqueda.",
                1254,
                301,
                (1254, 252),
            ),
            point(
                "Tabla de ventas: muestra ticket, fecha, cliente, total y estado.",
                622,
                365,
                (622, 410),
            ),
            point(
                "Ver ticket: abre las partidas y acciones del comprobante elegido.",
                876,
                495,
                (1000, 495),
            ),
            point(
                "Paginación: Anterior y Siguiente recorren resultados; el contador indica cuántos hay.",
                450,
                998,
                (450, 1040),
            ),
        ),
    ),
    Figure(
        "ticket",
        "Detalle y acciones de un ticket",
        "### Cancelar una venta",
        (285, 190, 870, 700),
        (
            point(
                "Número y estado: verifica el comprobante y si está completado o cancelado.",
                340,
                304,
                (306, 304),
            ),
            point(
                "Datos de la venta: fecha, empleado y cliente.", 340, 373, (306, 373)
            ),
            point(
                "Partidas: revisa productos, cantidades, precios e importes.",
                340,
                477,
                (306, 477),
            ),
            point(
                "Total y método: confirma el importe y cómo se registró el pago.",
                340,
                647,
                (306, 647),
            ),
            point("Cerrar: vuelve al historial.", 593, 821, (593, 778)),
            point(
                "Cancelar venta: disponible para Administrador y Supervisor.",
                726,
                821,
                (726, 778),
            ),
            point(
                "Descargar PDF: guarda una copia del comprobante en el equipo.",
                894,
                821,
                (894, 778),
            ),
            point(
                "Imprimir: envía el ticket a la impresora configurada.",
                1040,
                821,
                (1040, 778),
            ),
        ),
    ),
    Figure(
        "cancelar_venta",
        "Formulario de cancelación",
        "## 6. Clientes",
        (405, 325, 630, 435),
        (
            point(
                "Ticket e importe: comprueba que cancelarás la venta correcta.",
                470,
                439,
                (434, 439),
            ),
            point(
                "Aviso: la cancelación devuelve existencias y conserva el historial.",
                470,
                501,
                (434, 501),
            ),
            point("Motivo: explica por qué se cancela la venta.", 470, 573, (434, 573)),
            point(
                "Volver: abandona el formulario sin cancelar la venta.",
                727,
                689,
                (727, 645),
            ),
            point(
                "Confirmar cancelación: registra la cancelación completa del ticket.",
                875,
                689,
                (998, 689),
            ),
        ),
    ),
    Figure(
        "clientes",
        "Directorio de clientes",
        "### Eliminar",
        (240, 145, 1185, 560),
        (
            point(
                "Nuevo cliente: abre el formulario de registro.", 1336, 200, (1336, 245)
            ),
            point(
                "Buscar: encuentra clientes por nombre, correo o identificación.",
                275,
                297,
                (250, 297),
            ),
            point(
                "Registros: indica el número de clientes cargados.",
                1352,
                297,
                (1352, 344),
            ),
            point(
                "Datos del cliente: nombre, correo, teléfono e identificación fiscal.",
                490,
                415,
                (490, 364),
            ),
            point(
                "Editar: abre los datos del cliente para corregirlos.",
                711,
                415,
                (711, 360),
            ),
            point(
                "Eliminar: solicita borrar un cliente sin ventas; requiere permiso.",
                751,
                415,
                (815, 415),
            ),
        ),
    ),
    Figure(
        "cliente_formulario",
        "Formulario de cliente",
        "### Eliminar",
        (410, 270, 620, 540),
        (
            point("Nombre: dato obligatorio del cliente.", 475, 396, (437, 396)),
            point("Correo: contacto opcional.", 475, 478, (437, 478)),
            point("Teléfono: contacto opcional.", 475, 560, (437, 560)),
            point(
                "RFC o identificación fiscal: dato opcional; no genera una factura.",
                475,
                642,
                (437, 642),
            ),
            point("Cancelar: descarta la captura sin guardar.", 807, 742, (807, 701)),
            point("Guardar: registra los datos del cliente.", 915, 742, (997, 742)),
        ),
    ),
    Figure(
        "inventario",
        "Consulta y acciones del inventario",
        "### Crear una categoría",
        (240, 145, 1185, 910),
        (
            point(
                "Categorías: administra las familias de productos.",
                865,
                200,
                (865, 246),
            ),
            point(
                "Ajustes: registra entradas, mermas y correcciones.",
                1003,
                200,
                (1003, 246),
            ),
            point(
                "Importar Excel: abre la carga de productos nuevos.",
                1152,
                200,
                (1152, 246),
            ),
            point(
                "Nuevo producto: abre el formulario de alta.", 1329, 200, (1329, 246)
            ),
            point(
                "Buscar y categoría: filtran el catálogo por texto y familia.",
                670,
                466,
                (670, 419),
            ),
            point(
                "Stock bajo: muestra existencias iguales o menores al mínimo.",
                1291,
                467,
                (1291, 419),
            ),
            point(
                "Costo, precio, margen y stock: permiten revisar cada producto antes de operar.",
                699,
                529,
                (699, 574),
            ),
            point(
                "Añadir al carrito: prepara una venta con ese producto.",
                960,
                586,
                (960, 548),
            ),
            point(
                "Editar: cambia los datos del producto, excepto la existencia.",
                1000,
                586,
                (1000, 625),
            ),
            point(
                "Ajustar: abre un movimiento de inventario del producto.",
                1040,
                586,
                (1040, 548),
            ),
            point(
                "Eliminar: solicita la baja sólo si el historial lo permite.",
                1080,
                586,
                (1140, 586),
            ),
        ),
    ),
    Figure(
        "inventario_pie",
        "Controles al final del inventario",
        "### Crear una categoría",
        (240, 650, 1185, 405),
        (
            point(
                "Paginación: Anterior y Siguiente recorren productos y muestran el total de coincidencias.",
                450,
                900,
                (450, 850),
            ),
            point(
                "Nueva categoría: acceso adicional al alta de familias de productos.",
                1310,
                950,
                (1310, 900),
            ),
            point(
                "Aviso de importación: recuerda que Excel agrega productos nuevos.",
                500,
                1033,
                (700, 1005),
            ),
        ),
    ),
    Figure(
        "categorias",
        "Listado de categorías",
        "### Crear o editar un producto",
        (240, 145, 1185, 510),
        (
            point(
                "Nueva categoría: abre el formulario de alta.", 1328, 200, (1328, 246)
            ),
            point(
                "Nombre, descripción y productos: muestran cómo se organiza el catálogo.",
                476,
                300,
                (476, 254),
            ),
            point(
                "Editar: cambia el nombre o descripción de la categoría.",
                583,
                357,
                (583, 315),
            ),
            point(
                "Eliminar: sólo permite borrar categorías sin productos asociados.",
                625,
                357,
                (686, 357),
            ),
        ),
    ),
    Figure(
        "categoria_formulario",
        "Formulario de categoría",
        "### Crear o editar un producto",
        (440, 355, 560, 370),
        (
            point("Nombre: identifica la familia de productos.", 506, 484, (466, 484)),
            point(
                "Descripción: agrega una explicación opcional.", 506, 562, (466, 562)
            ),
            point("Cancelar: cierra sin guardar cambios.", 714, 653, (714, 611)),
            point(
                "Guardar categoría: valida y registra la información.",
                854,
                653,
                (975, 653),
            ),
        ),
    ),
    Figure(
        "producto_formulario",
        "Formulario de producto",
        "### Ajustar existencias",
        (410, 190, 620, 700),
        (
            point(
                "Código de barras: opcional y único; conserva ceros iniciales.",
                480,
                311,
                (440, 311),
            ),
            point(
                "Nombre: identifica el producto en catálogo y tickets.",
                480,
                361,
                (440, 361),
            ),
            point("Categoría: selecciona una familia existente.", 480, 416, (440, 416)),
            point("Descripción: información adicional opcional.", 480, 469, (440, 469)),
            point(
                "Costo unitario: indica cuánto cuesta adquirir una unidad.",
                480,
                519,
                (440, 519),
            ),
            point(
                "Precio de venta: importe final cobrado al cliente.",
                480,
                569,
                (440, 569),
            ),
            point(
                "Existencia inicial: cantidad al crear el producto; después utiliza Ajustes.",
                480,
                619,
                (440, 619),
            ),
            point(
                "Stock mínimo: umbral de alerta para reposición.", 480, 669, (440, 669)
            ),
            point("Cancelar: descarta el formulario.", 742, 822, (742, 779)),
            point(
                "Guardar producto: valida y registra el artículo.",
                881,
                822,
                (1001, 822),
            ),
        ),
    ),
    Figure(
        "eliminar_producto",
        "Confirmación de eliminación",
        "### Ajustar existencias",
        (420, 375, 600, 330),
        (
            point(
                "Registro: revisa qué producto vas a eliminar.", 485, 487, (447, 487)
            ),
            point(
                "Restricciones: los registros con historial no pueden eliminarse.",
                485,
                539,
                (447, 539),
            ),
            point("Cancelar: conserva el producto.", 795, 636, (795, 592)),
            point(
                "Eliminar: solicita la baja; el sistema vuelve a validar las restricciones.",
                906,
                636,
                (995, 636),
            ),
        ),
    ),
    Figure(
        "ajustes",
        "Selección de producto para ajustar",
        "## 8. Importar productos desde Excel",
        (240, 145, 1185, 910),
        (
            point(
                "Buscar: escribe nombre o código; puedes escanear y pulsar Enter.",
                275,
                300,
                (250, 300),
            ),
            point(
                "Existencia: consulta el stock antes de elegir el movimiento.",
                598,
                423,
                (598, 375),
            ),
            point(
                "Ajustar: abre el formulario del producto de esa fila.",
                710,
                423,
                (815, 423),
            ),
        ),
    ),
    Figure(
        "ajuste_formulario",
        "Formulario de ajuste de existencias",
        "## 8. Importar productos desde Excel",
        (410, 265, 620, 550),
        (
            point(
                "Producto y existencia: confirma sobre qué artículo aplicarás el movimiento.",
                475,
                418,
                (437, 418),
            ),
            point(
                "Cantidad del movimiento: positiva para entrada y negativa para salida; no es la existencia final.",
                475,
                468,
                (437, 468),
            ),
            point(
                "Motivo: explica la recepción, merma o corrección.",
                475,
                552,
                (437, 552),
            ),
            point("Cancelar: cierra sin registrar el ajuste.", 771, 747, (771, 704)),
            point(
                "Aplicar ajuste: guarda el movimiento y actualiza el stock.",
                898,
                747,
                (1002, 747),
            ),
        ),
    ),
    Figure(
        "importar",
        "Asistente de importación antes de elegir un archivo",
        "## 9. Cierre y consulta de caja",
        (240, 185, 960, 710),
        (
            point(
                "Instrucciones: explican el orden de descarga, llenado, revisión y confirmación.",
                550,
                310,
                (550, 273),
            ),
            point(
                "Descargar plantilla: guarda el Excel con los encabezados correctos.",
                387,
                458,
                (387, 419),
            ),
            point(
                "Seleccionar Excel: abre el selector de archivos .xlsx.",
                577,
                458,
                (577, 419),
            ),
            point(
                "Archivo seleccionado: aquí aparecerá el nombre del documento elegido.",
                440,
                499,
                (440, 537),
            ),
            point("Cerrar: abandona el asistente sin importar.", 885, 827, (885, 785)),
            point(
                "Confirmar importación: permanece deshabilitado hasta validar un archivo.",
                1040,
                827,
                (1040, 785),
            ),
        ),
    ),
    Figure(
        "importar_validado",
        "Vista previa de una importación válida",
        "## 9. Cierre y consulta de caja",
        (240, 185, 960, 710),
        (
            point(
                "Nombre de archivo: comprueba que hayas elegido el documento correcto.",
                430,
                499,
                (430, 537),
            ),
            point(
                "Resultado de validación: indica cuántos productos están listos para importar.",
                536,
                536,
                (727, 536),
            ),
            point(
                "Vista previa: revisa producto, categoría, precio y existencia antes de guardar.",
                484,
                638,
                (484, 681),
            ),
            point(
                "Confirmar importación: guarda el lote validado; si falla una fila, no se guarda ninguna.",
                1040,
                827,
                (1040, 785),
            ),
            point(
                "Cerrar: permite salir sin confirmar la carga.", 885, 827, (885, 785)
            ),
        ),
    ),
    Figure(
        "corte",
        "Estado y conciliación de caja",
        "## 10. Usuarios y permisos de acceso",
        (240, 145, 1185, 570),
        (
            point(
                "Cerrar caja: abre el formulario de conteo físico.",
                1344,
                200,
                (1344, 245),
            ),
            point("Estado: indica si tu turno está abierto.", 390, 326, (485, 326)),
            point(
                "Fondo inicial: efectivo registrado al abrir el turno.",
                685,
                326,
                (785, 326),
            ),
            point(
                "Efectivo esperado: fondo más ventas completadas en efectivo del turno.",
                980,
                326,
                (1080, 326),
            ),
            point(
                "Tickets del turno: número de comprobantes, incluidos los cancelados.",
                1240,
                326,
                (1350, 326),
            ),
            point(
                "Historial: muestra apertura, estado, efectivo esperado, contado y diferencia.",
                540,
                565,
                (540, 612),
            ),
        ),
    ),
    Figure(
        "cerrar_caja",
        "Formulario de cierre de turno",
        "## 10. Usuarios y permisos de acceso",
        (430, 350, 580, 380),
        (
            point(
                "Efectivo contado: reemplaza el valor propuesto por el conteo físico real.",
                495,
                478,
                (455, 478),
            ),
            point(
                "Notas del cierre: explica diferencias o incidencias si corresponde.",
                495,
                542,
                (455, 542),
            ),
            point(
                "Cancelar: conserva abierto el turno sin confirmar el cierre.",
                735,
                659,
                (735, 615),
            ),
            point(
                "Confirmar cierre: guarda contado, esperado y diferencia y termina el turno.",
                869,
                659,
                (980, 659),
            ),
        ),
    ),
    Figure(
        "usuarios",
        "Administración de usuarios",
        "### Editar o desactivar",
        (240, 145, 1185, 560),
        (
            point(
                "Nuevo usuario: abre el alta de un empleado.", 1333, 200, (1333, 245)
            ),
            point("Buscar: localiza al empleado por sus datos.", 275, 297, (250, 297)),
            point(
                "Rol: identifica si la cuenta es Administrador, Supervisor o Cajero.",
                585,
                415,
                (585, 365),
            ),
            point(
                "Editar: cambia datos, rol, estado o contraseña de otra cuenta.",
                679,
                415,
                (679, 365),
            ),
            point(
                "Desactivar: retira el acceso y conserva el historial.",
                720,
                415,
                (789, 415),
            ),
        ),
    ),
    Figure(
        "usuario_formulario",
        "Formulario de empleado",
        "### Editar o desactivar",
        (410, 185, 620, 710),
        (
            point("Nombre y apellidos: identifican al empleado.", 475, 311, (437, 311)),
            point("Correo: será su identificador de acceso.", 475, 475, (437, 475)),
            point("Teléfono: contacto opcional.", 475, 557, (437, 557)),
            point("Rol: define los permisos de la cuenta.", 475, 639, (437, 639)),
            point(
                "Acceso activo: habilita o impide iniciar sesión.", 479, 697, (437, 697)
            ),
            point(
                "Contraseña inicial: mínimo 12 caracteres; al editar es opcional si no se cambia.",
                475,
                755,
                (437, 755),
            ),
            point(
                "Mostrar contraseña: revisa el dato capturado mediante el icono del ojo.",
                755,
                755,
                (820, 755),
            ),
            point(
                "Cancelar: descarta los cambios del formulario.", 807, 827, (807, 868)
            ),
            point("Guardar: valida y registra al empleado.", 915, 827, (997, 827)),
        ),
    ),
    Figure(
        "desactivar_usuario",
        "Confirmación de desactivación",
        "## 11. Reportes",
        (430, 380, 580, 320),
        (
            point(
                "Empleado: confirma a quién retirarás el acceso.", 495, 495, (455, 495)
            ),
            point(
                "Conservación del historial: las ventas anteriores permanecen registradas.",
                495,
                543,
                (455, 543),
            ),
            point("Cancelar: conserva el acceso actual.", 770, 633, (770, 592)),
            point(
                "Desactivar: confirma la baja de acceso del empleado.",
                888,
                633,
                (979, 633),
            ),
        ),
    ),
    Figure(
        "reporte_ventas",
        "Panel de reportes",
        "## 12. Configuración personal e impresoras",
        (240, 145, 1185, 910),
        (
            point(
                "Periodo: selecciona los últimos 7 o 30 días.", 1153, 200, (1153, 249)
            ),
            point(
                "Exportar CSV: guarda todas las filas del reporte seleccionado.",
                1338,
                200,
                (1338, 249),
            ),
            point(
                "Pestañas: Ventas, Clientes, Usuarios y Predicciones cambian el análisis; Usuarios requiere Administrador.",
                454,
                270,
                (454, 315),
            ),
            point(
                "Indicadores: resumen importes, operaciones, promedio y clientes.",
                827,
                380,
                (827, 336),
            ),
            point(
                "Tendencia: gráfica de los últimos siete días.", 830, 600, (830, 551)
            ),
            point(
                "Tabla: muestra el detalle del reporte; desplázate hacia abajo para sus controles finales.",
                481,
                850,
                (780, 850),
            ),
        ),
    ),
    Figure(
        "reporte_tabla",
        "Paginación del reporte y acceso a tickets",
        "## 12. Configuración personal e impresoras",
        (240, 620, 1185, 435),
        (
            point(
                "Paginación: recorre las páginas del reporte sin cambiar el periodo.",
                465,
                900,
                (465, 850),
            ),
            point(
                "Historial y tickets: permite abrir los comprobantes desde el reporte de ventas.",
                370,
                950,
                (590, 950),
            ),
        ),
    ),
    Figure(
        "reporte_predicciones",
        "Reposición sugerida",
        "## 12. Configuración personal e impresoras",
        (240, 745, 1185, 310),
        (
            point(
                "Unidades vendidas y promedio diario: resumen la demanda del periodo.",
                524,
                850,
                (524, 800),
            ),
            point(
                "Existencia: cantidad disponible de cada producto.",
                740,
                850,
                (740, 800),
            ),
            point(
                "Reposición: cantidad sugerida para cubrir el objetivo de stock.",
                837,
                850,
                (907, 850),
            ),
            point(
                "Ejemplo: el café sugiere reponer 2 unidades porque tiene 8 y su mínimo es 10.",
                817,
                981,
                (950, 981),
            ),
        ),
    ),
    Figure(
        "aspectos",
        "Apariencia y estado de conexión",
        "### Contraseña y correo",
        (240, 145, 1185, 450),
        (
            point(
                "Pestañas de configuración: Periféricos, Aspectos, Contraseña y Correo.",
                490,
                270,
                (490, 312),
            ),
            point(
                "Tema claro: aplica y conserva una apariencia clara en este equipo.",
                343,
                433,
                (343, 477),
            ),
            point(
                "Tema oscuro: aplica y conserva una apariencia oscura en este equipo.",
                496,
                433,
                (496, 477),
            ),
            point(
                "Conexión y sincronización: muestra el modo y los eventos pendientes.",
                1200,
                386,
                (1200, 337),
            ),
            point(
                "Sincronizar ahora: se habilita en una instalación con sincronización configurada; en demo está deshabilitado.",
                1150,
                470,
                (1370, 470),
            ),
        ),
    ),
    Figure(
        "contrasena",
        "Cambio de contraseña propia",
        "### Impresora",
        (235, 300, 800, 455),
        (
            point(
                "Contraseña actual: confirma tu identidad antes del cambio.",
                275,
                402,
                (250, 402),
            ),
            point(
                "Nueva contraseña: escribe la nueva clave de acceso.",
                275,
                470,
                (250, 470),
            ),
            point(
                "Confirmar: repite exactamente la nueva contraseña.",
                275,
                538,
                (250, 538),
            ),
            point(
                "Mostrar: los iconos del ojo revelan temporalmente los campos que lo permiten.",
                555,
                402,
                (621, 402),
            ),
            point(
                "Cambiar contraseña: guarda el cambio y renueva la sesión actual.",
                362,
                635,
                (510, 635),
            ),
        ),
    ),
    Figure(
        "correo",
        "Cambio del correo de acceso",
        "### Impresora",
        (235, 300, 800, 390),
        (
            point("Contraseña actual: confirma tu identidad.", 275, 402, (250, 402)),
            point(
                "Nuevo correo de acceso: sustituye el correo actual por el que utilizarás al entrar.",
                275,
                470,
                (250, 470),
            ),
            point(
                "Guardar correo: actualiza el acceso y renueva la sesión.",
                346,
                567,
                (495, 567),
            ),
        ),
    ),
    Figure(
        "perifericos",
        "Impresora USB",
        "### Conexión y sincronización",
        (240, 300, 1185, 535),
        (
            point(
                "Conexión: elige USB, Serial / COM o Red / Ethernet.",
                275,
                402,
                (250, 402),
            ),
            point(
                "Fabricante: escribe el identificador USB proporcionado para tu modelo.",
                275,
                470,
                (250, 470),
            ),
            point(
                "Producto: escribe el identificador USB del dispositivo.",
                275,
                538,
                (250, 538),
            ),
            point(
                "Cortar papel: habilita el corte si el equipo lo admite.",
                279,
                603,
                (250, 603),
            ),
            point(
                "Guardar configuración: conserva los parámetros de este equipo.",
                378,
                658,
                (378, 702),
            ),
            point(
                "Imprimir prueba: envía un comprobante físico; verifica papel y conexión.",
                576,
                658,
                (576, 702),
            ),
            point(
                "Sincronización: consulta el modo y la disponibilidad de envío de pendientes.",
                1200,
                386,
                (1200, 337),
            ),
        ),
    ),
    Figure(
        "perifericos_serial",
        "Impresora Serial / COM",
        "### Conexión y sincronización",
        (240, 300, 800, 535),
        (
            point(
                "Conexión Serial / COM: muestra los parámetros de un dispositivo serial.",
                275,
                402,
                (250, 402),
            ),
            point(
                "Puerto o dispositivo: escribe el puerto asignado, por ejemplo COM3.",
                275,
                470,
                (250, 470),
            ),
            point(
                "Baudios: debe coincidir con la velocidad configurada en la impresora.",
                275,
                538,
                (250, 538),
            ),
            point(
                "Guardar e imprimir prueba: conserva los parámetros y comprueba la conexión.",
                475,
                658,
                (675, 658),
            ),
        ),
    ),
    Figure(
        "perifericos_red",
        "Impresora de red",
        "### Conexión y sincronización",
        (240, 300, 800, 535),
        (
            point(
                "Conexión Red / Ethernet: muestra los datos de una impresora de red.",
                275,
                402,
                (250, 402),
            ),
            point(
                "Dirección: utiliza la dirección real de tu impresora; la imagen contiene una dirección de ejemplo.",
                275,
                470,
                (250, 470),
            ),
            point(
                "Puerto de red: debe coincidir con el puerto de impresión configurado.",
                275,
                538,
                (250, 538),
            ),
            point(
                "Guardar e imprimir prueba: conserva los datos y envía una prueba física.",
                475,
                658,
                (675, 658),
            ),
        ),
    ),
)
