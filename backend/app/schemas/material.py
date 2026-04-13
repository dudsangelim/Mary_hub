from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel, date, datetime


class MaterialRead(ORMModel):
    id: UUID
    student_id: UUID
    uploaded_by: UUID
    title: str
    description: str | None
    subject_id: UUID | None
    material_type: str
    file_path: str | None
    file_name: str | None
    file_size_bytes: int | None
    mime_type: str | None
    text_content: str | None
    source: str
    tags: list[str]
    is_processed: bool
    created_at: datetime
    updated_at: datetime


class MaterialCreate(BaseModel):
    student_id: UUID
    title: str = Field(max_length=500)
    description: str | None = None
    subject_id: UUID | None = None
    material_type: str = Field(max_length=50)
    text_content: str | None = None
    source: str = "manual_upload"
    tags: list[str] = []


class MaterialUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    description: str | None = None
    subject_id: UUID | None = None
    source: str | None = Field(default=None, max_length=50)
    tags: list[str] | None = None
