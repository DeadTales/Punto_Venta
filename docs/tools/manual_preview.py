"""Renderiza escenas de documentación sin conectar con la API ni imprimir."""

from decimal import Decimal
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import flet as ft
from fastapi import HTTPException
from fastapi.routing import APIRoute
from openpyxl import load_workbook

from frontend.src.app import PosApp
from frontend.src.models.demo import demo_state
from frontend.src.services.printer_service import PrinterService
from frontend.src.views.cash_view import cash_dialog
from frontend.src.views.inventory_adjust_view import adjustment_dialog
from frontend.src.views.inventory_view import (
    category_dialog,
    delete_dialog,
    import_dialog,
    product_dialog,
)
from frontend.src.views.people_dialogs import delete_person_dialog, person_dialog
from frontend.src.views.pos_view import checkout_dialog
from frontend.src.views.sales_view import cancel_sale_dialog, sale_dialog
from shared.inventory_excel import template_bytes

ROOT = Path(__file__).resolve().parents[2]
SESSION = {}
ROUTES = {
    "inicio": "caja/inicio",
    "login": "caja/inicio",
    "caja_cerrada": "caja/corte",
    "abrir_caja": "caja/corte",
    "carrito": "carrito",
    "cobrar": "carrito",
    "tickets": "ventas",
    "ticket": "ventas",
    "cancelar_venta": "ventas",
    "clientes": "clientes",
    "cliente_formulario": "clientes",
    "inventario": "inventario",
    "producto_formulario": "inventario",
    "categorias": "inventario/categorias",
    "categoria_formulario": "inventario/categorias",
    "ajustes": "inventario/ajustes",
    "ajuste_formulario": "inventario/ajustes",
    "eliminar_producto": "inventario",
    "importar": "inventario",
    "importar_validado": "inventario",
    "corte": "caja/corte",
    "cerrar_caja": "caja/corte",
    "usuarios": "usuarios",
    "usuario_formulario": "usuarios",
    "desactivar_usuario": "usuarios",
    "reporte_ventas": "reportes/ventas",
    "reporte_predicciones": "reportes/predicciones",
    "perifericos": "settings/perifericos",
    "perifericos_serial": "settings/perifericos",
    "perifericos_red": "settings/perifericos",
    "aspectos": "settings/aspectos",
    "contrasena": "settings/contraseña",
    "correo": "settings/correo",
    "buscar_vista": "caja/inicio",
    "sesion": "caja/inicio",
    "inventario_pie": "inventario",
    "reporte_tabla": "reportes/ventas",
}


def prepare_state(controller):
    controller.state = demo_state()
    state = controller.state
    state.user.update(id_empleado=1, activo=True)
    state.opening_cash = Decimal("500.00")
    state.cart = {1: Decimal("2"), 3: Decimal("1")}
    state.cart_client = 1
    state.shift_history = [
        {
            "id_turno": 12,
            "apertura": "2026-11-15T09:00:00",
            "estado": "Cerrado",
            "efectivo_esperado": "1250.00",
            "efectivo_contado": "1240.00",
            "diferencia": "-10.00",
        }
    ]
    sale = {
        "id_venta": 1008,
        "fecha_hora": state.sales[-1]["fecha_hora"],
        "id_cliente": 1,
        "id_empleado": 1,
        "id_metodo_pago": 1,
        "total": "50.50",
        "subtotal": "50.50",
        "impuesto": "0.00",
        "estado": "Completada",
    }
    state.sales.append(sale)
    state.sale_details[1008] = {
        **sale,
        "items": [
            {
                "id_producto": 1,
                "nombre": state.products[0]["nombre"],
                "cantidad": "2",
                "precio_unitario_venta": "12.00",
                "subtotal": "24.00",
            },
            {
                "id_producto": 3,
                "nombre": state.products[2]["nombre"],
                "cantidad": "1",
                "precio_unitario_venta": "26.50",
                "subtotal": "26.50",
            },
        ],
    }
    controller.printer = PrinterService(ROOT / ".venv-codex/manual-settings.json")
    controller.printer.config.update(vendor_id="0x04b8", product_id="0x0202")
    controller.state.theme = "light"
    controller.page.theme_mode = ft.ThemeMode.LIGHT
    controller.pending_sale = None
    controller.filters = {}
    controller.catalog_stale = False
    controller.global_search.value = ""
    controller.picker = SESSION["picker"]


async def main(page):
    controller = PosApp(page, mode="demo")
    SESSION.update(controller=controller, picker=controller.picker, dialog=False)
    prepare_state(controller)
    controller.render()
    page.data = controller


async def ready():
    return {"ready": "controller" in SESSION}


async def show_import_preview(controller):
    workbook = load_workbook(BytesIO(template_bytes()))
    workbook["Inventario"].append(
        [
            "7509990000012",
            "Té de manzanilla",
            "Bebidas",
            "Caja de 20 sobres",
            18,
            30,
            24,
            6,
        ]
    )
    target = ROOT / ".venv-codex/inventario_manual.xlsx"
    workbook.save(target)

    async def pick_files(**kwargs):
        return [SimpleNamespace(path=str(target), name=target.name)]

    controller.picker = SimpleNamespace(pick_files=pick_files)
    import_dialog(controller)
    dialog = controller.page._dialogs.controls[-1]
    button = dialog.content.controls[3].controls[1]
    await button.on_click(None)


async def scene(name: str):
    if name not in ROUTES or "controller" not in SESSION:
        raise HTTPException(404, "Escena no disponible")

    controller = SESSION["controller"]

    if SESSION["dialog"]:
        controller.page.pop_dialog()
        SESSION["dialog"] = False

    prepare_state(controller)
    controller.route = ROUTES[name]
    controller.navigation_history = ["caja/inicio"] if name != "inicio" else []

    if name == "login":
        controller.state.mode = "api"
        controller.state.user = {}
        controller.state.cart = {}
        controller.navigation_history = []

    if name == "sesion":
        controller.state.mode = "api"

    if name == "perifericos_serial":
        controller.printer.config.update(connection="Serial / COM", address="COM3")
    elif name == "perifericos_red":
        controller.printer.config.update(
            connection="Red / Ethernet", address="192.0.2.25"
        )

    if name in {"caja_cerrada", "abrir_caja"}:
        controller.state.shift_open = False
        controller.state.opening_cash = Decimal(0)

    header = controller.root.controls[1].content.controls[0]
    header.controls[2].visible = not controller.state.demo
    controller.render()

    dialogs = {
        "abrir_caja": lambda: cash_dialog(controller),
        "cerrar_caja": lambda: cash_dialog(controller, closing=True),
        "cobrar": lambda: checkout_dialog(controller),
        "cliente_formulario": lambda: person_dialog(controller, False),
        "usuario_formulario": lambda: person_dialog(controller, True),
        "producto_formulario": lambda: product_dialog(controller),
        "categoria_formulario": lambda: category_dialog(controller),
        "ajuste_formulario": lambda: adjustment_dialog(
            controller, controller.state.products[0]
        ),
        "eliminar_producto": lambda: delete_dialog(
            controller, "products", controller.state.products[0]
        ),
        "importar": lambda: import_dialog(controller),
        "desactivar_usuario": lambda: delete_person_dialog(
            controller, True, controller.state.users[1]
        ),
        "cancelar_venta": lambda: cancel_sale_dialog(
            controller, controller.state.sale_details[1008]
        ),
    }

    if name in dialogs:
        dialogs[name]()
        SESSION["dialog"] = True
    elif name == "ticket":
        await sale_dialog(controller, 1008)
        SESSION["dialog"] = True
    elif name == "importar_validado":
        await show_import_preview(controller)
        SESSION["dialog"] = True
    elif name == "buscar_vista":
        controller.global_search.value = "inventario"
        controller.search_route(None)
        SESSION["dialog"] = True

    controller.page.update()

    if name in {"inventario_pie", "reporte_tabla"}:
        await controller.body.scroll_to(offset=-1, duration=0)

    return {"scene": name, "route": controller.route, "fixture": True}


app = ft.run(main, export_asgi_app=True, no_cdn=True)
app.router.routes.insert(0, APIRoute("/__manual/ready", ready, methods=["GET"]))
app.router.routes.insert(0, APIRoute("/__manual/scene/{name}", scene, methods=["POST"]))
