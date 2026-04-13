from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Subject(TimestampMixin, Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("slug", "grade", name="uq_subject_slug_grade"),)

    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    grade: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(50), default="core")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    curriculum_items = relationship("CurriculumItem", back_populates="subject")


class CurriculumItem(TimestampMixin, Base):
    __tablename__ = "curriculum_items"

    subject_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    bncc_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    semester: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty_level: Mapped[str] = mapped_column(String(20), default="normal")
    source_type: Mapped[str] = mapped_column(String(30), default="seed_demo")
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    subject = relationship("Subject", back_populates="curriculum_items")
