from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class MaryReport(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "mary_reports"

    student_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"))
    report_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[dict] = mapped_column(JSONB)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    generated_by: Mapped[str] = mapped_column(String(50), default="system")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
