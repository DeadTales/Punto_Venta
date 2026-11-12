from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ...core.config.db_config import Base


class OutboxEvent(Base):
    __tablename__ = "sync_outbox"
    __table_args__ = (CheckConstraint("status IN ('pending', 'sent', 'conflict')"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[UUID] = mapped_column(Uuid, default=uuid4, unique=True)
    kind: Mapped[str] = mapped_column(String(50))
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime)


class SyncReceipt(Base):
    __tablename__ = "sync_receipt"
    event_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    payload_hash: Mapped[str] = mapped_column(String(64))
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
