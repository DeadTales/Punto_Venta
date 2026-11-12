import asyncio
from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import uuid4

import flet as ft

from shared.inventory_excel import parse_inventory
from .components.ui import GREEN, MUTED, card, note, pill, primary, secondary, text
from .models.demo import demo_state
from .models.state import AppState
from .services.api_client import ApiClient, ApiError
from .views.inventory_view import inventory_view
from .views.people_view import people_view
from .views.pos_view import cart_view, cash_view
from .views.reports_view import reports_view
from .views.settings_view import settings_view


class PosApp:
    routes = [
        ("caja/inicio", "Inicio", ft.Icons.SPACE_DASHBOARD_OUTLINED),
        ("caja/corte", "Corte", ft.Icons.POINT_OF_SALE),
        ("carrito", "Carrito", ft.Icons.SHOPPING_CART_OUTLINED),
        ("inventario", "Inventario", ft.Icons.INVENTORY_2_OUTLINED),
        ("clientes", "Clientes", ft.Icons.PEOPLE_OUTLINE),
        ("usuarios", "Usuarios", ft.Icons.MANAGE_ACCOUNTS_OUTLINED),
        ("reportes/ventas", "Ventas", ft.Icons.BAR_CHART_OUTLINED),
        ("reportes/clientes", "Clientes", ft.Icons.PEOPLE_OUTLINE),
        ("reportes/usuarios", "Usuarios", ft.Icons.BADGE_OUTLINED),
        ("reportes/predicciones", "Predicciones", ft.Icons.AUTO_GRAPH),
        ("settings/perifericos", "Periféricos", ft.Icons.PRINT_OUTLINED),
        ("settings/aspectos", "Aspectos", ft.Icons.PALETTE_OUTLINED),
        ("settings/contraseña", "Contraseña", ft.Icons.LOCK_OUTLINE),
        ("settings/correo", "Correo", ft.Icons.MAIL_OUTLINE),
    ]

    def __init__(self, page, mode="demo", base_url="http://127.0.0.1:8000"):
        if mode not in {"demo", "api"}:
            raise ValueError("POS_MODE debe ser demo o api")
        self.page = page
        self.state = demo_state() if mode == "demo" else AppState(mode="api", shift_open=False)
        self.api = ApiClient(base_url) if mode == "api" else None
        self.route = "caja/inicio"
        self.filters = {}
        self.pending_sale = None
        self.catalog_stale = False
        self.picker = ft.FilePicker()
        page.services.append(self.picker)
        self.body = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=22)
        self.sidebar = ft.Container(width=224, bgcolor="#142D2A", padding=18)
        self.status = ft.Container()
        self.global_search = ft.TextField(hint_text="Ir a una vista…  Ctrl + K", prefix_icon=ft.Icons.SEARCH,
                                          width=310, dense=True, border_radius=9, text_size=12,
                                          on_submit=self.search_route)
        self.root = ft.Row([
            self.sidebar,
            ft.Container(ft.Column([
                ft.Row([text("ESPACIO DE TRABAJO", 10, True, MUTED, expand=True), self.global_search,
                        ft.IconButton(ft.Icons.REFRESH, tooltip="Actualizar datos de la API", visible=not self.state.demo, on_click=self.refresh_data), self.status], spacing=20),
                ft.Divider(height=14, color=ft.Colors.OUTLINE_VARIANT), self.body,
            ], expand=True, spacing=15), padding=ft.Padding.only(left=28, right=28, top=22, bottom=24), expand=True),
        ], expand=True, spacing=0)
        page.title = "Punto · Sistema de venta"
        page.padding = 0
        page.spacing = 0
        page.window.width, page.window.height = 1440, 940
        page.window.min_width, page.window.min_height = 980, 720
        page.theme = ft.Theme(color_scheme_seed=GREEN, use_material3=True, font_family="Roboto")
        page.theme_mode = ft.ThemeMode.LIGHT
        page.bgcolor = ft.Colors.SURFACE_CONTAINER_LOWEST
        page.on_keyboard_event = self.keyboard
        page.on_resize = lambda e: self.render()
        page.on_disconnect = self.disconnect
        page.add(self.root)
        self.render()

    async def disconnect(self, e):
        if self.api:
            await self.api.close()

    def navigate(self, route):
        if not self.state.demo and self.state.user.get("rol") != "Administrador" and route in {"usuarios", "reportes/usuarios"}:
            self.notify("Esta vista requiere el rol Administrador", error=True)
            return
        if route not in [r[0] for r in self.routes]:
            return
        self.route = route
        self.render()

    def keyboard(self, e):
        if e.ctrl and e.key.lower() == "k":
            self.page.run_task(self.global_search.focus)

    def search_route(self, e):
        query = (self.global_search.value or "").casefold().strip()
        matches = [(key, title) for key, title, _ in self.routes if query in (key + " " + title).casefold()]
        if len(matches) == 1:
            self.global_search.value = ""
            self.navigate(matches[0][0])
        elif matches:
            self.dialog("Ir a una vista", ft.Column([
                ft.TextButton(key.split("/")[0].capitalize() + " · " + title,
                              on_click=lambda e, route=key: self.choose_route(route)) for key, title in matches
            ], width=400, tight=True, scroll=ft.ScrollMode.AUTO), [secondary("Cerrar", lambda e: self.page.pop_dialog())])
        else:
            self.notify("No se encontró una vista con ese nombre")

    def choose_route(self, route):
        self.page.pop_dialog()
        self.global_search.value = ""
        self.navigate(route)

    def build_sidebar(self):
        compact = bool(self.page.width and self.page.width < 1150)
        self.sidebar.width = 80 if compact else 224
        links = [
            ("caja/inicio", "Caja", ft.Icons.SPACE_DASHBOARD_OUTLINED),
            ("carrito", "Carrito", ft.Icons.SHOPPING_CART_OUTLINED),
            ("inventario", "Inventario", ft.Icons.INVENTORY_2_OUTLINED),
            ("clientes", "Clientes", ft.Icons.PEOPLE_OUTLINE),
            ("reportes/ventas", "Reportes", ft.Icons.BAR_CHART_OUTLINED),
            ("usuarios", "Usuarios", ft.Icons.MANAGE_ACCOUNTS_OUTLINED),
        ]
        nav = []
        for route, label, icon in links:
            if route == "usuarios" and not self.state.demo and self.state.user.get("rol") != "Administrador":
                continue
            selected = self.route.split("/")[0] == route.split("/")[0]
            nav.append(ft.Container(ft.Row([
                ft.Icon(icon, size=21, color="#B6E7D7" if selected else "#9DB6B0"),
                *([] if compact else [text(label, 13, selected, "#F4FBF8" if selected else "#B8CDC7", expand=True),
                                     *([pill(str(len(self.state.cart)), "green")] if label == "Carrito" and self.state.cart else [])]),
            ], spacing=14), padding=13, border_radius=9, bgcolor="#275047" if selected else None,
                tooltip=label, on_click=lambda e, target=route: self.navigate(target)))
        identity = ft.Container(text("P", 23, True, "white"), width=40, height=40, bgcolor="#2D997F", border_radius=12,
                                alignment=ft.Alignment.CENTER)
        settings_selected = self.route.startswith("settings/")
        return ft.Column([
            ft.Row([identity, *([] if compact else [ft.Column([text("punto", 25, True, "white"), text("PUNTO DE VENTA", 8, True, "#9DB6B0")], spacing=0)])], spacing=12),
            ft.Container(height=24),
            *([] if compact else [text("PRINCIPAL", 9, True, "#78998F")]),
            *nav,
            ft.Container(expand=True),
            ft.Container(ft.Row([ft.Icon(ft.Icons.SETTINGS_OUTLINED, color="#B8CDC7", size=21),
                                 *([] if compact else [text("Configuración", 13, color="#B8CDC7")])], spacing=14),
                         padding=13, border_radius=9, bgcolor="#275047" if settings_selected else None,
                         tooltip="Configuración", on_click=lambda e: self.navigate("settings/perifericos")),
            ft.Divider(color="#315149"),
            ft.Row([ft.CircleAvatar(content=text((self.state.user.get("nombre") or "P")[0], 14, True, "#DEF3EA"), bgcolor="#31594D", radius=18),
                    *([] if compact else [ft.Column([text(self.state.user.get("nombre", "Iniciar sesión"), 12, True, "white"),
                                                    text(self.state.user.get("rol", "Sin sesión"), 10, color="#9DB6B0")], spacing=2)])], spacing=10),
            *([] if self.state.demo or not self.state.user else [ft.TextButton("Salir", on_click=lambda e: self.logout())]),
        ], spacing=9, expand=True)

    def render(self):
        self.sidebar.content = self.build_sidebar()
        self.status.content = pill("DEMO · datos ficticios", "amber") if self.state.demo else pill(
            "API · base local" if self.state.sync.get("database_mode") == "local" else "API · nube", "blue")
        if not self.state.demo and not self.state.user:
            self.body.controls = [self.login_view()]
        else:
            if self.route.startswith("caja/"):
                view = cash_view(self)
            elif self.route == "carrito":
                view = cart_view(self)
            elif self.route == "inventario":
                view = inventory_view(self)
            elif self.route in {"clientes", "usuarios"}:
                view = people_view(self, self.route == "usuarios")
            elif self.route.startswith("reportes/"):
                view = reports_view(self)
            else:
                view = settings_view(self)
            crumbs = " / ".join(p.capitalize() if p != "settings" else "Configuración" for p in self.route.split("/"))
            self.body.controls = [text("Punto / " + crumbs, 11, color=MUTED),
                *([note("La venta se guardó, pero el catálogo no pudo actualizarse. Pulsa Actualizar antes de la siguiente venta.")] if self.catalog_stale else []), view]
        self.page.update()

    def dialog(self, title, content, actions):
        self.page.show_dialog(ft.AlertDialog(title=text(title, 22, True), content=content, actions=actions,
                                             actions_alignment=ft.MainAxisAlignment.END, modal=True))

    def notify(self, message, error=False):
        self.page.show_dialog(ft.SnackBar(content=text(message, 13, color="white"), bgcolor="#A93232" if error else GREEN))

    def login_view(self):
        email = ft.TextField(label="Correo", autofocus=True)
        password = ft.TextField(label="Contraseña", password=True, can_reveal_password=True)
        error = text("", 12, color=ft.Colors.ERROR)
        button = primary("Entrar al sistema", None, ft.Icons.LOGIN)

        async def login(e):
            button.disabled = True
            self.page.update()
            try:
                self.state.user = await self.api.login(email.value or "", password.value or "")
                await self.reload()
                self.render()
            except Exception as exc:
                self.state.user = {}
                error.value = str(exc)
                button.disabled = False
                self.page.update()

        button.on_click = login
        password.on_submit = login
        return ft.Container(card(ft.Column([
            text("Bienvenido a Punto", 28, True), text("Inicia sesión para consultar los datos de tu negocio.", 13, color=MUTED),
            email, password, error, button,
            note("La API configura si usa PostgreSQL local o en la nube. Las credenciales de la base de datos nunca se solicitan en la interfaz."),
        ], spacing=20), width=480), padding=ft.Padding.only(top=50))

    def logout(self):
        if self.pending_sale:
            self.notify("Hay un cobro sin confirmación. Reinténtalo con el mismo carrito antes de cerrar sesión.", error=True)
            return
        self.api.token = None
        self.state = AppState(mode="api", shift_open=False)
        self.route = "caja/inicio"
        self.render()

    async def refresh_data(self, e):
        if not self.state.user or self.state.demo:
            return
        try:
            await self.reload()
            self.catalog_stale = False
            self.render()
            self.notify("Datos actualizados")
        except ApiError as exc:
            self.notify(str(exc), error=True)

    async def reload(self):
        endpoints = {"products": "/api/products?limit=500", "categories": "/api/categories", "clients": "/api/clients",
                     "sales": "/api/sales", "methods": "/api/payment-methods", "sync": "/api/sync/status"}
        if self.state.user.get("rol") == "Administrador":
            endpoints["users"] = "/api/employees"
        results = await asyncio.gather(*[self.api.request("GET", path) for path in endpoints.values()])
        for key, result in zip(endpoints, results):
            setattr(self.state, key, result)

    def add_to_cart(self, product):
        if self.pending_sale:
            self.notify("Hay un cobro sin confirmación. Reintenta el mismo cobro antes de modificar el carrito.", error=True)
            return
        identifier = product["id_producto"]
        quantity = self.state.cart.get(identifier, Decimal(0)) + 1
        if quantity > Decimal(str(product["stock_actual"])):
            self.notify("No hay stock suficiente para añadir otra unidad", error=True)
            return
        self.state.cart[identifier] = quantity
        self.state.operation_id = str(uuid4())
        self.render()
        if self.route != "carrito":
            self.notify("Producto añadido al carrito")

    def set_quantity(self, identifier, value):
        if self.pending_sale:
            self.notify("No cambies las cantidades de un cobro sin confirmar.", error=True)
            return
        try:
            quantity = Decimal(value)
            product = next(p for p in self.state.products if p["id_producto"] == identifier)
            if not quantity.is_finite() or quantity <= 0 or quantity > Decimal(str(product["stock_actual"])) or quantity != quantity.quantize(Decimal("0.001")):
                raise ValueError
            self.state.cart[identifier] = quantity
            self.state.operation_id = str(uuid4())
            self.render()
        except (InvalidOperation, ValueError):
            self.notify("Cantidad inválida. Usa hasta 3 decimales sin superar el stock disponible.", error=True)

    def remove_from_cart(self, identifier):
        if self.pending_sale:
            self.notify("Reintenta el cobro pendiente antes de quitar productos.", error=True)
            return
        self.state.cart.pop(identifier, None)
        self.state.operation_id = str(uuid4())
        self.render()

    def empty_cart(self):
        if self.pending_sale:
            self.notify("Reintenta el cobro pendiente antes de vaciar el carrito.", error=True)
            return
        self.state.reset_cart()
        self.render()

    async def preview_inventory(self, data):
        if not self.state.demo:
            return await self.api.request("POST", "/api/inventory/preview", files={"file": ("inventario.xlsx", data)})
        result = (await asyncio.to_thread(parse_inventory, data)).json()
        categories = {c["nombre"] for c in self.state.categories}
        codes = {p.get("codigo_barras") for p in self.state.products if p.get("codigo_barras")}
        for row in result["rows"]:
            if row["categoria"] not in categories:
                result["errors"].append({"fila": row["fila"], "columna": "categoria", "mensaje": "La categoría no existe. Créala primero."})
            if row["codigo_barras"] and row["codigo_barras"] in codes:
                result["errors"].append({"fila": row["fila"], "columna": "codigo_barras", "mensaje": "El código ya está registrado."})
        result["valid"] = not result["errors"]
        return result

    async def confirm_inventory(self, data):
        if not self.state.demo:
            result = await self.api.request("POST", "/api/inventory/import", files={"file": ("inventario.xlsx", data)})
            if "errors" in result:
                raise ApiError("El archivo cambió de validez. Vuelve a cargarlo para revisar los errores.")
            await self.reload()
            return result
        result = await self.preview_inventory(data)
        if not result["valid"]:
            raise ValueError("Hay errores; revisa la vista previa. No se guardó ninguna fila.")
        for row in result["rows"]:
            values = dict(row)
            values.pop("fila")
            category = values.pop("categoria")
            values["id_categoria"] = next(c["id_categoria"] for c in self.state.categories if c["nombre"] == category)
            self.state.products.append({"id_producto": max([p["id_producto"] for p in self.state.products], default=0) + 1, **values})
        return {"imported": result["count"]}

    async def checkout(self, method_id):
        state = self.state
        if not state.cart:
            raise ValueError("El carrito está vacío")
        if state.demo:
            if not state.shift_open:
                raise ValueError("Abre la caja antes de cobrar")
            selected = [(next(p for p in state.products if p["id_producto"] == identifier), quantity) for identifier, quantity in state.cart.items()]
            if any(Decimal(str(p["stock_actual"])) < q for p, q in selected):
                raise ValueError("Stock insuficiente. Revisa las cantidades.")
            result = {"id_venta": max([s["id_venta"] for s in state.sales], default=0) + 1,
                      "id_cliente": state.cart_client, "id_empleado": 1, "id_metodo_pago": method_id,
                      "fecha_hora": datetime.now().isoformat(), "total": str(state.total), "estado": "Completada"}
            for p, quantity in selected:
                p["stock_actual"] = str(Decimal(str(p["stock_actual"])) - quantity)
            state.sales.append(result)
            state.reset_cart()
            return result
        if self.catalog_stale:
            raise ValueError("Actualiza el catálogo antes de cobrar una nueva venta")
        if self.pending_sale is None:
            self.pending_sale = {"operation_id": state.operation_id,
                "id_cliente": state.cart_client, "id_metodo_pago": method_id,
                "items": [{"id_producto": identifier, "cantidad": str(quantity)} for identifier, quantity in state.cart.items()]}
        try:
            result = await self.api.request("POST", "/api/sales", json=self.pending_sale)
        except ApiError as exc:
            if exc.status_code in {401, 403, 409, 422}:
                self.pending_sale = None
            raise
        self.pending_sale = None
        # La venta ya fue confirmada: un fallo posterior al refrescar no debe permitir cobrar otra vez.
        state.reset_cart()
        try:
            await self.reload()
        except ApiError:
            self.catalog_stale = True
        return result
