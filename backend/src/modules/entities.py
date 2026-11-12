"""Las siete entidades del documento y metadatos mínimos de sincronización.

Los nombres SQL son minúsculos porque PostgreSQL normaliza los identificadores
sin comillas del DDL original. Los UUID no reemplazan las PK SERIAL existentes.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.config.db_config import Base


class SyncIdentity:
    sync_id: Mapped[UUID] = mapped_column(Uuid, unique=True, default=uuid4, server_default=text("gen_random_uuid()"))


class Category(SyncIdentity, Base):
    __tablename__ = "categoria"
    id_categoria: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    descripcion: Mapped[str | None] = mapped_column(Text)


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


class PaymentMethod(Base):
    __tablename__ = "metodo_pago"
    __table_args__ = (CheckConstraint(
        "nombre IN ('Efectivo', 'Tarjeta Débito', 'Tarjeta Crédito', 'Transferencia')"
    ),)
    id_metodo_pago: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50))


class Product(SyncIdentity, Base):
    __tablename__ = "producto"
    __table_args__ = tuple(CheckConstraint(f"{field} >= 0") for field in (
        "precio_compra", "precio_venta", "stock_actual", "stock_minimo"
    ))
    id_producto: Mapped[int] = mapped_column(primary_key=True)
    id_categoria: Mapped[int] = mapped_column(ForeignKey("categoria.id_categoria"))
    codigo_barras: Mapped[str | None] = mapped_column(String(50), unique=True)
    nombre: Mapped[str] = mapped_column(String(150))
    descripcion: Mapped[str | None] = mapped_column(Text)
    precio_compra: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    precio_venta: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock_actual: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    stock_minimo: Mapped[Decimal] = mapped_column(Numeric(10, 3))


class Sale(SyncIdentity, Base):
    __tablename__ = "venta"
    __table_args__ = (
        CheckConstraint("total >= 0"),
        CheckConstraint("estado IN ('Completada', 'Cancelada')"),
    )
    id_venta: Mapped[int] = mapped_column(primary_key=True)
    id_cliente: Mapped[int | None] = mapped_column(ForeignKey("cliente.id_cliente"))
    id_empleado: Mapped[int] = mapped_column(ForeignKey("empleado.id_empleado"))
    id_metodo_pago: Mapped[int] = mapped_column(ForeignKey("metodo_pago.id_metodo_pago"))
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, server_default=func.now())
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    estado: Mapped[str] = mapped_column(String(20), default="Completada")
    request_hash: Mapped[str | None] = mapped_column(String(64))


class SaleDetail(Base):
    __tablename__ = "detalle_venta"
    __table_args__ = (
        CheckConstraint("cantidad > 0"), CheckConstraint("precio_unitario_venta >= 0"),
        CheckConstraint("subtotal >= 0"),
    )
    id_detalle_venta: Mapped[int] = mapped_column(primary_key=True)
    id_venta: Mapped[int] = mapped_column(ForeignKey("venta.id_venta", ondelete="CASCADE"))
    id_producto: Mapped[int] = mapped_column(ForeignKey("producto.id_producto"))
    cantidad: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    precio_unitario_venta: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
