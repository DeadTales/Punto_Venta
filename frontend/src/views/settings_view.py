import re

import flet as ft

from ..components.ui import GREEN, MUTED, card, heading, note, pill, primary, secondary, tabs, text


def settings_view(app):
    state = app.state
    kind = app.route.split("/")[1]
    if kind == "perifericos":
        connection = ft.Dropdown(label="Conexión de impresora térmica", value=state.peripheral,
                                 options=[ft.DropdownOption(v) for v in ["USB", "Serial / COM", "Red / Ethernet"]])
        address = ft.TextField(label="Identificador USB, puerto COM o dirección IP", hint_text="Ej. 0x04b8:0x0202, /dev/ttyUSB0 o 192.168.1.50")
        scanner = ft.Switch(label="Lector de código como teclado (USB HID)", value=True)

        def save(e):
            state.peripheral = connection.value
            app.notify("Preferencia guardada durante esta sesión. La impresión física aún no está integrada.")

        content = [text("Impresoras y lectores", 19, True), text("Configura el puesto de trabajo.", 13, color=MUTED),
                   connection, address, scanner, primary("Guardar preferencia de sesión", save, ft.Icons.SAVE_OUTLINED),
                   note("Maquetado de periféricos: python-escpos, pyusb y pyserial están declarados. No se envían comandos al hardware desde esta vista.")]
    elif kind == "aspectos":
        def set_theme(value):
            state.theme = value
            app.page.theme_mode = ft.ThemeMode.DARK if value == "dark" else ft.ThemeMode.LIGHT
            app.render()

        content = [text("Hazlo tuyo", 19, True), text("Elige la apariencia de tu espacio de trabajo.", 13, color=MUTED),
                   ft.Row([secondary("Tema claro", lambda e: set_theme("light"), ft.Icons.LIGHT_MODE_OUTLINED),
                           primary("Tema oscuro", lambda e: set_theme("dark"), ft.Icons.DARK_MODE_OUTLINED)], wrap=True),
                   pill("Oscuro" if state.theme == "dark" else "Claro"), note("La apariencia se aplica inmediatamente y dura durante esta sesión.")]
    elif kind == "contraseña":
        current = ft.TextField(label="Contraseña actual", password=True, can_reveal_password=True)
        new = ft.TextField(label="Nueva contraseña", password=True, can_reveal_password=True)
        repeat = ft.TextField(label="Repetir nueva contraseña", password=True)
        error = text("", 12, color=ft.Colors.ERROR)

        def save(e):
            if not current.value or len(new.value or "") < 12 or new.value != repeat.value:
                error.value = "Completa la contraseña actual y usa al menos 12 caracteres. La confirmación debe coincidir."
                app.page.update()
                return
            app.notify("Formulario válido. Demostración: no se ha cambiado ninguna contraseña.")

        content = [text("Cambiar contraseña", 19, True), current, new, repeat, error,
                   primary("Validar formulario", save, ft.Icons.LOCK_OUTLINED, disabled=not state.demo),
                   note("Maquetado: falta integrar el endpoint de cambio de contraseña y la revocación de sesiones.")]
    else:
        email = ft.TextField(label="Nuevo correo de acceso", value=state.user.get("correo", ""))
        password = ft.TextField(label="Confirma tu contraseña", password=True, can_reveal_password=True)
        error = text("", 12, color=ft.Colors.ERROR)

        def save(e):
            if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.value or "") or not password.value:
                error.value = "Escribe un correo válido y confirma tu contraseña."
                app.page.update()
                return
            state.user["correo"] = email.value
            app.notify("Correo actualizado sólo en la demostración")

        content = [text("Correo de acceso", 19, True), text("Correo actual: " + state.user.get("correo", "—"), 13, color=MUTED), email, password, error,
                   primary("Guardar en demostración", save, ft.Icons.MAIL_OUTLINE, disabled=not state.demo),
                   note("En producción se necesita verificar el nuevo correo mediante un enlace y volver a autenticar al usuario. Este flujo todavía no está integrado.")]
    sync = state.sync

    async def push(e):
        try:
            result = await app.api.request("POST", "/api/sync/push")
            state.sync = await app.api.request("GET", "/api/sync/status")
            app.render()
            app.notify(f"Sincronización: {result['status']} · {result['sent']} eventos enviados")
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

    return ft.Column([
        heading("Configuración", "Ajusta tu espacio, tu cuenta y tus dispositivos."), tabs(app, "settings"),
        ft.ResponsiveRow([
            ft.Container(card(ft.Column(content, spacing=20)), col={"sm": 12, "lg": 8}),
            ft.Container(card(ft.Column([
                text("Conexión y sincronización", 17, True),
                pill("Demostración" if state.demo else ("Base local" if sync.get("database_mode") == "local" else "Nube"), "blue"),
                text("No hay operaciones reales en cola." if state.demo else f"Pendientes: {sync.get('counts', {}).get('pending', 0)} · Conflictos: {sync.get('counts', {}).get('conflict', 0)}", 13, color=MUTED),
                *[ft.Column([text(f"Conflicto {c['event_id']}: {c['error']}", 11, color=ft.Colors.ERROR),
                             secondary("Reintentar tras corregir la causa", retry_handler(c["event_id"]))]) for c in sync.get("conflicts", [])],
                secondary("Sincronizar ahora", push, ft.Icons.SYNC, disabled=state.demo or not sync.get("configured")),
                text("Para trabajar sin internet, la API y PostgreSQL deben estar instalados en la sucursal. La interfaz continúa usando la misma API local.", 12, color=MUTED),
            ], spacing=18)), col={"sm": 12, "lg": 4}),
        ], spacing=20, run_spacing=20),
    ], spacing=22)
