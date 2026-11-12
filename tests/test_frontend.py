import asyncio
from decimal import Decimal
from types import SimpleNamespace

import pytest

ft = pytest.importorskip("flet")

from frontend.src.app import PosApp
from frontend.src.views.inventory_view import category_dialog, import_dialog, product_dialog
from frontend.src.views.people_view import person_dialog
from frontend.src.views.pos_view import checkout_dialog
from frontend.src.services.api_client import ApiError
from test_inventory_excel import row, workbook


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
    person_dialog(app, True)
    person_dialog(app, False)
    app.page.width = 980
    app.render()
    assert app.sidebar.width == 80


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
