from uuid import uuid4

import flet as ft
from pydantic import ValidationError

from shared.catalog import StockAdjustmentInput, validation_message

from ..components.ui import card, heading, note, primary, secondary, table, text
from ..services.api_client import ApiError


def inventory_adjust_view(app):
    search = ft.TextField(
        label="Nombre o código de barras", prefix_icon=ft.Icons.SEARCH
    )
    host = ft.Container()

    def refresh(e=None):
        query = (search.value or "").casefold()
        matches = [
            p
            for p in app.state.products
            if query in (p["nombre"] + " " + (p.get("codigo_barras") or "")).casefold()
        ]
        host.content = table(
            ["PRODUCTO", "CÓDIGO", "EXISTENCIA", ""],
            [
                [
                    p["nombre"],
                    p.get("codigo_barras") or "—",
                    p["stock_actual"],
                    secondary(
                        "Ajustar",
                        lambda e, product=p: adjustment_dialog(app, product),
                        disabled=not app.products.can_manage,
                    ),
                ]
                for p in matches[:30]
            ],
        )

        if e:
            app.page.update()

    async def scan(e):
        try:
            product = await app.products.barcode(search.value or "")
            adjustment_dialog(app, product)
        except Exception as exc:
            app.notify(str(exc), error=True)

    search.on_change, search.on_submit = refresh, scan
    refresh()

    return ft.Column(
        [
            heading(
                "Ajustes de inventario",
                "Registra entradas, mermas y correcciones de existencias.",
            ),
            card(ft.Column([search, host], spacing=18)),
            note(
                "Escanea y pulsa Enter para elegir un producto. Se muestran las primeras 30 coincidencias; afina la búsqueda por nombre o código."
            ),
        ],
        spacing=22,
    )


def adjustment_dialog(app, product):
    quantity = ft.TextField(
        label="Cantidad del movimiento",
        helper="Positiva para entrada; negativa para salida. Hasta 3 decimales.",
    )
    reason = ft.TextField(label="Motivo", max_length=250)
    error = text("", 12, color=ft.Colors.ERROR)
    submit = primary("Aplicar ajuste", None)
    cancel = secondary("Cancelar", lambda e: app.page.pop_dialog())
    pending = {"body": None}

    async def save(e):
        if submit.disabled:
            return

        try:
            if pending["body"] is None:
                body = StockAdjustmentInput.model_validate(
                    {
                        "operation_id": str(uuid4()),
                        "cantidad": quantity.value,
                        "motivo": reason.value,
                    }
                )
                pending["body"] = body.model_dump(mode="json")

            submit.disabled = True
            quantity.disabled = reason.disabled = cancel.disabled = True
            app.page.update()
            result = await app.products.adjust_stock(
                product["id_producto"], pending["body"]
            )
            await app.products.refresh_after_write()
            app.page.pop_dialog()
            app.render()
            app.notify(f"Ajuste registrado · Existencia: {result['stock_nuevo']}")
        except Exception as exc:
            submit.disabled = False
            uncertain = isinstance(exc, ApiError) and exc.status_code not in {
                401,
                403,
                404,
                409,
                422,
            }

            if uncertain:
                error.value = f"{exc}\nReintenta Aplicar ajuste para confirmar la misma operación."
            else:
                pending["body"] = None
                quantity.disabled = reason.disabled = cancel.disabled = False
                error.value = (
                    validation_message(exc.errors())
                    if isinstance(exc, ValidationError)
                    else str(exc)
                )

            app.page.update()

    submit.on_click = save
    app.dialog(
        "Ajustar existencias",
        ft.Column(
            [
                text(product["nombre"], 18, True),
                text(f"Existencia consultada: {product['stock_actual']}"),
                quantity,
                reason,
                note(
                    "El ajuste se aplica al stock vigente. El motivo y el empleado quedan registrados. La existencia nunca puede ser negativa."
                ),
                error,
            ],
            width=490,
            tight=True,
            spacing=16,
        ),
        [cancel, submit],
    )
