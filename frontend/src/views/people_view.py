import flet as ft

from ..components.ui import (
    MUTED,
    card,
    heading,
    note,
    pill,
    primary,
    table,
    text,
)
from .people_dialogs import delete_person_dialog, person_dialog


def people_view(app, users=False):
    state = app.state
    items = state.users if users else state.clients
    search = ft.TextField(
        hint_text="Buscar por nombre, correo o identificación",
        prefix_icon=ft.Icons.SEARCH,
        dense=True,
        expand=True,
        border_radius=8,
    )
    host = ft.Container()

    def refresh(e=None):
        q = (search.value or "").casefold()
        rows = []

        for item in items:
            if q not in " ".join(str(v or "") for v in item.values()).casefold():
                continue

            name = item["nombre"] + (" " + item.get("apellido", "") if users else "")
            rows.append(
                [
                    ft.Column(
                        [
                            text(name, 13, True),
                            text(item.get("correo") or "Sin correo", 11, color=MUTED),
                        ],
                        spacing=4,
                    ),
                    item.get("telefono") or "—",
                    pill(item["rol"], "blue")
                    if users
                    else item.get("rfc_o_identificacion_fiscal") or "—",
                    ft.Row(
                        [
                            ft.IconButton(
                                ft.Icons.EDIT_OUTLINED,
                                tooltip="Editar registro",
                                disabled=users
                                and not (
                                    state.demo
                                    or state.user.get("rol") == "Administrador"
                                ),
                                on_click=lambda e, record=item: person_dialog(
                                    app, users, record
                                ),
                            ),
                            ft.IconButton(
                                ft.Icons.PERSON_OFF_OUTLINED
                                if users
                                else ft.Icons.DELETE_OUTLINE,
                                tooltip="Desactivar empleado"
                                if users
                                else "Eliminar cliente",
                                disabled=not app.products.can_manage,
                                on_click=lambda event, record=item: (
                                    delete_person_dialog(app, users, record)
                                ),
                            ),
                        ],
                        spacing=0,
                    ),
                ]
            )

        host.content = table(
            [
                "USUARIO / CORREO" if users else "CLIENTE / CORREO",
                "TELÉFONO",
                "ROL" if users else "RFC / IDENTIFICACIÓN",
                "",
            ],
            rows,
        )

        if e:
            app.page.update()

    search.on_change = refresh
    refresh()
    title = "Usuarios" if users else "Clientes"

    return ft.Column(
        [
            heading(
                title,
                "Control de acceso y personal de tu negocio."
                if users
                else "Conoce a tus compradores y conserva sus datos de contacto.",
                [
                    primary(
                        "Nuevo usuario" if users else "Nuevo cliente",
                        lambda e: person_dialog(app, users),
                        ft.Icons.PERSON_ADD_ALT_1,
                        disabled=users
                        and not (
                            state.demo or state.user.get("rol") == "Administrador"
                        ),
                    )
                ],
            ),
            card(
                ft.Column(
                    [
                        ft.Row([search, pill(f"{len(items)} registros", "blue")]),
                        host,
                    ],
                    spacing=18,
                )
            ),
            note(
                "Roles del sistema: Administrador, Supervisor y Cajero. La API verifica permisos en cada operación."
                if users
                else "Público general no necesita registro. El RFC es opcional y se conserva para identificar al comprador."
            ),
        ],
        spacing=22,
    )
