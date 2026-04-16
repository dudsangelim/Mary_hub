from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.profile import SessionKind


class SessionStep(BaseModel):
    index: int
    kind: str  # "intro" | "task" | "celebration"
    task_id: UUID | None = None
    task_title: str | None = None
    subject: str | None = None
    pages: str | None = None
    book_reference: str | None = None
    instruction: str | None = None
    audio_key: str | None = None
    done: bool = False


class SessionRuntimeState(BaseModel):
    current_step: int = 0
    started_at: datetime | None = None
    last_activity_at: datetime | None = None


class SessionOutcome(BaseModel):
    completed_steps: int = 0
    total_steps: int = 0
    tasks_done: list[UUID] = []
    duration_minutes: int | None = None


class TutorSessionRead(BaseModel):
    id: UUID
    student_id: UUID | None
    student_name: str | None = None
    plan_id: UUID
    task_id: UUID | None
    title: str
    scheduled_date: date
    session_kind: str
    status: str
    runtime_state: dict
    steps: list[dict]
    outcome: dict

    model_config = {"from_attributes": True}


class TutorSessionCreate(BaseModel):
    student_id: UUID
    scheduled_date: date
    session_kind: SessionKind = SessionKind.homework


class TutorNextRequest(BaseModel):
    session_id: UUID
    step_index: int
    mark_done: bool = False


class TutorNextResponse(BaseModel):
    session_id: UUID
    step: SessionStep | None
    is_last: bool
    message: str | None = None


class TutorTTSRequest(BaseModel):
    text: str
    voice: str = "nova"


class TutorTTSResponse(BaseModel):
    audio_key: str
    cached: bool


# Status endpoint
class TutorStatusResponse(BaseModel):
    available: bool
    reason: str
    next_window_start: datetime | None = None
    next_window_end: datetime | None = None
    session_type: str | None = None
    existing_session_id: UUID | None = None


# Stuck endpoint
class TutorStuckRequest(BaseModel):
    step_id: str
    reason: str = ""


# Complete endpoint
class TutorCompleteRequest(BaseModel):
    completion_notes: str = ""
    parent_feedback: str = ""


# Message endpoint
class TutorMessageRequest(BaseModel):
    user_message: str
    step_id: str = ""


class TutorMessageResponse(BaseModel):
    reply_text: str
    reply_audio_url: str | None = None
    suggested_next_action: str
