from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ...core.config.db_config import Base


class StockAdjustment(Base):
    __tablename__ = "ajuste_inventario"
    __table_args__ = (
        CheckConstraint("cantidad <> 0"),
        CheckConstraint("stock_anterior >= 0"),
        CheckConstraint("stock_nuevo >= 0"),
        CheckConstraint("stock_nuevo = stock_anterior + cantidad"),
    )

    operation_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    id_producto: Mapped[int] = mapped_column(ForeignKey("producto.id_producto"))
    id_empleado: Mapped[int] = mapped_column(ForeignKey("empleado.id_empleado"))

    cantidad: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    stock_anterior: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    stock_nuevo: Mapped[Decimal] = mapped_column(Numeric(10, 3))

    motivo: Mapped[str] = mapped_column(String(250))
    request_hash: Mapped[str] = mapped_column(String(64))
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
