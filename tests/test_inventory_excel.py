from io import BytesIO

from openpyxl import Workbook, load_workbook
import pytest

from shared.inventory_excel import HEADERS, parse_inventory, template_bytes


def workbook(rows):
    wb = Workbook()
    wb.active.title = "Inventario"
    wb.active.append(HEADERS)
    for row in rows:
        wb.active.append(row)
    data = BytesIO()
    wb.save(data)
    return data.getvalue()


def row(**changes):
    return [changes.get(k, v) for k, v in zip(HEADERS, ["001234", "Agua", "General", None, "6.50", "12.00", "24.750", "5"])]


def test_template_has_separate_example_and_blank_import_sheet():
    wb = load_workbook(BytesIO(template_bytes()))
    assert wb["Inventario"]["A2"].number_format == "@"
    assert "Instrucciones" in wb.sheetnames
    assert parse_inventory(template_bytes()).errors


def test_preserves_barcode_and_decimal_quantities():
    preview = parse_inventory(workbook([row()]))
    assert not preview.errors
    assert preview.rows[0].codigo_barras == "001234"
    assert str(preview.rows[0].stock_actual) == "24.750"


@pytest.mark.parametrize("changes", [
    {"codigo_barras": 1234}, {"nombre": ""}, {"precio_venta": "=2+2"},
    {"precio_compra": "-1"}, {"precio_venta": "1.001"}, {"stock_actual": "0.0001"},
    {"stock_actual": "NaN"}, {"stock_actual": "Infinity"}, {"stock_actual": None},
    {"precio_venta": "100000000"}, {"stock_actual": "10000000"},
])
def test_rejects_invalid_cells(changes):
    result = parse_inventory(workbook([row(**changes)]))
    assert result.errors and result.errors[0]["fila"] == 2


def test_duplicate_codes_are_not_silently_merged():
    result = parse_inventory(workbook([row(), row(nombre="Otro producto")]))
    assert any("repetido" in e["mensaje"] for e in result.errors)


def test_invalid_file_and_renamed_headers():
    assert parse_inventory(b"not an excel file").errors
    wb = load_workbook(BytesIO(workbook([row()])))
    wb.active["A1"] = "barcode"
    output = BytesIO()
    wb.save(output)
    assert parse_inventory(output.getvalue()).errors
