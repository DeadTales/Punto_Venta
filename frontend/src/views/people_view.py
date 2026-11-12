import re

import flet as ft

from ..components.ui import MUTED, card, heading, note, pill, primary, secondary, table, text


def people_view(app, users=False):
    state = app.state
    items = state.users if users else state.clients
    search = ft.TextField(hint_text="Buscar por nombre, correo o identificación", prefix_icon=ft.Icons.SEARCH,
                          dense=True, expand=True, border_radius=8)
    host = ft.Container()

    def refresh(e=None):
        q = (search.value or "").casefold()
        rows = []
        for item in items:
            if q not in " ".join(str(v or "") for v in item.values()).casefold():
                continue
            name = item["nombre"] + (" " + item.get("apellido", "") if users else "")
            rows.append([ft.Column([text(name, 13, True), text(item.get("correo") or "Sin correo", 11, color=MUTED)], spacing=4),
                         item.get("telefono") or "—", pill(item["rol"], "blue") if users else item.get("rfc_o_identificacion_fiscal") or "—",
                         ft.IconButton(ft.Icons.EDIT_OUTLINED, tooltip="Editar registro de demostración", disabled=not state.demo,
                                       on_click=lambda e, record=item: person_dialog(app, users, record))])
        host.content = table(["USUARIO / CORREO" if users else "CLIENTE / CORREO", "TELÉFONO", "ROL" if users else "RFC / IDENTIFICACIÓN", ""], rows)
        if e:
            app.page.update()

    search.on_change = refresh
    refresh()
    title = "Usuarios" if users else "Clientes"
    return ft.Column([
        heading(title, "Control de acceso y personal de tu negocio." if users else "Conoce a tus compradores y conserva sus datos de contacto.",
                [primary("Nuevo usuario" if users else "Nuevo cliente", lambda e: person_dialog(app, users), ft.Icons.PERSON_ADD_ALT_1, disabled=not state.demo)]),
        card(ft.Column([
            ft.Row([search, pill(f"{len(items)} registros", "blue")]), host,
        ], spacing=18)),
        note("Roles del sistema: Administrador, Supervisor y Cajero. La API verifica permisos en cada operación." if users else "Público general no necesita registro. El RFC es opcional y se conserva para identificar al comprador."),
        *([] if state.demo else [note("Esta primera vista permite consultar datos de la API. El alta y la edición están disponibles en la demostración; el CRUD de este módulo queda por integrar.")]),
    ], spacing=22)


def person_dialog(app, users, record=None):
    original = record or {}
    name = ft.TextField(label="Nombre", value=original.get("nombre", ""), max_length=100 if users else 150)
    surname = ft.TextField(label="Apellidos", value=original.get("apellido", ""), max_length=100)
    email = ft.TextField(label="Correo" + ("" if users else " (opcional)"), value=original.get("correo") or "", max_length=150)
    phone = ft.TextField(label="Teléfono (opcional)", value=original.get("telefono") or "", max_length=20)
    fiscal = ft.TextField(label="RFC o identificación fiscal (opcional)", value=original.get("rfc_o_identificacion_fiscal") or "", max_length=50)
    role = ft.Dropdown(label="Rol", value=original.get("rol", "Cajero"), options=[ft.DropdownOption(r) for r in ["Cajero", "Supervisor", "Administrador"]])
    error = text("", 12, color=ft.Colors.ERROR)

    def save(e):
        if not app.state.demo:
            return
        if not (name.value or "").strip() or users and not (surname.value or "").strip():
            error.value = "Completa el nombre" + (" y los apellidos." if users else ".")
        elif (users or email.value) and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.value or ""):
            error.value = "Escribe un correo válido."
        else:
            items = app.state.users if users else app.state.clients
            id_key = "id_empleado" if users else "id_cliente"
            values = {"nombre": name.value.strip(), "correo": email.value or None, "telefono": phone.value or None}
            values.update({"apellido": surname.value.strip(), "rol": role.value} if users else {"rfc_o_identificacion_fiscal": fiscal.value or None})
            if record:
                record.update(values)
            else:
                items.append({id_key: max([i[id_key] for i in items], default=0) + 1, **values})
            app.page.pop_dialog()
            app.render()
            app.notify("Registro guardado en la demostración")
        app.page.update()

    app.dialog(("Editar" if record else "Nuevo") + (" usuario" if users else " cliente"),
        ft.Column([name, *([surname] if users else []), email, phone, role if users else fiscal, error,
                   text("Datos de demostración; los cambios duran mientras la aplicación esté abierta.", 11, color=MUTED)], width=470, tight=True, spacing=14),
        [secondary("Cancelar", lambda e: app.page.pop_dialog()), primary("Guardar", save)])
