"""Identidad compartida por los modelos que participan en sincronización."""

from uuid import UUID, uuid4

from sqlalchemy import Uuid, text
from sqlalchemy.orm import Mapped, mapped_column


class SyncIdentity:
    sync_id: Mapped[UUID] = mapped_column(
        Uuid, unique=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
