from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class SchoolMaterial(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "school_materials"

    student_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"))
    uploaded_by: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("guardians.id"))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=True)
    material_type: Mapped[str] = mapped_column(String(50))
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="manual_upload")
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)

    student = relationship("Student", back_populates="materials")
    subject = relationship("Subject")


class SchoolTask(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "school_tasks"

    student_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"))
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("guardians.id"))
    material_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("school_materials.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), default="homework")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    parent_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="manual")

    student = relationship("Student", back_populates="tasks")
    subject = relationship("Subject")
    material = relationship("SchoolMaterial")


class ClassifiedTask(TimestampMixin, Base):
    __tablename__ = "classified_tasks"

    task_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("school_tasks.id"), unique=True)
    curriculum_item_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("curriculum_items.id"), nullable=True)
    difficulty_assessed: Mapped[str | None] = mapped_column(String(20), nullable=True)
    estimated_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    classification_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    classification_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    classification_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    classified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    classified_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
