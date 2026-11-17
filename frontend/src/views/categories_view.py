import flet as ft

from ..components.ui import card, heading, primary, table


def categories_view(app):
    from .inventory_view import category_dialog, delete_dialog

    rows = []

    for category in app.state.categories:
        actions = (
            ft.Row(
                [
                    ft.IconButton(
                        ft.Icons.EDIT_OUTLINED,
                        tooltip="Editar categoría",
                        on_click=lambda e, c=category: category_dialog(app, c),
                    ),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE,
                        tooltip="Eliminar categoría",
                        on_click=lambda e, c=category: delete_dialog(
                            app, "categories", c
                        ),
                    ),
                ],
                spacing=0,
            )
            if app.products.can_manage
            else ""
        )
        count = sum(
            p["id_categoria"] == category["id_categoria"] for p in app.state.products
        )
        rows.append(
            [category["nombre"], category.get("descripcion") or "—", count, actions]
        )

    return ft.Column(
        [
            heading(
                "Categorías",
                "Organiza los productos por familia.",
                [
                    primary(
                        "Nueva categoría",
                        lambda e: category_dialog(app),
                        ft.Icons.ADD,
                    )
                ]
                if app.products.can_manage
                else [],
            ),
            card(table(["NOMBRE", "DESCRIPCIÓN", "PRODUCTOS", ""], rows)),
        ],
        spacing=22,
    )
