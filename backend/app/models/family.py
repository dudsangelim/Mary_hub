from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Family(TimestampMixin, Base):
    __tablename__ = "families"

    name: Mapped[str] = mapped_column(String(255))
    timezone: Mapped[str] = mapped_column(String(50), default="America/Sao_Paulo")
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    guardians = relationship("Guardian", back_populates="family")
    students = relationship("Student", back_populates="family")


class Guardian(TimestampMixin, Base):
    __tablename__ = "guardians"

    family_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("families.id"))
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="parent")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    family = relationship("Family", back_populates="guardians")


class Student(TimestampMixin, Base):
    __tablename__ = "students"

    family_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("families.id"))
    name: Mapped[str] = mapped_column(String(255))
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    grade: Mapped[str] = mapped_column(String(50))
    grade_label: Mapped[str] = mapped_column(String(100))
    school_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    school_shift: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_color: Mapped[str] = mapped_column(String(7), default="#6366f1")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    family = relationship("Family", back_populates="students")
    profile = relationship("StudentProfile", back_populates="student", uselist=False)
    interests = relationship("InterestProfile", back_populates="student", uselist=False)
    materials = relationship("SchoolMaterial", back_populates="student")
    tasks = relationship("SchoolTask", back_populates="student")
