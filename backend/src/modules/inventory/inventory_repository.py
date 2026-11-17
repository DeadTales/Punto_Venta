"""Lecturas del historial de ajustes de existencias."""

from sqlalchemy import select

from ...core.repository import Repository
from .inventory_model import StockAdjustment


class InventoryRepository(Repository):
    def __init__(self, session):
        super().__init__(session, StockAdjustment)

    async def list_adjustments(self, product_id, limit=100, offset=0):
        statement = (
            select(StockAdjustment)
            .where(StockAdjustment.id_producto == product_id)
            .order_by(StockAdjustment.fecha_hora.desc(), StockAdjustment.operation_id)
            .limit(limit)
            .offset(offset)
        )
        adjustments = await self.session.scalars(statement)

        return list(adjustments.all())
