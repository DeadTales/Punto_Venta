import asyncio
from decimal import Decimal
from types import SimpleNamespace

import pytest

ft = pytest.importorskip("flet")

from test_inventory_excel import row, workbook

from frontend.src.app import PosApp
from frontend.src.services.api_client import ApiError
from frontend.src.views.inventory_adjust_view import adjustment_dialog
from frontend.src.views.inventory_view import (
    category_dialog,
    import_dialog,
    product_dialog,
)
from frontend.src.views.people_view import person_dialog
from frontend.src.views.pos_view import checkout_dialog


class Page:
    def __init__(self):
        self.services = []
        self.window = SimpleNamespace()
        self.width = 1440
        self.controls = []
        self.dialogs = []

    def add(self, control):
        self.controls.append(control)

    def update(self):
        pass

    def show_dialog(self, dialog):
        self.dialogs.append(dialog)

    def pop_dialog(self):
        return self.dialogs.pop()


def test_all_views_and_dialogs_construct_with_installed_flet():
    app = PosApp(Page())

    for route, _, _ in app.routes:
        app.navigate(route)
        assert app.body.controls

    for dialog in [category_dialog, import_dialog, product_dialog, checkout_dialog]:
        dialog(app)

    product_dialog(app, app.state.products[0])
    category_dialog(app, app.state.categories[0])
    adjustment_dialog(app, app.state.products[0])
    person_dialog(app, True)
    person_dialog(app, False)
    app.page.width = 980
    app.render()
    assert app.sidebar.width == 80


def test_back_arrow_returns_to_previous_views_without_repeating_current_route():
    app = PosApp(Page())
    assert not app.body.controls[0].controls[0].visible
    app.go_back()
    assert app.route == "caja/inicio"

    app.navigate("inventario")
    app.navigate("inventario/categorias")
    app.navigate("inventario/categorias")
    app.render()
    app.navigate("settings/aspectos")

    for expected in ["inventario/categorias", "inventario", "caja/inicio"]:
        back_button = app.body.controls[0].controls[0]
        assert back_button.visible
        assert back_button.icon == ft.Icons.ARROW_BACK
        back_button.on_click(None)
        assert app.route == expected

    assert not app.navigation_history
    assert not app.body.controls[0].controls[0].visible


def test_rejected_navigation_does_not_change_back_history():
    app = PosApp(Page())
    app.state.mode = "api"
    app.state.user["rol"] = "Cajero"
    app.navigate("inventario")

    for route in ["usuarios", "reportes/usuarios", "ruta-inexistente"]:
        app.navigate(route)
        assert app.route == "inventario"
        assert app.navigation_history == ["caja/inicio"]

    app.go_back()
    assert app.route == "caja/inicio"
    assert not app.navigation_history


def test_ticket_history_paginates_and_filters_by_ticket_client_and_dates():
    app = PosApp(Page())
    template = app.state.sales[0]
    client = app.state.clients[0]
    app.state.sales = [
        {
            **template,
            "id_venta": identifier,
            "id_cliente": client["id_cliente"],
            "fecha_hora": "2026-11-16T12:00:00",
        }
        for identifier in range(1, 26)
    ]
    app.navigate("ventas")
    filters, host, footer = app.body.controls[-1].controls[1].content.controls
    search, start, end, submit = filters.controls

    assert len(host.content.controls[0].rows) == 20
    footer.controls[-1].on_click(None)
    assert len(host.content.controls[0].rows) == 5

    search.value = "25"
    search.on_change(SimpleNamespace())
    assert len(host.content.controls[0].rows) == 1
    assert host.content.controls[0].rows[0].cells[0].content.value == "#25"
    assert footer.controls[0].disabled

    search.value = client["nombre"]
    start.value = end.value = "2026-11-16"
    submit.on_click(SimpleNamespace())
    assert len(host.content.controls[0].rows) == 20

    start.value = "fecha-invalida"
    submit.on_click(SimpleNamespace())
    assert isinstance(host.content, ft.Text)
    assert "Revisa las fechas" in host.content.value

    start.value = end.value = "2026-11-17"
    submit.on_click(SimpleNamespace())
    assert "No hay registros" in host.content.content.controls[1].value


def test_demo_import_and_sale_update_only_in_memory():
    async def scenario():
        app = PosApp(Page())
        count = len(app.state.products)
        data = workbook([row()])
        assert (await app.preview_inventory(data))["valid"]
        assert (await app.confirm_inventory(data))["imported"] == 1
        assert len(app.state.products) == count + 1
        assert not (await app.preview_inventory(data))["valid"]
        product = app.state.products[-1]
        app.add_to_cart(product)
        app.set_quantity(product["id_producto"], "1.250")
        assert app.state.total == Decimal("15.00")
        result = await app.checkout(1)
        assert result["total"] == "15.00"
        assert product["stock_actual"] == "23.500"
        assert not app.state.cart
        assert app.api is None

    asyncio.run(scenario())


def test_demo_catalog_crud_barcode_and_adjustment_retry():
    async def scenario():
        app = PosApp(Page())
        service = app.products
        category = await service.save_category(
            {"nombre": " Nuevos ", "descripcion": "Prueba"}
        )

        with pytest.raises(ValueError, match="Ya existe"):
            await service.save_category({"nombre": "nuevos"})

        product = await service.save_product(
            {
                "id_categoria": category["id_categoria"],
                "codigo_barras": "00000001",
                "nombre": "Producto nuevo",
                "precio_compra": "2.50",
                "precio_venta": "5",
                "stock_actual": "1.250",
            }
        )
        assert (await service.barcode("00000001"))["id_producto"] == product[
            "id_producto"
        ]

        with pytest.raises(ValueError, match="contiene productos"):
            await service.delete("categories", category["id_categoria"])

        update = {
            key: product[key]
            for key in (
                "id_categoria",
                "codigo_barras",
                "nombre",
                "precio_compra",
                "precio_venta",
                "stock_minimo",
            )
        }
        update["nombre"] = "Editado"
        await service.save_product(update, product["id_producto"])
        assert product["nombre"] == "Editado" and product["stock_actual"] == "1.250"
        body = {
            "operation_id": "00000000-0000-0000-0000-000000000001",
            "cantidad": "-0.250",
            "motivo": "Merma",
        }

        for _ in range(2):
            assert (await service.adjust_stock(product["id_producto"], body))[
                "stock_nuevo"
            ] == "1.000"

        assert product["stock_actual"] == "1.000"

        with pytest.raises(ValueError, match="otros datos"):
            await service.adjust_stock(
                product["id_producto"], {**body, "cantidad": "1"}
            )

        with pytest.raises(ValueError, match="historial"):
            await service.delete("products", product["id_producto"])

        temporary = await service.save_product({**update, "codigo_barras": None})
        await service.delete("products", temporary["id_producto"])
        assert temporary not in app.state.products
        assert app.api is None

    asyncio.run(scenario())


def test_api_catalog_loads_all_pages_and_cashier_cannot_write():
    async def scenario():
        app = PosApp(Page())
        pages = []

        class Client:
            async def request(self, method, path, **kwargs):
                pages.append(kwargs["params"]["offset"])

                return (
                    [{"id_producto": i} for i in range(500)]
                    if len(pages) == 1
                    else [{"id_producto": 501}]
                )

        app.api = Client()
        assert len(await app.products.all_products()) == 501
        assert pages == [0, 500]
        app.state.mode = "api"
        app.state.user["rol"] = "Cajero"

        with pytest.raises(ValueError, match="Administrador o Supervisor"):
            await app.products.delete("products", 1)

    asyncio.run(scenario())


def test_confirmed_catalog_write_is_not_retried_when_refresh_fails():
    async def scenario():
        app = PosApp(Page())
        app.state.mode = "api"

        async def reload():
            raise ApiError("Sin conexión")

        app.reload = reload
        await app.products.refresh_after_write()
        assert app.catalog_stale

    asyncio.run(scenario())


def test_adjustment_dialog_preserves_operation_after_lost_confirmation():
    async def scenario():
        app = PosApp(Page())
        calls = []

        async def adjust(identifier, values):
            calls.append(dict(values))

            if len(calls) == 1:
                raise ApiError("Confirmación perdida")

            return {"stock_nuevo": "49.250"}

        app.products.adjust_stock = adjust
        adjustment_dialog(app, app.state.products[0])
        dialog = app.page.dialogs[-1]
        quantity, reason = dialog.content.controls[2:4]
        cancel, submit = dialog.actions
        quantity.value, reason.value = "1.250", "Recepción"
        await submit.on_click(None)
        assert quantity.disabled and reason.disabled and cancel.disabled
        assert not submit.disabled
        await submit.on_click(None)
        assert len(calls) == 2 and calls[0] == calls[1]

    asyncio.run(scenario())


def test_logout_clears_expired_credentials_when_api_rejects_the_token():
    async def scenario():
        app = PosApp(Page())

        class ExpiredClient:
            token = "expired-token"

            async def request(self, method, path, **kwargs):
                raise ApiError("La sesión expiró", 401)

        app.api = ExpiredClient()
        app.state.mode = "api"
        app.navigate("clientes")
        assert app.navigation_history
        await app.logout()

        assert app.api.token is None
        assert app.state.user == {}
        assert not app.state.shift_open
        assert not app.navigation_history
        assert app.route == "caja/inicio"
        app.navigate("inventario")
        assert app.route == "caja/inicio"
        assert not app.navigation_history

    asyncio.run(scenario())


def test_rounding_matches_backend_per_line_half_up():
    app = PosApp(Page())
    p = app.state.products[0]
    p["precio_venta"] = "0.01"
    app.state.cart[p["id_producto"]] = Decimal("0.500")
    assert app.state.total == Decimal("0.01")


def test_uncertain_sale_keeps_same_payload_and_blocks_cart_changes():
    async def scenario():
        app = PosApp(Page())
        product = app.state.products[0]
        app.add_to_cart(product)
        app.state.mode = "api"
        calls = []

        class Client:
            async def request(self, method, path, **kwargs):
                calls.append(dict(kwargs["json"]))

                if len(calls) == 1:
                    raise ApiError("Confirmación perdida")

                return {"id_venta": 99, "total": "12.00"}

        async def reload():
            pass

        app.api = Client()
        app.reload = reload

        with pytest.raises(ApiError):
            await app.checkout(1)

        app.add_to_cart(product)
        app.empty_cart()
        app.set_quantity(product["id_producto"], "2")
        assert app.state.cart[product["id_producto"]] == 1
        assert app.pending_sale is not None
        assert (await app.checkout(2))["id_venta"] == 99
        assert calls[0] == calls[1]
        assert not app.pending_sale and not app.state.cart

    asyncio.run(scenario())
