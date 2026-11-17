import flet as ft
from pydantic import ValidationError

from shared.catalog import validation_message

from ..components.ui import note, primary, secondary, text


def person_dialog(app, users, record=None):
    original = record or {}
    name = ft.TextField(
        label="Nombre",
        value=original.get("nombre", ""),
        max_length=100 if users else 150,
    )
    surname = ft.TextField(
        label="Apellidos", value=original.get("apellido", ""), max_length=100
    )
    email = ft.TextField(
        label="Correo" + ("" if users else " (opcional)"),
        value=original.get("correo") or "",
        max_length=150,
    )
    phone = ft.TextField(
        label="Teléfono (opcional)", value=original.get("telefono") or "", max_length=20
    )
    fiscal = ft.TextField(
        label="RFC o identificación fiscal (opcional)",
        value=original.get("rfc_o_identificacion_fiscal") or "",
        max_length=50,
    )
    role = ft.Dropdown(
        label="Rol",
        value=original.get("rol", "Cajero"),
        options=[
            ft.DropdownOption(role)
            for role in ("Cajero", "Supervisor", "Administrador")
        ],
    )
    active = ft.Switch(label="Acceso activo", value=original.get("activo", True))
    password = ft.TextField(
        label="Nueva contraseña (opcional)" if record else "Contraseña inicial",
        password=True,
        can_reveal_password=True,
    )
    error = text("", 12, color=ft.Colors.ERROR)
    submit = primary("Guardar", None)

    async def save(event):
        if submit.disabled:
            return

        try:
            values = {
                "nombre": name.value,
                "correo": email.value or None,
                "telefono": phone.value or None,
            }

            if users:
                values.update(
                    apellido=surname.value, rol=role.value, activo=bool(active.value)
                )

                if password.value or record is None:
                    values["password"] = password.value or ""
            else:
                values["rfc_o_identificacion_fiscal"] = fiscal.value or None

            submit.disabled = True
            app.page.update()
            await app.people.save(
                values, users, original.get("id_empleado" if users else "id_cliente")
            )
            await app.products.refresh_after_write()
            app.page.pop_dialog()
            app.render()
            app.notify(
                "Registro guardado" + (" en la demostración" if app.state.demo else "")
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
    controls = [
        name,
        *([surname] if users else []),
        email,
        phone,
        *(
            [
                role,
                active,
                password,
                note(
                    "Usa al menos 12 caracteres y hasta 72 bytes. Una nueva contraseña invalida las sesiones anteriores."
                ),
            ]
            if users
            else [fiscal]
        ),
        error,
    ]
    app.dialog(
        ("Editar" if record else "Nuevo") + (" empleado" if users else " cliente"),
        ft.Column(
            controls,
            width=490,
            height=500 if users else 330,
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
        ),
        [secondary("Cancelar", lambda event: app.page.pop_dialog()), submit],
    )


def delete_person_dialog(app, users, record):
    submit = primary("Desactivar" if users else "Eliminar", None)
    error = text("", 12, color=ft.Colors.ERROR)

    async def remove(event):
        if submit.disabled:
            return

        submit.disabled = True
        app.page.update()

        try:
            await app.people.delete(
                record["id_empleado" if users else "id_cliente"], users
            )
            await app.products.refresh_after_write()
            app.page.pop_dialog()
            app.render()
            app.notify("Acceso desactivado" if users else "Cliente eliminado")
        except Exception as exc:
            submit.disabled = False
            error.value = str(exc)
            app.page.update()

    submit.on_click = remove
    app.dialog(
        "Desactivar empleado" if users else "Eliminar cliente",
        ft.Column(
            [
                text(record["nombre"], 20, True),
                note(
                    "Se conservará el historial de ventas del empleado."
                    if users
                    else "Sólo pueden eliminarse clientes sin ventas registradas."
                ),
                error,
            ],
            width=450,
            tight=True,
        ),
        [secondary("Cancelar", lambda event: app.page.pop_dialog()), submit],
    )
