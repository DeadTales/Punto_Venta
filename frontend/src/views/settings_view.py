import flet as ft

from ..components.ui import (
    MUTED,
    card,
    heading,
    pill,
    secondary,
    tabs,
    text,
)
from .settings_forms import account_form, appearance_form, printer_form


def settings_view(app):
    state = app.state
    kind = app.route.split("/")[1]

    if kind == "perifericos":
        content = printer_form(app)
    elif kind == "aspectos":
        content = appearance_form(app)
    else:
        content = account_form(app, password_change=kind != "correo")

    sync = state.sync

    async def push(e):
        try:
            result = await app.api.request("POST", "/api/sync/push")
            state.sync = await app.api.request("GET", "/api/sync/status")
            app.render()
            app.notify(
                f"Sincronización: {result['status']} · {result['sent']} eventos enviados"
            )
        except Exception as exc:
            app.notify(str(exc), error=True)

    async def retry(event_id):
        try:
            await app.api.request("POST", f"/api/sync/outbox/{event_id}/retry")
            await push(None)
        except Exception as exc:
            app.notify(str(exc), error=True)

    def retry_handler(identifier):
        async def handler(e):
            await retry(identifier)

        return handler

    return ft.Column(
        [
            heading(
                "Configuración", "Ajusta tu espacio, tu cuenta y tus dispositivos."
            ),
            tabs(app, "settings"),
            ft.ResponsiveRow(
                [
                    ft.Container(
                        card(ft.Column(content, spacing=20)), col={"sm": 12, "lg": 8}
                    ),
                    ft.Container(
                        card(
                            ft.Column(
                                [
                                    text("Conexión y sincronización", 17, True),
                                    pill(
                                        "Demostración"
                                        if state.demo
                                        else (
                                            "Base local"
                                            if sync.get("database_mode") == "local"
                                            else "Nube"
                                        ),
                                        "blue",
                                    ),
                                    text(
                                        "No hay operaciones reales en cola."
                                        if state.demo
                                        else f"Pendientes: {sync.get('counts', {}).get('pending', 0)} · Conflictos: {sync.get('counts', {}).get('conflict', 0)}",
                                        13,
                                        color=MUTED,
                                    ),
                                    *[
                                        ft.Column(
                                            [
                                                text(
                                                    f"Conflicto {c['event_id']}: {c['error']}",
                                                    11,
                                                    color=ft.Colors.ERROR,
                                                ),
                                                secondary(
                                                    "Reintentar tras corregir la causa",
                                                    retry_handler(c["event_id"]),
                                                ),
                                            ]
                                        )
                                        for c in sync.get("conflicts", [])
                                    ],
                                    secondary(
                                        "Sincronizar ahora",
                                        push,
                                        ft.Icons.SYNC,
                                        disabled=state.demo
                                        or not sync.get("configured"),
                                    ),
                                    text(
                                        "Para trabajar sin internet, la API y PostgreSQL deben estar instalados en la sucursal. La interfaz continúa usando la misma API local.",
                                        12,
                                        color=MUTED,
                                    ),
                                ],
                                spacing=18,
                            )
                        ),
                        col={"sm": 12, "lg": 4},
                    ),
                ],
                spacing=20,
                run_spacing=20,
            ),
        ],
        spacing=22,
    )
