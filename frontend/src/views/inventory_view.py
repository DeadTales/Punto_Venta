from decimal import Decimal
from pathlib import Path

import flet as ft
from pydantic import ValidationError

from shared.catalog import profit_margin, validation_message
from shared.inventory_excel import MAX_BYTES, template_bytes

from ..components.ui import (
    GREEN,
    MUTED,
    card,
    heading,
    note,
    pill,
    primary,
    secondary,
    stat,
    table,
    text,
)
from ..models.state import money

PRODUCTS_PER_PAGE = 20


def _stock_indicator(product):
    current_stock = Decimal(str(product["stock_actual"]))
    minimum_stock = Decimal(str(product["stock_minimo"]))

    if current_stock == 0:
        return pill("Agotado", "red")

    if current_stock <= minimum_stock:
        return pill("Reponer", "amber")

    return pill("Disponible", "green")


def _product_actions(app, product):
    actions = [
        ft.IconButton(
            ft.Icons.ADD_SHOPPING_CART_OUTLINED,
            tooltip="Añadir al carrito",
            icon_color=GREEN,
            on_click=lambda event: app.add_to_cart(product),
        )
    ]

    if app.products.can_manage:
        actions.extend(
            [
                ft.IconButton(
                    ft.Icons.EDIT_OUTLINED,
                    tooltip="Editar producto",
                    on_click=lambda event: product_dialog(app, product),
                ),
                ft.IconButton(
                    ft.Icons.TUNE,
                    tooltip="Ajustar existencias",
                    on_click=lambda event: open_adjustment(app, product),
                ),
                ft.IconButton(
                    ft.Icons.DELETE_OUTLINE,
                    tooltip="Eliminar producto",
                    on_click=lambda event: delete_dialog(app, "products", product),
                ),
            ]
        )

    return ft.Row(actions, spacing=0)


def _product_row(app, product):
    category_name = next(
        (
            category["nombre"]
            for category in app.state.categories
            if category["id_categoria"] == product["id_categoria"]
        ),
        "—",
    )
    margin = profit_margin(product["precio_compra"], product["precio_venta"])

    product_identity = ft.Column(
        [
            text(product["nombre"], 13, True),
            text(product.get("codigo_barras") or "Sin código", 11, color=MUTED),
        ],
        spacing=3,
    )

    return [
        product_identity,
        category_name,
        money(product["precio_compra"]),
        money(product["precio_venta"]),
        "—" if margin is None else f"{margin}%",
        text(product["stock_actual"], 13, True),
        _stock_indicator(product),
        _product_actions(app, product),
    ]


def inventory_view(app):
    state = app.state
    filters = app.filters.setdefault(
        "inventory", {"q": "", "category": "all", "low": False, "page": 0}
    )

    if filters["category"] not in {str(c["id_categoria"]) for c in state.categories}:
        filters["category"] = "all"

    search = ft.TextField(
        hint_text="Buscar nombre o código de barras",
        prefix_icon=ft.Icons.SEARCH,
        dense=True,
        expand=True,
        border_radius=8,
        value=filters["q"],
    )
    category = ft.Dropdown(
        value=filters["category"],
        width=200,
        dense=True,
        label="Categoría",
        options=[ft.DropdownOption("all", "Todas las categorías")]
        + [
            ft.DropdownOption(str(c["id_categoria"]), c["nombre"])
            for c in state.categories
        ],
    )
    low = ft.Switch(label="Stock bajo", value=filters["low"])
    host = ft.Container()
    pagination = ft.Row()

    def refresh(e=None):
        if e:
            filters["page"] = 0

        filters.update(
            q=search.value or "", category=category.value, low=bool(low.value)
        )
        query = (search.value or "").casefold()
        matches = []

        for p in state.products:
            if (
                query
                not in (p["nombre"] + " " + (p.get("codigo_barras") or "")).casefold()
            ):
                continue

            if category.value != "all" and str(p["id_categoria"]) != category.value:
                continue

            is_low = Decimal(str(p["stock_actual"])) <= Decimal(str(p["stock_minimo"]))

            if low.value and not is_low:
                continue

            matches.append(p)

        pages = max(1, (len(matches) + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE)
        filters["page"] = min(filters["page"], pages - 1)
        page_start = filters["page"] * PRODUCTS_PER_PAGE
        page_end = page_start + PRODUCTS_PER_PAGE
        visible_products = matches[page_start:page_end]
        rows = [_product_row(app, product) for product in visible_products]
        host.content = table(
            [
                "PRODUCTO / CÓDIGO",
                "CATEGORÍA",
                "COSTO",
                "PRECIO",
                "MARGEN",
                "EXISTENCIA",
                "ESTADO",
                "",
            ],
            rows,
        )
        pagination.controls = [
            secondary("Anterior", lambda e: move(-1), disabled=filters["page"] == 0),
            text(
                f"Página {filters['page'] + 1} de {pages} · {len(matches)} productos",
                12,
            ),
            secondary(
                "Siguiente", lambda e: move(1), disabled=filters["page"] >= pages - 1
            ),
        ]

        if e:
            app.page.update()

    def move(step):
        filters["page"] += step
        refresh()
        app.page.update()

    search.on_change = refresh
    category.on_select = refresh
    low.on_change = refresh
    refresh()

    return ft.Column(
        [
            heading(
                "Inventario",
                "Tu catálogo, existencias y alertas en un solo lugar.",
                [
                    secondary(
                        "Categorías",
                        lambda e: app.navigate("inventario/categorias"),
                        ft.Icons.CATEGORY_OUTLINED,
                    ),
                    secondary(
                        "Ajustes",
                        lambda e: app.navigate("inventario/ajustes"),
                        ft.Icons.TUNE,
                    ),
                    *(
                        [
                            secondary(
                                "Importar Excel",
                                lambda e: import_dialog(app),
                                ft.Icons.UPLOAD_FILE,
                            ),
                            primary(
                                "Nuevo producto",
                                lambda e: product_dialog(app),
                                ft.Icons.ADD,
                            ),
                        ]
                        if app.products.can_manage
                        else []
                    ),
                ],
            ),
            ft.ResponsiveRow(
                [
                    stat(
                        "Productos",
                        len(state.products),
                        "Referencias en el catálogo",
                        ft.Icons.INVENTORY_2_OUTLINED,
                    ),
                    stat(
                        "Por reponer",
                        len(state.low_stock),
                        "En el mínimo o por debajo",
                        ft.Icons.WARNING_AMBER_ROUNDED,
                    ),
                    stat(
                        "Categorías",
                        len(state.categories),
                        "Familias de productos",
                        ft.Icons.CATEGORY_OUTLINED,
                    ),
                    stat(
                        "Valor al costo",
                        money(
                            sum(
                                (
                                    Decimal(str(p["precio_compra"]))
                                    * Decimal(str(p["stock_actual"]))
                                    for p in state.products
                                ),
                                Decimal(0),
                            )
                        ),
                        "Estimación de inventario actual",
                        ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED,
                    ),
                ],
                spacing=16,
                run_spacing=16,
            ),
            card(
                ft.Column(
                    [
                        ft.Row([search, category, low], spacing=12),
                        host,
                        pagination,
                        ft.Row(
                            [
                                text(
                                    "Precios en MXN · cantidades con hasta 3 decimales",
                                    11,
                                    color=MUTED,
                                    expand=True,
                                ),
                                *(
                                    [
                                        secondary(
                                            "Nueva categoría",
                                            lambda e: category_dialog(app),
                                            ft.Icons.ADD,
                                        )
                                    ]
                                    if app.products.can_manage
                                    else []
                                ),
                            ]
                        ),
                    ],
                    spacing=16,
                )
            ),
            note(
                "Importa productos nuevos con la plantilla. Los códigos existentes se rechazan para proteger el stock y el historial."
            ),
        ],
        spacing=22,
    )


def category_dialog(app, category=None):
    name = ft.TextField(
        label="Nombre de la categoría",
        max_length=100,
        autofocus=True,
        value=category["nombre"] if category else "",
    )
    description = ft.TextField(
        label="Descripción (opcional)",
        value=category.get("descripcion") if category else "",
    )
    error = text("", 12, color=ft.Colors.ERROR)
    submit = primary("Guardar categoría", None)

    async def save(e):
        if submit.disabled:
            return

        value = (name.value or "").strip()

        if not value:
            error.value = "Escribe el nombre de la categoría."
            app.page.update()

            return

        try:
            submit.disabled = True
            app.page.update()
            await app.products.save_category(
                {"nombre": value, "descripcion": description.value or None},
                category["id_categoria"] if category else None,
            )
            await app.products.refresh_after_write()
            app.page.pop_dialog()
            app.render()
            app.notify(
                "Categoría guardada" + (" en la demostración" if app.state.demo else "")
            )
        except Exception as exc:
            submit.disabled = False
            error.value = (
                validation_message(exc.errors())
                if isinstance(exc, ValidationError)
                else str(exc)
            )
            app.page.update()

    submit.on_click = save
    app.dialog(
        "Editar categoría" if category else "Nueva categoría",
        ft.Column([name, description, error], tight=True, width=430),
        [secondary("Cancelar", lambda e: app.page.pop_dialog()), submit],
    )


def product_dialog(app, product=None):
    fields = [
        ft.TextField(label=label, dense=True)
        for label in [
            "Código de barras (opcional)",
            "Nombre",
            "Descripción (opcional)",
            "Costo unitario",
            "Precio de venta",
            "Existencia inicial",
            "Stock mínimo",
        ]
    ]
    keys = [
        "codigo_barras",
        "nombre",
        "descripcion",
        "precio_compra",
        "precio_venta",
        "stock_actual",
        "stock_minimo",
    ]

    for field, key in zip(fields, keys):
        if product:
            field.value = str(product[key]) if product.get(key) is not None else ""
        else:
            field.value = "0" if key in keys[3:] else ""

    fields[5].visible = product is None
    category = ft.Dropdown(
        label="Categoría",
        options=[
            ft.DropdownOption(str(c["id_categoria"]), c["nombre"])
            for c in app.state.categories
        ],
        value=str(product["id_categoria"])
        if product
        else str(app.state.categories[0]["id_categoria"])
        if app.state.categories
        else None,
    )
    error = text("", 12, color=ft.Colors.ERROR)
    submit = primary("Guardar producto", None)

    async def save(e):
        if submit.disabled:
            return

        try:
            values = {key: field.value or None for key, field in zip(keys, fields)}
            values["id_categoria"] = int(category.value) if category.value else 0

            if product:
                values.pop("stock_actual")

            submit.disabled = True
            app.page.update()
            await app.products.save_product(
                values, product["id_producto"] if product else None
            )
            await app.products.refresh_after_write()
            app.page.pop_dialog()
            app.render()
            app.notify("Producto guardado")
        except Exception as exc:
            submit.disabled = False
            error.value = (
                validation_message(exc.errors())
                if isinstance(exc, ValidationError)
                else str(exc)
            )

        app.page.update()

    submit.on_click = save
    app.dialog(
        "Editar producto" if product else "Nuevo producto",
        ft.Column(
            [fields[0], fields[1], category, *fields[2:], error],
            tight=True,
            scroll=ft.ScrollMode.AUTO,
            width=480,
            height=490,
        ),
        [secondary("Cancelar", lambda e: app.page.pop_dialog()), submit],
    )


def open_adjustment(app, product):
    from .inventory_adjust_view import adjustment_dialog

    adjustment_dialog(app, product)


def delete_dialog(app, entity, record):
    error = text("", 12, color=ft.Colors.ERROR)
    submit = primary("Eliminar", None)

    async def remove(e):
        if submit.disabled:
            return

        submit.disabled = True
        app.page.update()

        try:
            identifier = record[
                "id_producto" if entity == "products" else "id_categoria"
            ]
            await app.products.delete(entity, identifier)
            await app.products.refresh_after_write()
            app.page.pop_dialog()
            app.render()
            app.notify("Registro eliminado")
        except Exception as exc:
            submit.disabled = False
            error.value = str(exc)
            app.page.update()

    submit.on_click = remove
    app.dialog(
        "Eliminar registro",
        ft.Column(
            [
                text(f"¿Eliminar {record['nombre']}?"),
                note(
                    "Los productos con ventas o ajustes y las categorías con productos conservan su historial y no pueden eliminarse."
                ),
                error,
            ],
            width=470,
            tight=True,
        ),
        [secondary("Cancelar", lambda e: app.page.pop_dialog()), submit],
    )


def import_dialog(app):
    selected = {"data": None}
    filename = text("Ningún archivo seleccionado", 12, color=MUTED)
    result_host = ft.Container()
    confirm = primary("Confirmar importación", None, ft.Icons.CHECK, disabled=True)

    async def download(e):
        try:
            await app.picker.save_file(
                file_name="plantilla_inventario.xlsx",
                src_bytes=template_bytes(),
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["xlsx"],
            )
        except Exception as exc:
            app.notify(f"No se pudo guardar la plantilla: {exc}", error=True)

    async def choose(e):
        confirm.disabled = True
        selected["data"] = None

        try:
            files = await app.picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["xlsx"],
            )

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
                result_host.content = ft.Column(
                    [
                        pill(f"{result['count']} productos listos para importar"),
                        table(
                            ["PRODUCTO", "CATEGORÍA", "PRECIO", "EXISTENCIA"],
                            [
                                [
                                    r["nombre"],
                                    r["categoria"],
                                    money(r["precio_venta"]),
                                    r["stock_actual"],
                                ]
                                for r in result["rows"][:10]
                            ],
                        ),
                        text(
                            "Vista previa de las primeras 10 filas. Al confirmar se valida y guarda el archivo completo.",
                            11,
                            color=MUTED,
                        ),
                    ],
                    spacing=10,
                )
            else:
                result_host.content = ft.Column(
                    [
                        pill(
                            f"{len(result['errors'])} errores · no se guardará ninguna fila",
                            "red",
                        ),
                        table(
                            ["FILA", "COLUMNA", "CÓMO CORREGIR"],
                            [
                                [r["fila"], r["columna"], r["mensaje"]]
                                for r in result["errors"][:30]
                            ],
                        ),
                        text(
                            "Se muestran hasta 30 errores. Corrige el archivo y vuelve a seleccionarlo.",
                            11,
                            color=MUTED,
                        ),
                    ]
                )
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
            app.notify(
                f"{result['imported']} productos importados"
                + (" · demostración" if app.state.demo else "")
            )
        except Exception as exc:
            result_host.content = text(str(exc), 13, color=ft.Colors.ERROR)
            confirm.disabled = False
            app.page.update()

    confirm.on_click = save
    app.dialog(
        "Importar inventario desde Excel",
        ft.Column(
            [
                note(
                    "1. Descarga la plantilla  /  2. Llena Inventario  /  3. Revisa y confirma"
                ),
                text("Cómo llenar tu archivo", 16, True),
                text(
                    "Una fila por producto nuevo. No cambies los encabezados. Usa una categoría existente; los códigos son texto para conservar ceros iniciales. Precios: 2 decimales. Stock: 3 decimales. Sin fórmulas.",
                    13,
                    color=MUTED,
                ),
                ft.Row(
                    [
                        secondary("Descargar plantilla", download, ft.Icons.DOWNLOAD),
                        primary("Seleccionar Excel", choose, ft.Icons.UPLOAD_FILE),
                    ],
                    wrap=True,
                ),
                filename,
                result_host,
                text(
                    "Sólo .xlsx · hasta 5 MB / 5,000 productos · Si una fila falla, no se importa ninguna.",
                    11,
                    color=MUTED,
                ),
            ],
            width=850,
            height=500,
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
        ),
        [secondary("Cerrar", lambda e: app.page.pop_dialog()), confirm],
    )
