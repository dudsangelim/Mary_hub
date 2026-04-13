from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class StudentProfile(TimestampMixin, Base):
    __tablename__ = "student_profiles"

    student_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"), unique=True)
    learning_style: Mapped[str | None] = mapped_column(String(50), nullable=True)
    attention_span_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    best_study_time: Mapped[str | None] = mapped_column(String(20), nullable=True)
    difficulty_areas: Mapped[list[str]] = mapped_column(JSONB, default=list)
    strength_areas: Mapped[list[str]] = mapped_column(JSONB, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    student = relationship("Student", back_populates="profile")


class InterestProfile(TimestampMixin, Base):
    __tablename__ = "interest_profiles"

    student_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"), unique=True)
    interests: Mapped[list[str]] = mapped_column(JSONB, default=list)
    favorite_subjects: Mapped[list[str]] = mapped_column(JSONB, default=list)
    hobbies: Mapped[list[str]] = mapped_column(JSONB, default=list)
    motivators: Mapped[list[str]] = mapped_column(JSONB, default=list)
    aversions: Mapped[list[str]] = mapped_column(JSONB, default=list)

    student = relationship("Student", back_populates="interests")
