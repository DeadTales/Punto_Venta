from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .schemas import SaleInput, SaleSnapshot

__all__ = ["SaleInput", "SaleSnapshot", "CancelSaleInput"]


class CancelSaleInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    operation_id: UUID
    motivo: str = Field(min_length=1, max_length=250)
