from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel, date, datetime, time


class TaskRead(ORMModel):
    id: UUID
    student_id: UUID
    created_by: UUID
    material_id: UUID | None
    title: str
    description: str | None
    subject_id: UUID | None
    task_type: str
    due_date: date | None
    due_time: time | None
    status: str
    priority: str
    parent_notes: str | None
    estimated_minutes: int | None
    completed_at: datetime | None
    source: str
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    student_id: UUID
    material_id: UUID | None = None
    title: str = Field(max_length=500)
    description: str | None = None
    subject_id: UUID | None = None
    task_type: str = "homework"
    due_date: date | None = None
    due_time: time | None = None
    status: str = "pending"
    priority: str = "normal"
    parent_notes: str | None = None
    estimated_minutes: int | None = None
    source: str = "manual"


class TaskUpdate(BaseModel):
    material_id: UUID | None = None
    title: str | None = Field(default=None, max_length=500)
    description: str | None = None
    subject_id: UUID | None = None
    task_type: str | None = None
    due_date: date | None = None
    due_time: time | None = None
    status: str | None = None
    priority: str | None = None
    parent_notes: str | None = None
    estimated_minutes: int | None = None
    source: str | None = None


class TaskStatusUpdate(BaseModel):
    status: str


class AgendaTaskImportItem(BaseModel):
    activity_date: date
    card_color: str = Field(min_length=1, max_length=30)
    subject_name: str | None = Field(default=None, max_length=255)
    topic: str | None = None
    classwork_text: str | None = None
    homework_text: str | None = None
    teacher_name: str | None = Field(default=None, max_length=255)
    raw_text: str | None = None


class AgendaTaskImportRequest(BaseModel):
    student_id: UUID
    source_app: str = Field(default="tell_me", max_length=50)
    screenshot_date: date | None = None
    items: list[AgendaTaskImportItem] = Field(default_factory=list)


class AgendaTaskImportResponse(BaseModel):
    created: int
    updated: int
    skipped: int
    tasks: list[TaskRead]


class OpenClawAgendaIngestRequest(BaseModel):
    student_id: UUID
    source_channel: str = Field(default="telegram_openclaw", max_length=50)
    screenshot_date: date | None = None
    source_message_id: str | None = Field(default=None, max_length=255)
    source_chat_id: str | None = Field(default=None, max_length=255)
    image_path: str | None = Field(default=None, max_length=1000)
    extraction_model: str | None = Field(default=None, max_length=255)
    extraction_confidence: float | None = None
    items: list[AgendaTaskImportItem] = Field(default_factory=list)


class OpenClawAgendaIngestResponse(BaseModel):
    created: int
    updated: int
    skipped: int
    student_id: UUID
    student_name: str
    pending_tasks_count: int
    agenda_task_ids: list[UUID]
    linked_subjects: list[str]
    library_context_titles: list[str]
    message: str


class DashboardTodayStudent(BaseModel):
    student_id: UUID
    student_name: str
    avatar_color: str
    tasks_due_today: list[TaskRead]
    tasks_overdue: list[TaskRead]
    tasks_in_progress: list[TaskRead]


class DashboardTodayResponse(BaseModel):
    date: date
    students: list[DashboardTodayStudent]


class DashboardSummaryStudent(BaseModel):
    student_id: UUID
    student_name: str
    total_tasks: int
    pending: int
    in_progress: int
    done: int
    overdue: int
    materials_count: int


class DashboardSummaryResponse(BaseModel):
    students: list[DashboardSummaryStudent]
