from decimal import Decimal
from uuid import UUID

from pydantic import ConfigDict, computed_field

from shared.catalog import ProductCreate, ProductUpdate, profit_margin

__all__ = ["ProductCreate", "ProductUpdate", "ProductResponse"]


class ProductResponse(ProductCreate):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    id_producto: int
    sync_id: UUID

    @computed_field
    @property
    def margen_ganancia(self) -> Decimal | None:
        return profit_margin(self.precio_compra, self.precio_venta)
