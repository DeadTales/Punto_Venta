"""Validaciones del catálogo compartidas por API y escritorio (sin ORM)."""

from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Name = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)
]
Price = Annotated[
    Decimal, Field(ge=0, max_digits=10, decimal_places=2, allow_inf_nan=False)
]
Stock = Annotated[
    Decimal, Field(ge=0, max_digits=10, decimal_places=3, allow_inf_nan=False)
]


class CatalogInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CategoryInput(CatalogInput):
    nombre: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    descripcion: str | None = None


class ProductUpdate(CatalogInput):
    """PUT reemplaza los datos del artículo; el stock cambia mediante ajustes."""

    id_categoria: int = Field(gt=0)
    codigo_barras: str | None = Field(default=None, max_length=50)
    nombre: Name
    descripcion: str | None = None

    precio_compra: Price
    precio_venta: Price

    stock_minimo: Stock = Decimal(0)

    @field_validator("codigo_barras", "descripcion")
    @classmethod
    def empty_to_none(cls, value):
        return value or None


class ProductCreate(ProductUpdate):
    stock_actual: Stock = Decimal(0)


class StockAdjustmentInput(CatalogInput):
    operation_id: UUID
    cantidad: Annotated[
        Decimal, Field(max_digits=10, decimal_places=3, allow_inf_nan=False)
    ]
    motivo: Annotated[str, StringConstraints(min_length=1, max_length=250)]

    @field_validator("cantidad")
    @classmethod
    def nonzero(cls, value):
        if value == 0:
            raise ValueError("La cantidad del ajuste debe ser distinta de cero")

        return value


def profit_margin(cost, price):
    """Porcentaje de margen sobre venta; sin porcentaje para precio cero."""

    cost = Decimal(str(cost))
    price = Decimal(str(price))

    if price == 0:
        return None

    margin = (price - cost) * 100 / price

    return margin.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def adjusted_stock(current, delta):
    result = Decimal(str(current)) + Decimal(str(delta))

    if not 0 <= result <= Decimal("9999999.999"):
        raise ValueError(
            "El ajuste dejaría existencias negativas o superaría 9999999.999"
        )

    return result


def validation_message(errors):
    """Mensajes de formulario sin representaciones internas de Pydantic."""

    labels = {
        "nombre": "Nombre",
        "id_categoria": "Categoría",
        "codigo_barras": "Código de barras",
        "precio_compra": "Costo",
        "precio_venta": "Precio",
        "stock_actual": "Existencia",
        "stock_minimo": "Stock mínimo",
        "cantidad": "Cantidad",
        "motivo": "Motivo",
    }
    messages = []

    for error in errors[:8]:
        field = str(error.get("loc", ["campo"])[-1])
        code = error.get("type", "")
        context = error.get("ctx", {})

        if code in {"missing", "string_too_short"}:
            message = "Completa este campo."
        elif code == "string_too_long":
            message = f"Usa hasta {context.get('max_length')} caracteres."
        elif code == "extra_forbidden" and field == "stock_actual":
            message = "Para cambiar existencias registra un ajuste."
        elif code == "decimal_max_places":
            message = f"Usa hasta {context.get('decimal_places')} decimales."
        elif code in {"decimal_max_digits", "decimal_whole_digits"}:
            message = "El importe supera el límite permitido."
        elif code == "value_error" and field == "cantidad":
            message = "La cantidad debe ser distinta de cero."
        else:
            message = "Escribe un valor válido dentro del rango permitido."

        messages.append(f"{labels.get(field, field)}: {message}")

    return "\n".join(messages)
