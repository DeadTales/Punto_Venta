"""Validación de los cambios de catálogo intercambiados entre APIs."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, model_validator

from shared.catalog import ProductCreate


class CatalogChangeInput(BaseModel):
    entity: Literal["category", "product"]
    sync_id: UUID
    before: dict | None
    after: dict | None

    @model_validator(mode="after")
    def validate_snapshots(self):
        if self.before is None and self.after is None:
            raise ValueError("El evento debe incluir un estado anterior o posterior")

        if self.entity == "category":
            expected_fields = {"nombre", "descripcion"}
        else:
            expected_fields = set(ProductCreate.model_fields) - {"id_categoria"}
            expected_fields.add("category_sync_id")

        for snapshot in (self.before, self.after):
            if snapshot is not None and set(snapshot) != expected_fields:
                raise ValueError(
                    "Los campos de la instantánea no corresponden al catálogo"
                )

        return self
