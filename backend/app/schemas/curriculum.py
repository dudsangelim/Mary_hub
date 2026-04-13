from __future__ import annotations

from uuid import UUID

from app.schemas.common import ORMModel


class SubjectRead(ORMModel):
    id: UUID
    name: str
    slug: str
    grade: str
    category: str
    description: str | None
    is_active: bool


class CurriculumItemRead(ORMModel):
    id: UUID
    subject_id: UUID
    title: str
    description: str | None
    bncc_code: str | None
    order_index: int
    semester: int | None
    difficulty_level: str
    source_type: str
    source_reference: str | None
