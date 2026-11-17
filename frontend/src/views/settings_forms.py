import flet as ft
from pydantic import ValidationError

from shared.catalog import validation_message
from shared.people import EmailChange, PasswordChange

from ..components.ui import MUTED, note, primary, secondary, text


def printer_form(app):
    config = app.printer.config
    connection = ft.Dropdown(
        label="Conexión",
        value=config["connection"],
        options=[
            ft.DropdownOption(value)
            for value in ("USB", "Serial / COM", "Red / Ethernet")
        ],
    )
    vendor = ft.TextField(
        label="USB: fabricante (ej. 0x04b8)", value=config["vendor_id"]
    )
    product = ft.TextField(
        label="USB: producto (ej. 0x0202)", value=config["product_id"]
    )
    address = ft.TextField(
        label="Puerto COM, dispositivo serial o dirección de red",
        value=config["address"],
    )
    port = ft.TextField(label="Puerto de red", value=str(config["port"]))
    baudrate = ft.TextField(
        label="Velocidad serial (baudios)", value=str(config["baudrate"])
    )
    cut = ft.Switch(label="Cortar papel al terminar", value=bool(config["cut"]))
    error = text("", 12, color=ft.Colors.ERROR)

    def update(event=None):
        vendor.visible = product.visible = connection.value == "USB"
        address.visible = connection.value != "USB"
        port.visible = connection.value == "Red / Ethernet"
        baudrate.visible = connection.value == "Serial / COM"

        if event:
            app.page.update()

    def save(event):
        try:
            values = {
                "connection": connection.value,
                "vendor_id": vendor.value.strip(),
                "product_id": product.value.strip(),
                "address": address.value.strip(),
                "port": int(port.value),
                "baudrate": int(baudrate.value),
                "cut": bool(cut.value),
            }

            if connection.value == "USB":
                if not all(
                    0 < int(value, 0) <= 65535
                    for value in (values["vendor_id"], values["product_id"])
                ):
                    raise ValueError("Revisa los identificadores USB")
            elif not values["address"]:
                raise ValueError("Captura el puerto o dirección")

            if not 1 <= values["port"] <= 65535 or values["baudrate"] <= 0:
                raise ValueError("Revisa el puerto de red o velocidad serial")

            app.printer.save(config=values)
            app.state.peripheral = connection.value
            error.value = "Configuración guardada."
        except (OSError, ValueError) as exc:
            error.value = str(exc)

        app.page.update()

    async def test_print(event):
        try:
            sale = {
                "id_venta": "PRUEBA",
                "fecha_hora": "Prueba de conexión",
                "total": "0",
                "items": [],
                "metodo_pago": "Prueba",
            }
            await app.printer.print_sale(sale, app.state.business_name)
            error.value = "Comprobante de prueba enviado."
        except Exception as exc:
            error.value = f"No se pudo imprimir: {exc}"

        app.page.update()

    connection.on_select = update
    update()

    return [
        text("Impresoras y lectores", 19, True),
        connection,
        vendor,
        product,
        address,
        port,
        baudrate,
        cut,
        ft.Row(
            [
                primary("Guardar configuración", save, ft.Icons.SAVE_OUTLINED),
                secondary("Imprimir prueba", test_print, ft.Icons.PRINT_OUTLINED),
            ],
            wrap=True,
        ),
        error,
        note(
            "Los lectores USB que funcionan como teclado se usan en el buscador de la caja: escanea y pulsa Enter. En USB la impresora necesita el controlador y acceso al dispositivo."
        ),
    ]


def appearance_form(app):
    def set_theme(value):
        app.printer.save(theme=value)
        app.state.theme = value
        app.page.theme_mode = (
            ft.ThemeMode.DARK if value == "dark" else ft.ThemeMode.LIGHT
        )
        app.render()

    return [
        text("Hazlo tuyo", 19, True),
        text("La apariencia se conserva en este equipo.", 13, color=MUTED),
        ft.Row(
            [
                secondary(
                    "Tema claro",
                    lambda event: set_theme("light"),
                    ft.Icons.LIGHT_MODE_OUTLINED,
                ),
                primary(
                    "Tema oscuro",
                    lambda event: set_theme("dark"),
                    ft.Icons.DARK_MODE_OUTLINED,
                ),
            ],
            wrap=True,
        ),
    ]


def account_form(app, password_change=False):
    current = ft.TextField(
        label="Contraseña actual", password=True, can_reveal_password=True
    )
    password = ft.TextField(
        label="Nueva contraseña", password=True, can_reveal_password=True
    )
    repeat = ft.TextField(label="Confirmar nueva contraseña", password=True)
    email = ft.TextField(
        label="Nuevo correo de acceso", value=app.state.user.get("correo", "")
    )
    error = text("", 12, color=ft.Colors.ERROR)
    submit = primary(
        "Cambiar contraseña" if password_change else "Guardar correo", None
    )

    async def save(event):
        if submit.disabled:
            return

        try:
            if password_change:
                if password.value != repeat.value:
                    raise ValueError("La confirmación de la contraseña no coincide")

                body = PasswordChange(
                    current_password=current.value, new_password=password.value
                ).model_dump()
                path = "/api/auth/password"
            else:
                body = EmailChange(
                    correo=email.value, current_password=current.value
                ).model_dump()
                path = "/api/auth/email"

            submit.disabled = True
            app.page.update()

            if app.state.demo:
                if not password_change:
                    app.state.user["correo"] = body["correo"]

                message = "Formulario validado en la demostración"
            else:
                result = await app.api.request("PUT", path, json=body)
                app.api.token = result["access_token"]
                app.state.user = result["user"]
                await app.products.refresh_after_write()
                message = "Datos actualizados y sesión renovada"

            current.value = password.value = repeat.value = ""
            app.render()
            app.notify(message)
        except Exception as exc:
            error.value = (
                validation_message(exc.errors())
                if isinstance(exc, ValidationError)
                else str(exc)
            )
        finally:
            submit.disabled = False
            app.page.update()

    submit.on_click = save

    return [
        text("Cambiar contraseña" if password_change else "Correo de acceso", 19, True),
        current,
        *([password, repeat] if password_change else [email]),
        error,
        submit,
        note(
            "Confirma tu contraseña actual. Al guardar se renueva esta sesión y se invalidan los tokens anteriores de tu cuenta."
        ),
    ]
