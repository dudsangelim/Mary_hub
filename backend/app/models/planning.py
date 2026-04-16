from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, Time
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class StudyPlan(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "study_plans"

    student_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_type: Mapped[str] = mapped_column(String(50), default="weekly")
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    generated_by: Mapped[str] = mapped_column(String(50), default="manual")
    plan_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)


class StudySession(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "study_sessions"

    plan_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("study_plans.id"))
    task_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("school_tasks.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    scheduled_date: Mapped[date] = mapped_column(Date)
    scheduled_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    scheduled_end: Mapped[time | None] = mapped_column(Time, nullable=True)
    actual_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="scheduled")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # v0.2 — Session Engine
    student_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=True)
    session_kind: Mapped[str] = mapped_column(String(30), default="homework")
    runtime_state: Mapped[dict] = mapped_column(JSONB, default=dict)
    steps: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    outcome: Mapped[dict] = mapped_column(JSONB, default=dict)
