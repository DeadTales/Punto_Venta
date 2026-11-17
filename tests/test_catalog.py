from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from shared.catalog import (
    CategoryInput,
    ProductCreate,
    ProductUpdate,
    StockAdjustmentInput,
    adjusted_stock,
    profit_margin,
)


def product_values(**changes):
    return {
        "id_categoria": 1,
        "codigo_barras": "001234",
        "nombre": "Agua",
        "descripcion": None,
        "precio_compra": "6.50",
        "precio_venta": "12.00",
        "stock_actual": "24.750",
        "stock_minimo": "5",
        **changes,
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("nombre", "   "),
        ("nombre", "x" * 151),
        ("id_categoria", 0),
        ("codigo_barras", "1" * 51),
        ("precio_compra", "-0.01"),
        ("precio_venta", "1.001"),
        ("precio_venta", "NaN"),
        ("precio_venta", "100000000"),
        ("stock_actual", "0.0001"),
        ("stock_minimo", "-1"),
        ("stock_actual", "10000000"),
        ("stock_actual", "Infinity"),
    ],
)
def test_product_rejects_values_outside_database_contract(field, value):
    with pytest.raises(ValidationError):
        ProductCreate.model_validate(product_values(**{field: value}))


def test_catalog_normalizes_text_preserves_barcodes_and_allows_negative_margin():
    body = ProductCreate.model_validate(
        product_values(nombre=" Agua ", codigo_barras=" 001234 ")
    )
    assert body.nombre == "Agua" and body.codigo_barras == "001234"
    assert body.stock_actual == Decimal("24.750")
    assert (
        ProductCreate.model_validate(product_values(codigo_barras=" ")).codigo_barras
        is None
    )
    assert profit_margin("6.50", "12") == Decimal("45.83")
    assert profit_margin("12", "6") == Decimal("-100.00")
    assert profit_margin("6", "0") is None

    with pytest.raises(ValidationError):
        CategoryInput(nombre="   ")


def test_edit_cannot_change_stock_without_an_audited_adjustment():
    with pytest.raises(ValidationError):
        ProductUpdate.model_validate(product_values())


@pytest.mark.parametrize(
    "quantity", ["0", "0.000", "0.0001", "NaN", "Infinity", "10000000"]
)
def test_adjustment_requires_nonzero_finite_quantity_with_three_decimals(quantity):
    with pytest.raises(ValidationError):
        StockAdjustmentInput(operation_id=uuid4(), cantidad=quantity, motivo="Entrada")


def test_adjustments_handle_fractional_stock_and_reject_underflow_and_overflow():
    assert adjusted_stock("1.250", "-0.250") == Decimal("1.000")

    for current, delta in [("1", "-1.001"), ("9999999.999", "0.001")]:
        with pytest.raises(ValueError):
            adjusted_stock(current, delta)
