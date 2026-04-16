from __future__ import annotations

from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class Weekday(str, Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"


class SessionKind(str, Enum):
    homework = "homework"
    reading = "reading"
    review = "review"
    light = "light"
    weekly_prep = "weekly_prep"
    free = "free"


class ClassBlock(BaseModel):
    subject: str
    start: str  # HH:MM
    end: str    # HH:MM
    kind: SessionKind = SessionKind.homework


class FixedActivity(BaseModel):
    name: str
    weekday: Weekday
    start: str  # HH:MM
    end: str    # HH:MM
    priority: int = 1


class TutorWindow(BaseModel):
    start: str  # HH:MM
    end: str    # HH:MM
    kind: SessionKind = SessionKind.homework
    label: str | None = None


WeeklySchedule = dict[str, list[ClassBlock]]
TutorWindowsByDay = dict[str, list[TutorWindow]]


class StudentProfileRead(ORMModel):
    id: UUID
    student_id: UUID
    learning_style: str | None
    attention_span_minutes: int | None
    best_study_time: str | None
    difficulty_areas: list[str]
    strength_areas: list[str]
    notes: str | None
    weekly_schedule: dict = Field(default_factory=dict)
    fixed_activities: list[dict] = Field(default_factory=list)
    tutor_windows: dict = Field(default_factory=dict)


class StudentProfileUpdate(BaseModel):
    learning_style: str | None = Field(default=None, max_length=50)
    attention_span_minutes: int | None = None
    best_study_time: str | None = Field(default=None, max_length=20)
    difficulty_areas: list[str] | None = None
    strength_areas: list[str] | None = None
    notes: str | None = None
    weekly_schedule: dict | None = None
    fixed_activities: list[dict] | None = None
    tutor_windows: dict | None = None


class InterestProfileRead(ORMModel):
    id: UUID
    student_id: UUID
    interests: list[str]
    favorite_subjects: list[str]
    hobbies: list[str]
    motivators: list[str]
    aversions: list[str]


class InterestProfileUpdate(BaseModel):
    interests: list[str] | None = None
    favorite_subjects: list[str] | None = None
    hobbies: list[str] | None = None
    motivators: list[str] | None = None
    aversions: list[str] | None = None


class StudentRead(ORMModel):
    id: UUID
    family_id: UUID
    name: str
    birth_date: date | None
    grade: str
    grade_label: str
    school_name: str | None
    school_shift: str | None
    avatar_color: str
    is_active: bool
    profile: StudentProfileRead | None = None
    interests: InterestProfileRead | None = None


class StudentUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    birth_date: date | None = None
    grade_label: str | None = Field(default=None, max_length=100)
    school_name: str | None = Field(default=None, max_length=255)
    school_shift: str | None = Field(default=None, max_length=20)
    avatar_color: str | None = Field(default=None, max_length=7)
    is_active: bool | None = None
