from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ...core.config.db_config import Base
from ..catalog.catalog_model import SyncIdentity


class Category(SyncIdentity, Base):
    __tablename__ = "categoria"
    id_categoria: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    descripcion: Mapped[str | None] = mapped_column(Text)
