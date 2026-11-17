from datetime import date
from uuid import uuid4

import flet as ft

from ..components.ui import (
    MUTED,
    card,
    heading,
    note,
    pill,
    primary,
    secondary,
    table,
    text,
)
from ..models.state import money
from ..services.api_client import ApiError


def sales_view(app):
    search = ft.TextField(
        label="Ticket o cliente",
        prefix_icon=ft.Icons.SEARCH,
        col={"xs": 12, "md": 6, "lg": 5},
    )
    start = ft.TextField(label="Desde (AAAA-MM-DD)", col={"xs": 6, "md": 3, "lg": 2})
    end = ft.TextField(label="Hasta (AAAA-MM-DD)", col={"xs": 6, "md": 3, "lg": 2})
    host = ft.Container()
    footer = ft.Row()
    position = {"page": 0}

    async def show(identifier):
        await sale_dialog(app, identifier)

    def show_handler(identifier):
        async def handler(event):
            await show(identifier)

        return handler

    def refresh(event=None):
        if event is not None:
            position["page"] = 0

        try:
            start_date = date.fromisoformat(start.value) if start.value else None
            end_date = date.fromisoformat(end.value) if end.value else None

            if start_date and end_date and start_date > end_date:
                raise ValueError
        except ValueError:
            host.content = text(
                "Revisa las fechas: usa AAAA-MM-DD y un periodo válido.",
                color=ft.Colors.ERROR,
            )
            app.page.update()

            return

        matches = []
        query = (search.value or "").casefold()

        for sale in sorted(
            app.state.sales, key=lambda sale: sale["fecha_hora"], reverse=True
        ):
            day = date.fromisoformat(sale["fecha_hora"][:10])
            client = next(
                (
                    client["nombre"]
                    for client in app.state.clients
                    if client["id_cliente"] == sale.get("id_cliente")
                ),
                "Público general",
            )

            if query not in f"{sale['id_venta']} {client}".casefold():
                continue

            if start_date and day < start_date or end_date and day > end_date:
                continue

            matches.append((sale, client))

        pages = max(1, (len(matches) + 19) // 20)
        position["page"] = min(position["page"], pages - 1)
        page = matches[position["page"] * 20 : (position["page"] + 1) * 20]
        host.content = table(
            ["TICKET", "FECHA", "CLIENTE", "TOTAL", "ESTADO", ""],
            [
                [
                    f"#{sale['id_venta']}",
                    sale["fecha_hora"].replace("T", " ")[:16],
                    client,
                    money(sale["total"]),
                    pill(
                        sale["estado"],
                        "red" if sale["estado"] == "Cancelada" else "green",
                    ),
                    secondary(
                        "Ver ticket",
                        show_handler(sale["id_venta"]),
                        ft.Icons.RECEIPT_LONG_OUTLINED,
                    ),
                ]
                for sale, client in page
            ],
        )
        footer.controls = [
            secondary(
                "Anterior", lambda event: move(-1), disabled=position["page"] == 0
            ),
            text(
                f"Página {position['page'] + 1} de {pages} · {len(matches)} ventas", 12
            ),
            secondary(
                "Siguiente",
                lambda event: move(1),
                disabled=position["page"] == pages - 1,
            ),
        ]

        if event is not None:
            app.page.update()

    def move(step):
        position["page"] += step
        refresh()
        app.page.update()

    search.on_change = refresh
    start.on_submit = end.on_submit = refresh
    refresh()

    return ft.Column(
        [
            heading(
                "Historial y tickets",
                "Consulta comprobantes, descarga PDF y registra cancelaciones.",
            ),
            card(
                ft.Column(
                    [
                        ft.ResponsiveRow(
                            [
                                search,
                                start,
                                end,
                                secondary("Filtrar", refresh, col={"xs": 12, "lg": 3}),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=12,
                            run_spacing=12,
                        ),
                        host,
                        footer,
                    ],
                    spacing=18,
                )
            ),
        ],
        spacing=22,
    )


async def sale_dialog(app, identifier):
    try:
        sale = await app.sales.detail(identifier)
    except Exception as exc:
        app.notify(str(exc), error=True)

        return

    error = text("", 12, color=ft.Colors.ERROR)

    async def download(event):
        try:
            data = await app.sales.pdf(identifier)
            await app.picker.save_file(
                file_name=f"ticket_{identifier}.pdf",
                src_bytes=data,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["pdf"],
            )
        except Exception as exc:
            error.value = str(exc)
            app.page.update()

    async def print_receipt(event):
        try:
            await app.printer.print_sale(sale, app.state.business_name)
            error.value = "Ticket enviado a la impresora."
        except Exception as exc:
            error.value = f"No se pudo imprimir: {exc}"

        app.page.update()

    def cancel(event):
        app.page.pop_dialog()
        cancel_sale_dialog(app, sale)

    actions = [
        secondary("Cerrar", lambda event: app.page.pop_dialog()),
        secondary("Descargar PDF", download, ft.Icons.DOWNLOAD),
        primary("Imprimir", print_receipt, ft.Icons.PRINT_OUTLINED),
    ]

    if sale["estado"] == "Completada" and app.products.can_manage:
        actions.insert(1, secondary("Cancelar venta", cancel, ft.Icons.CANCEL_OUTLINED))

    app.dialog(
        f"Ticket #{identifier}",
        ft.Column(
            [
                pill(
                    sale["estado"], "red" if sale["estado"] == "Cancelada" else "green"
                ),
                text(
                    f"{sale['fecha_hora'].replace('T', ' ')[:19]} · {sale.get('empleado', '—')}",
                    12,
                    color=MUTED,
                ),
                text(f"Cliente: {sale.get('cliente', 'Público general')}"),
                table(
                    ["PRODUCTO", "CANTIDAD", "PRECIO", "IMPORTE"],
                    [
                        [
                            item["nombre"],
                            item["cantidad"],
                            money(item["precio_unitario_venta"]),
                            money(item["subtotal"]),
                        ]
                        for item in sale.get("items", [])
                    ],
                ),
                text(f"Impuesto incluido: {money(sale.get('impuesto', 0))}", 13),
                text(
                    f"Total: {money(sale['total'])} · {sale.get('metodo_pago', '—')}",
                    22,
                    True,
                ),
                *(
                    [note(sale.get("cancel_motivo") or "Venta cancelada")]
                    if sale["estado"] == "Cancelada"
                    else []
                ),
                error,
            ],
            width=760,
            height=490,
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
        ),
        actions,
    )


def cancel_sale_dialog(app, sale):
    reason = ft.TextField(label="Motivo de cancelación", max_length=250)
    error = text("", 12, color=ft.Colors.ERROR)
    submit = primary("Confirmar cancelación", None)
    back = secondary("Volver", lambda event: app.page.pop_dialog())
    pending = {"body": None}

    async def confirm(event):
        if submit.disabled:
            return

        if pending["body"] is None:
            if not (reason.value or "").strip():
                error.value = "Captura el motivo de cancelación."
                app.page.update()

                return

            pending["body"] = {
                "operation_id": str(uuid4()),
                "motivo": reason.value.strip(),
            }

        submit.disabled = True
        reason.disabled = back.disabled = True
        app.page.update()

        try:
            await app.sales.cancel(sale["id_venta"], pending["body"])
            await app.products.refresh_after_write()
            app.page.pop_dialog()
            app.render()
            app.notify("Venta cancelada y existencias devueltas")
        except Exception as exc:
            uncertain = isinstance(exc, ApiError) and exc.status_code not in {
                401,
                403,
                404,
                409,
                422,
            }
            submit.disabled = False

            if not uncertain:
                reason.disabled = back.disabled = False
                pending["body"] = None

            error.value = str(exc) + (
                " Reintenta para confirmar la misma operación." if uncertain else ""
            )
            app.page.update()

    submit.on_click = confirm
    app.dialog(
        "Cancelar venta",
        ft.Column(
            [
                text(f"Ticket #{sale['id_venta']} · {money(sale['total'])}", 20, True),
                note(
                    "Se devolverán todas las cantidades al inventario. El comprobante y el motivo quedarán registrados."
                ),
                reason,
                error,
            ],
            width=500,
            tight=True,
            spacing=16,
        ),
        [back, submit],
    )
