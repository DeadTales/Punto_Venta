"""Las siete entidades del documento y metadatos mínimos de sincronización.

Los nombres SQL son minúsculos porque PostgreSQL normaliza los identificadores
sin comillas del DDL original. Los UUID no reemplazan las PK SERIAL existentes.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..core.config.db_config import Base
from .catalog.catalog_model import SyncIdentity
from .category.category_model import Category
from .product.product_model import Product


class Client(SyncIdentity, Base):
    __tablename__ = "cliente"
    __table_args__ = (CheckConstraint("correo LIKE '%@%'"),)
    id_cliente: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150))
    telefono: Mapped[str | None] = mapped_column(String(20))
    correo: Mapped[str | None] = mapped_column(String(150))
    rfc_o_identificacion_fiscal: Mapped[str | None] = mapped_column(String(50))


class Employee(SyncIdentity, Base):
    __tablename__ = "empleado"
    __table_args__ = (
        CheckConstraint("correo LIKE '%@%'"),
        CheckConstraint("rol IN ('Cajero', 'Administrador', 'Supervisor')"),
    )
    id_empleado: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    apellido: Mapped[str] = mapped_column(String(100))
    correo: Mapped[str] = mapped_column(String(150), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(String(50))
    telefono: Mapped[str | None] = mapped_column(String(20))
    activo: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true")
    )
    token_version: Mapped[int] = mapped_column(default=0, server_default=text("0"))


class PaymentMethod(Base):
    __tablename__ = "metodo_pago"
    __table_args__ = (
        CheckConstraint(
            "nombre IN ('Efectivo', 'Tarjeta Débito', 'Tarjeta Crédito', 'Transferencia')"
        ),
    )
    id_metodo_pago: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50))


class Sale(SyncIdentity, Base):
    __tablename__ = "venta"
    __table_args__ = (
        CheckConstraint("total >= 0"),
        CheckConstraint("estado IN ('Completada', 'Cancelada')"),
    )
    id_venta: Mapped[int] = mapped_column(primary_key=True)
    id_cliente: Mapped[int | None] = mapped_column(ForeignKey("cliente.id_cliente"))
    id_empleado: Mapped[int] = mapped_column(ForeignKey("empleado.id_empleado"))
    id_metodo_pago: Mapped[int] = mapped_column(
        ForeignKey("metodo_pago.id_metodo_pago")
    )
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    estado: Mapped[str] = mapped_column(String(20), default="Completada")
    request_hash: Mapped[str | None] = mapped_column(String(64))
    id_turno: Mapped[int | None] = mapped_column(ForeignKey("turno_caja.id_turno"))
    tasa_impuesto: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=Decimal(0), server_default=text("0")
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal(0), server_default=text("0")
    )
    impuesto: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal(0), server_default=text("0")
    )
    cancel_operation_id: Mapped[UUID | None] = mapped_column(Uuid, unique=True)
    cancel_hash: Mapped[str | None] = mapped_column(String(64))
    cancel_motivo: Mapped[str | None] = mapped_column(String(250))
    cancelado_por: Mapped[int | None] = mapped_column(
        ForeignKey("empleado.id_empleado")
    )
    cancelado_en: Mapped[datetime | None] = mapped_column(DateTime)


class SaleDetail(Base):
    __tablename__ = "detalle_venta"
    __table_args__ = (
        CheckConstraint("cantidad > 0"),
        CheckConstraint("precio_unitario_venta >= 0"),
        CheckConstraint("subtotal >= 0"),
    )
    id_detalle_venta: Mapped[int] = mapped_column(primary_key=True)
    id_venta: Mapped[int] = mapped_column(
        ForeignKey("venta.id_venta", ondelete="CASCADE")
    )
    id_producto: Mapped[int] = mapped_column(ForeignKey("producto.id_producto"))
    cantidad: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    precio_unitario_venta: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    nombre_producto: Mapped[str | None] = mapped_column(String(150))
    codigo_barras: Mapped[str | None] = mapped_column(String(50))


# Los modelos de Persona 2 se exportan para preservar los imports existentes.

__all__ = [
    "SyncIdentity",
    "Category",
    "Product",
    "Client",
    "Employee",
    "PaymentMethod",
    "Sale",
    "SaleDetail",
]
