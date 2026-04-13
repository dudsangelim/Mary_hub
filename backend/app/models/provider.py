from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class ProviderAccount(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "provider_accounts"

    student_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"))
    provider_name: Mapped[str] = mapped_column(String(100))
    provider_type: Mapped[str] = mapped_column(String(50))
    credentials_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_config: Mapped[dict] = mapped_column(JSONB, default=dict)


class ProviderSyncLog(TimestampMixin, Base):
    __tablename__ = "provider_sync_logs"

    provider_account_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("provider_accounts.id"))
    sync_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30))
    items_found: Mapped[int] = mapped_column(Integer, default=0)
    items_synced: Mapped[int] = mapped_column(Integer, default=0)
    items_failed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
