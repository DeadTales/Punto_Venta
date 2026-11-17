from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ...core.config.db_config import Base
from ..catalog.catalog_model import SyncIdentity


class Product(SyncIdentity, Base):
    __tablename__ = "producto"
    __table_args__ = tuple(
        CheckConstraint(f"{field} >= 0")
        for field in ("precio_compra", "precio_venta", "stock_actual", "stock_minimo")
    )

    id_producto: Mapped[int] = mapped_column(primary_key=True)
    id_categoria: Mapped[int] = mapped_column(ForeignKey("categoria.id_categoria"))

    codigo_barras: Mapped[str | None] = mapped_column(String(50), unique=True)
    nombre: Mapped[str] = mapped_column(String(150))
    descripcion: Mapped[str | None] = mapped_column(Text)

    precio_compra: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    precio_venta: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    stock_actual: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    stock_minimo: Mapped[Decimal] = mapped_column(Numeric(10, 3))
