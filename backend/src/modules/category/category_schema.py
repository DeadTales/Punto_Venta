from uuid import UUID

from pydantic import BaseModel, ConfigDict

from shared.catalog import CategoryInput

__all__ = ["CategoryInput", "CategoryResponse"]


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_categoria: int
    sync_id: UUID
    nombre: str
    descripcion: str | None
