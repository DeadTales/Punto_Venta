import flet as ft

GREEN = "#176B5B"
MUTED = ft.Colors.ON_SURFACE_VARIANT
LINE = ft.Colors.OUTLINE_VARIANT


def text(value, size=14, bold=False, color=None, **kwargs):
    return ft.Text(str(value), size=size, weight=ft.FontWeight.W_600 if bold else ft.FontWeight.W_400,
                   color=color, **kwargs)


def pill(label, tone="green"):
    colors = {"green": ("#E2F3EC", "#176B5B"), "amber": ("#FFF3DA", "#8C5A0E"),
              "blue": ("#E8EFFC", "#355E9A"), "red": ("#FBE8E8", "#AD3434")}
    bg, fg = colors[tone]
    return ft.Container(text(label, 11, True, fg), padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                        bgcolor=bg, border_radius=20)


def card(content, **kwargs):
    return ft.Container(content, padding=22, bgcolor=ft.Colors.SURFACE, border_radius=14,
                        border=ft.Border.all(1, LINE), **kwargs)


def heading(title, subtitle="", actions=None):
    return ft.Row([
        ft.Column([text(title, 28, True), text(subtitle, 13, color=MUTED)], spacing=5, expand=True),
        *(actions or []),
    ], spacing=14)


def primary(label, handler, icon=None, **kwargs):
    return ft.Button(label, icon=icon, on_click=handler,
                     style=ft.ButtonStyle(
                         bgcolor={ft.ControlState.DEFAULT: GREEN, ft.ControlState.DISABLED: "#DFE5E2"},
                         color={ft.ControlState.DEFAULT: "white", ft.ControlState.DISABLED: "#7C8B84"},
                         shape=ft.RoundedRectangleBorder(radius=8)), **kwargs)


def secondary(label, handler, icon=None, **kwargs):
    return ft.OutlinedButton(label, icon=icon, on_click=handler, **kwargs)


def stat(label, value, caption, icon, tone="green"):
    return card(ft.Column([
        ft.Row([text(label, 12, color=MUTED, expand=True), ft.Icon(icon, color=GREEN, size=19)]),
        text(value, 27, True), text(caption, 11, color=MUTED),
    ], spacing=12), col={"sm": 6, "lg": 3})


def table(headers, rows, empty="No hay registros para mostrar."):
    if not rows:
        return ft.Container(ft.Column([ft.Icon(ft.Icons.INBOX_OUTLINED, size=34, color=MUTED),
                                      text(empty, 14, color=MUTED)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=40)
    control = ft.DataTable(
        columns=[ft.DataColumn(text(h, 11, True, MUTED)) for h in headers],
        rows=[ft.DataRow(cells=[ft.DataCell(v if isinstance(v, ft.Control) else text(v, 13)) for v in row]) for row in rows],
        heading_row_height=44, data_row_min_height=58, data_row_max_height=72,
        column_spacing=28, horizontal_margin=12, divider_thickness=0.5,
    )
    return ft.Row([control], scroll=ft.ScrollMode.AUTO)


def tabs(app, group):
    routes = [(key, title) for key, title, _ in app.routes if key.startswith(group + "/")]
    return ft.Row([ft.Button(title, on_click=lambda e, route=key: app.navigate(route),
                            bgcolor=GREEN if app.route == key else ft.Colors.SURFACE,
                            color="white" if app.route == key else MUTED,
                            elevation=0, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))
                   for key, title in routes], wrap=True, spacing=8)


def note(message, icon=ft.Icons.INFO_OUTLINE):
    return ft.Container(ft.Row([ft.Icon(icon, color=GREEN, size=18), text(message, 12, color=MUTED, expand=True)], spacing=10),
                        padding=14, bgcolor=ft.Colors.SURFACE_CONTAINER_LOW, border_radius=10)
