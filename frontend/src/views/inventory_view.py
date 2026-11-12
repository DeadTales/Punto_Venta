from io import BytesIO
from pathlib import Path
from decimal import Decimal

import flet as ft
from openpyxl import Workbook

from shared.inventory_excel import HEADERS, MAX_BYTES, template_bytes
from ..components.ui import GREEN, MUTED, card, heading, note, pill, primary, secondary, stat, table, text
from ..models.state import money


def workbook_bytes(values):
    wb = Workbook()
    wb.active.title = "Inventario"
    wb.active.append(HEADERS)
    for row in values:
        wb.active.append(row)
    output = BytesIO()
    wb.save(output)
    return output.getvalue()


def inventory_view(app):
    state = app.state
    search = ft.TextField(hint_text="Buscar nombre o código de barras", prefix_icon=ft.Icons.SEARCH,
                          dense=True, expand=True, border_radius=8)
    category = ft.Dropdown(value="all", width=200, dense=True, label="Categoría",
                           options=[ft.DropdownOption("all", "Todas las categorías")] +
                           [ft.DropdownOption(str(c["id_categoria"]), c["nombre"]) for c in state.categories])
    low = ft.Switch(label="Stock bajo", value=False)
    host = ft.Container()

    def refresh(e=None):
        query = (search.value or "").casefold()
        rows = []
        for p in state.products:
            if query not in (p["nombre"] + " " + (p.get("codigo_barras") or "")).casefold():
                continue
            if category.value != "all" and str(p["id_categoria"]) != category.value:
                continue
            is_low = Decimal(str(p["stock_actual"])) <= Decimal(str(p["stock_minimo"]))
            if low.value and not is_low:
                continue
            name = next((c["nombre"] for c in state.categories if c["id_categoria"] == p["id_categoria"]), "—")
            rows.append([ft.Column([text(p["nombre"], 13, True), text(p.get("codigo_barras") or "Sin código", 11, color=MUTED)], spacing=3),
                         name, money(p["precio_compra"]), money(p["precio_venta"]),
                         text(p["stock_actual"], 13, True), pill("Reponer" if is_low else "Disponible", "amber" if is_low else "green"),
                         ft.IconButton(ft.Icons.ADD_SHOPPING_CART_OUTLINED, tooltip="Añadir al carrito", icon_color=GREEN,
                                       on_click=lambda e, product=p: app.add_to_cart(product))])
        host.content = table(["PRODUCTO / CÓDIGO", "CATEGORÍA", "COSTO", "PRECIO", "EXISTENCIA", "ESTADO", ""], rows)
        if e:
            app.page.update()

    search.on_change = refresh
    category.on_select = refresh
    low.on_change = refresh
    refresh()
    return ft.Column([
        heading("Inventario", "Tu catálogo, existencias y alertas en un solo lugar.", [
            secondary("Importar Excel", lambda e: import_dialog(app), ft.Icons.UPLOAD_FILE),
            primary("Nuevo producto", lambda e: product_dialog(app), ft.Icons.ADD),
        ]),
        ft.ResponsiveRow([
            stat("Productos", len(state.products), "Referencias en el catálogo", ft.Icons.INVENTORY_2_OUTLINED),
            stat("Por reponer", len(state.low_stock), "En el mínimo o por debajo", ft.Icons.WARNING_AMBER_ROUNDED),
            stat("Categorías", len(state.categories), "Familias de productos", ft.Icons.CATEGORY_OUTLINED),
            stat("Valor al costo", money(sum((Decimal(str(p["precio_compra"])) * Decimal(str(p["stock_actual"])) for p in state.products), Decimal(0))),
                 "Estimación de inventario actual", ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED),
        ], spacing=16, run_spacing=16),
        card(ft.Column([
            ft.Row([search, category, low], spacing=12),
            host,
            ft.Row([text("Precios en MXN · cantidades con hasta 3 decimales", 11, color=MUTED, expand=True),
                    secondary("Nueva categoría", lambda e: category_dialog(app), ft.Icons.ADD)]),
        ], spacing=16)),
        note("Importa productos nuevos con la plantilla. Los códigos existentes se rechazan para proteger el stock y el historial."),
    ], spacing=22)


def category_dialog(app):
    name = ft.TextField(label="Nombre de la categoría", max_length=100, autofocus=True)
    error = text("", 12, color=ft.Colors.ERROR)

    async def save(e):
        value = (name.value or "").strip()
        if not value:
            error.value = "Escribe el nombre de la categoría."
            app.page.update()
            return
        try:
            if app.state.demo:
                app.state.categories.append({"id_categoria": max([c["id_categoria"] for c in app.state.categories], default=0) + 1, "nombre": value})
            else:
                await app.api.request("POST", "/api/categories", json={"nombre": value})
                await app.reload()
            app.page.pop_dialog()
            app.render()
            app.notify("Categoría creada" + (" en la demostración" if app.state.demo else ""))
        except Exception as exc:
            error.value = str(exc)
            app.page.update()

    app.dialog("Nueva categoría", ft.Column([name, error], tight=True, width=430), [secondary("Cancelar", lambda e: app.page.pop_dialog()), primary("Crear categoría", save)])


def product_dialog(app):
    fields = [ft.TextField(label=label, dense=True) for label in ["Código de barras (opcional)", "Nombre", "Descripción (opcional)", "Costo unitario", "Precio de venta", "Existencia inicial", "Stock mínimo"]]
    category = ft.Dropdown(label="Categoría", options=[ft.DropdownOption(c["nombre"]) for c in app.state.categories],
                           value=app.state.categories[0]["nombre"] if app.state.categories else None)
    error = text("", 12, color=ft.Colors.ERROR)

    async def save(e):
        values = [fields[0].value or None, fields[1].value, category.value, fields[2].value or None,
                  *[f.value for f in fields[3:]]]
        try:
            data = workbook_bytes([values])
            result = await app.preview_inventory(data)
            if not result["valid"]:
                error.value = "\n".join(f"{r['columna']}: {r['mensaje']}" for r in result["errors"][:8])
            else:
                await app.confirm_inventory(data)
                app.page.pop_dialog()
                app.render()
                app.notify("Producto registrado")
        except Exception as exc:
            error.value = str(exc)
        app.page.update()

    app.dialog("Nuevo producto", ft.Column([fields[0], fields[1], category, *fields[2:], error], tight=True, scroll=ft.ScrollMode.AUTO, width=480, height=490),
               [secondary("Cancelar", lambda e: app.page.pop_dialog()), primary("Guardar producto", save)])


def import_dialog(app):
    selected = {"data": None}
    filename = text("Ningún archivo seleccionado", 12, color=MUTED)
    result_host = ft.Container()
    confirm = primary("Confirmar importación", None, ft.Icons.CHECK, disabled=True)

    async def download(e):
        try:
            await app.picker.save_file(file_name="plantilla_inventario.xlsx", src_bytes=template_bytes(),
                                       file_type=ft.FilePickerFileType.CUSTOM, allowed_extensions=["xlsx"])
        except Exception as exc:
            app.notify(f"No se pudo guardar la plantilla: {exc}", error=True)

    async def choose(e):
        confirm.disabled = True
        selected["data"] = None
        try:
            files = await app.picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.CUSTOM,
                                                allowed_extensions=["xlsx"])
            if not files:
                app.page.update()
                return
            path = Path(files[0].path)
            if path.stat().st_size > MAX_BYTES:
                raise ValueError("El archivo supera 5 MB")
            data = path.read_bytes()
            result = await app.preview_inventory(data)
            filename.value = files[0].name
            if result["valid"]:
                selected["data"] = data
                confirm.disabled = False
                result_host.content = ft.Column([
                    pill(f"{result['count']} productos listos para importar"),
                    table(["PRODUCTO", "CATEGORÍA", "PRECIO", "EXISTENCIA"],
                          [[r["nombre"], r["categoria"], money(r["precio_venta"]), r["stock_actual"]] for r in result["rows"][:10]]),
                    text("Vista previa de las primeras 10 filas. Al confirmar se valida y guarda el archivo completo.", 11, color=MUTED),
                ], spacing=10)
            else:
                result_host.content = ft.Column([
                    pill(f"{len(result['errors'])} errores · no se guardará ninguna fila", "red"),
                    table(["FILA", "COLUMNA", "CÓMO CORREGIR"],
                          [[r["fila"], r["columna"], r["mensaje"]] for r in result["errors"][:30]]),
                    text("Se muestran hasta 30 errores. Corrige el archivo y vuelve a seleccionarlo.", 11, color=MUTED),
                ])
        except Exception as exc:
            result_host.content = text(str(exc), 13, color=ft.Colors.ERROR)
        app.page.update()

    async def save(e):
        if selected["data"] is None or confirm.disabled:
            return
        confirm.disabled = True
        app.page.update()
        try:
            result = await app.confirm_inventory(selected["data"])
            app.page.pop_dialog()
            app.render()
            app.notify(f"{result['imported']} productos importados" + (" · demostración" if app.state.demo else ""))
        except Exception as exc:
            result_host.content = text(str(exc), 13, color=ft.Colors.ERROR)
            confirm.disabled = False
            app.page.update()

    confirm.on_click = save
    app.dialog("Importar inventario desde Excel", ft.Column([
        note("1. Descarga la plantilla  /  2. Llena Inventario  /  3. Revisa y confirma"),
        text("Cómo llenar tu archivo", 16, True),
        text("Una fila por producto nuevo. No cambies los encabezados. Usa una categoría existente; los códigos son texto para conservar ceros iniciales. Precios: 2 decimales. Stock: 3 decimales. Sin fórmulas.", 13, color=MUTED),
        ft.Row([secondary("Descargar plantilla", download, ft.Icons.DOWNLOAD), primary("Seleccionar Excel", choose, ft.Icons.UPLOAD_FILE)], wrap=True),
        filename, result_host,
        text("Sólo .xlsx · hasta 5 MB / 5,000 productos · Si una fila falla, no se importa ninguna.", 11, color=MUTED),
    ], width=850, height=500, spacing=16, scroll=ft.ScrollMode.AUTO),
        [secondary("Cerrar", lambda e: app.page.pop_dialog()), confirm])
