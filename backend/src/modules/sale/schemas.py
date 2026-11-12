from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

Quantity = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=3)]
Money = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]


class SaleLine(BaseModel):
    id_producto: int = Field(gt=0)
    cantidad: Quantity


class SaleInput(BaseModel):
    operation_id: UUID
    id_cliente: int | None = Field(default=None, gt=0)
    id_metodo_pago: int = Field(gt=0)
    items: list[SaleLine] = Field(min_length=1, max_length=500)


class FrozenLine(BaseModel):
    product_sync_id: UUID
    cantidad: Quantity
    precio_unitario_venta: Money


class SaleSnapshot(BaseModel):
    sync_id: UUID
    employee_sync_id: UUID
    client_sync_id: UUID | None = None
    payment_method: str
    fecha_hora: str
    items: list[FrozenLine] = Field(min_length=1, max_length=500)
