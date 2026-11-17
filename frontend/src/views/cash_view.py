from uuid import uuid4

import flet as ft
from pydantic import BaseModel, ValidationError

from shared.catalog import Price, validation_message

from ..components.ui import card, heading, note, primary, secondary, stat, table, text
from ..models.state import money
from ..services.api_client import ApiError


class CashAmount(BaseModel):
    amount: Price


def cut_view(app):
    state = app.state
    expected = app.cash_expected
    shift_sales = (
        [
            sale
            for sale in state.sales
            if sale.get("id_turno") == (state.shift or {}).get("id_turno")
        ]
        if not state.demo
        else state.sales[state.shift_start :]
    )

    return ft.Column(
        [
            heading(
                "Corte de caja",
                "Apertura, conciliación e historial de tus turnos.",
                [
                    primary(
                        "Cerrar caja" if state.shift_open else "Abrir caja",
                        lambda event: cash_dialog(app, state.shift_open),
                        ft.Icons.POINT_OF_SALE,
                    )
                ],
            ),
            ft.ResponsiveRow(
                [
                    stat(
                        "Estado",
                        "Abierta" if state.shift_open else "Cerrada",
                        "Turno del usuario actual",
                        ft.Icons.LOCK_OPEN,
                    ),
                    stat(
                        "Fondo inicial",
                        money(state.opening_cash) if state.shift_open else "—",
                        "Importe de apertura",
                        ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED,
                    ),
                    stat(
                        "Efectivo esperado",
                        money(expected) if state.shift_open else "—",
                        "Fondo más ventas en efectivo",
                        ft.Icons.PAYMENTS_OUTLINED,
                    ),
                    stat(
                        "Tickets del turno",
                        len(shift_sales) if state.shift_open else 0,
                        "Incluye comprobantes cancelados",
                        ft.Icons.RECEIPT_LONG_OUTLINED,
                    ),
                ],
                spacing=16,
                run_spacing=16,
            ),
            card(
                ft.Column(
                    [
                        text("Turnos registrados", 18, True),
                        table(
                            [
                                "TURNO",
                                "APERTURA",
                                "ESTADO",
                                "ESPERADO",
                                "CONTADO",
                                "DIFERENCIA",
                            ],
                            [
                                [
                                    shift["id_turno"],
                                    shift.get("apertura", "—").replace("T", " ")[:16],
                                    shift["estado"],
                                    money(shift["efectivo_esperado"])
                                    if shift.get("efectivo_esperado") is not None
                                    else "—",
                                    money(shift["efectivo_contado"])
                                    if shift.get("efectivo_contado") is not None
                                    else "—",
                                    money(shift["diferencia"])
                                    if shift.get("diferencia") is not None
                                    else "—",
                                ]
                                for shift in state.shift_history
                            ],
                        ),
                    ],
                    spacing=16,
                )
            ),
            note(
                "El corte conserva el efectivo esperado, el contado y la diferencia. Las ventas de un turno cerrado conservan su cierre."
            ),
        ],
        spacing=22,
    )


def cash_dialog(app, closing=False):
    amount = ft.TextField(
        label="Efectivo contado" if closing else "Fondo inicial",
        value=str(app.cash_expected) if closing else "0",
        prefix=ft.Text("$ "),
    )
    notes = ft.TextField(
        label="Notas del cierre (opcional)", max_length=500, visible=closing
    )
    error = text("", 12, color=ft.Colors.ERROR)
    submit = primary("Confirmar cierre" if closing else "Abrir turno", None)
    cancel = secondary("Cancelar", lambda event: app.page.pop_dialog())
    pending = {"body": None}

    async def confirm(event):
        if submit.disabled:
            return

        try:
            if pending["body"] is None:
                value = CashAmount(amount=amount.value).amount
                pending["body"] = {
                    "operation_id": str(uuid4()),
                    "efectivo_contado" if closing else "fondo_inicial": str(value),
                }

                if closing:
                    pending["body"]["notas"] = notes.value or None

            submit.disabled = True
            amount.disabled = notes.disabled = cancel.disabled = True
            app.page.update()
            result = await (
                app.close_cash(pending["body"])
                if closing
                else app.open_cash(pending["body"])
            )
            app.page.pop_dialog()
            app.render()
            app.notify(
                f"Caja cerrada · Diferencia: {money(result['diferencia'])}"
                if closing
                else "Turno abierto"
            )
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
                amount.disabled = notes.disabled = cancel.disabled = False
                pending["body"] = None

            error.value = (
                validation_message(exc.errors())
                if isinstance(exc, ValidationError)
                else str(exc)
            )

            if uncertain:
                error.value += " Reintenta para confirmar la misma operación."

            app.page.update()

    submit.on_click = confirm
    app.dialog(
        "Cerrar turno" if closing else "Abrir caja",
        ft.Column([amount, notes, error], width=450, tight=True, spacing=16),
        [cancel, submit],
    )
