import asyncio
from decimal import Decimal

import pytest
from pydantic import ValidationError

from frontend.src.services.printer_service import PrinterService
from shared.people import ClientInput, EmployeeCreate, EmployeeUpdate, PasswordChange
from shared.receipts import receipt_lines, receipt_pdf


def test_people_contracts_normalize_email_and_keep_password_whitespace():
    employee = EmployeeCreate(
        nombre=" Ana ",
        apellido=" Prueba ",
        correo="ANA@EJEMPLO.LOCAL",
        password="  clave segura  ",
        rol="Cajero",
    )
    assert employee.nombre == "Ana" and employee.correo == "ana@ejemplo.local"
    assert employee.password == "  clave segura  "
    assert (
        EmployeeUpdate(
            nombre="Ana", apellido="Prueba", correo="ana@ejemplo.local", rol="Cajero"
        ).password
        is None
    )
    assert ClientInput(nombre="Persona", correo="   ").correo is None

    with pytest.raises(ValidationError):
        EmployeeCreate(
            nombre="Ana",
            apellido="Prueba",
            correo="ana@ejemplo.local",
            password="á" * 37,
            rol="Cajero",
        )

    with pytest.raises(ValidationError):
        PasswordChange(current_password="actual", new_password="corta")


def sample_sale():
    return {
        "id_venta": 1,
        "fecha_hora": "2026-11-16T10:00:00",
        "estado": "Completada",
        "total": "15.00",
        "impuesto": "2.07",
        "empleado": "Ana",
        "metodo_pago": "Efectivo",
        "items": [
            {
                "nombre": "Agua\x1b@\n" + "nombre extenso " * 8,
                "cantidad": "1.250",
                "precio_unitario_venta": "12.00",
                "subtotal": "15.00",
            }
        ],
    }


def test_receipt_formats_amounts_wraps_names_and_emits_pdf():
    sale = sample_sale()
    lines = receipt_lines(sale)
    assert all(len(line) <= 36 and "\x1b" not in line for line in lines)
    assert "Subtotal: $12.93" in lines
    assert "TOTAL: $15.00" in lines
    assert receipt_pdf(sale).startswith(b"%PDF-")
    sale["estado"] = "Cancelada"
    assert "VENTA CANCELADA" in receipt_lines(sale)


def test_printer_settings_persist_and_network_adapter_closes_device(
    tmp_path, monkeypatch
):
    printer_module = pytest.importorskip("escpos.printer")
    calls = []

    class FakePrinter:
        def __init__(self, host, **kwargs):
            calls.append((host, kwargs))

        def text(self, value):
            calls.append(value)

        def cut(self):
            calls.append("cut")

        def close(self):
            calls.append("close")

    monkeypatch.setattr(printer_module, "Network", FakePrinter)
    path = tmp_path / "preferences.json"
    service = PrinterService(path)
    service.save(
        config={"connection": "Red / Ethernet", "address": "127.0.0.1", "port": 9100},
        theme="dark",
    )
    restored = PrinterService(path)
    assert restored.theme == "dark"
    asyncio.run(restored.print_sale(sample_sale(), "Tienda"))
    assert calls[0][0] == "127.0.0.1" and calls[0][1]["port"] == 9100
    assert calls[-2:] == ["cut", "close"]


def test_demo_sale_can_be_cancelled_once_and_downloaded_as_pdf():
    pytest.importorskip("flet")
    from test_frontend import Page

    from frontend.src.app import PosApp

    async def scenario():
        app = PosApp(Page())
        product = app.state.products[0]
        before = Decimal(str(product["stock_actual"]))
        app.add_to_cart(product)
        result = await app.checkout(1)
        identifier = result["id_venta"]
        assert (await app.sales.pdf(identifier)).startswith(b"%PDF-")

        for _ in range(2):
            await app.sales.cancel(
                identifier,
                {
                    "motivo": "Prueba",
                    "operation_id": "00000000-0000-0000-0000-000000000001",
                },
            )

        assert Decimal(str(product["stock_actual"])) == before
        assert (await app.sales.detail(identifier))["estado"] == "Cancelada"
        await app.close_cash(
            {
                "operation_id": "00000000-0000-0000-0000-000000000002",
                "efectivo_contado": str(app.cash_expected),
            }
        )
        assert not app.state.shift_open
        await app.open_cash(
            {
                "operation_id": "00000000-0000-0000-0000-000000000003",
                "fondo_inicial": "50",
            }
        )
        assert app.state.shift_open and app.state.opening_cash == 50

    asyncio.run(scenario())
