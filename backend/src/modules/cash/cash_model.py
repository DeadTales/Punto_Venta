from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from ...core.config.db_config import Base


class CashShift(Base):
    __tablename__ = "turno_caja"
    __table_args__ = (
        CheckConstraint("estado IN ('Abierta', 'Cerrada')"),
        CheckConstraint("fondo_inicial >= 0"),
        CheckConstraint("efectivo_contado >= 0"),
        Index(
            "uq_turno_empleado_abierto",
            "id_empleado",
            unique=True,
            postgresql_where=text("estado = 'Abierta'"),
        ),
    )

    id_turno: Mapped[int] = mapped_column(primary_key=True)
    operation_id: Mapped[UUID] = mapped_column(Uuid, unique=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    id_empleado: Mapped[int] = mapped_column(ForeignKey("empleado.id_empleado"))
    estado: Mapped[str] = mapped_column(String(20), default="Abierta")

    apertura: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    cierre: Mapped[datetime | None] = mapped_column(DateTime)
    fondo_inicial: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    efectivo_esperado: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    efectivo_contado: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    diferencia: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    close_operation_id: Mapped[UUID | None] = mapped_column(Uuid, unique=True)
    close_hash: Mapped[str | None] = mapped_column(String(64))
    notas: Mapped[str | None] = mapped_column(String(500))
