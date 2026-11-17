"""Contrato de ajustes compartido con el escritorio."""

from decimal import Decimal

from shared.catalog import StockAdjustmentInput

__all__ = ["StockAdjustmentInput", "stock_adjustment_response"]


STOCK_ADJUSTMENT_FIELDS = (
    "operation_id",
    "id_producto",
    "id_empleado",
    "cantidad",
    "stock_anterior",
    "stock_nuevo",
    "motivo",
    "fecha_hora",
)


def stock_adjustment_response(adjustment):
    values = {field: getattr(adjustment, field) for field in STOCK_ADJUSTMENT_FIELDS}

    return {
        field: str(value) if isinstance(value, Decimal) else value
        for field, value in values.items()
    }
