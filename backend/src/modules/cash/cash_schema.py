from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from shared.catalog import Price


class OpenShiftInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID
    fondo_inicial: Price


class CloseShiftInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    operation_id: UUID
    efectivo_contado: Price
    notas: str | None = Field(default=None, max_length=500)
