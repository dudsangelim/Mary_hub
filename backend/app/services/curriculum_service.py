from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.curriculum import CurriculumItem, Subject


async def list_subjects(session: AsyncSession, grade: str | None = None) -> list[Subject]:
    query = select(Subject).where(Subject.is_active.is_(True)).order_by(Subject.grade, Subject.name)
    if grade:
        query = query.where(Subject.grade == grade)
    result = await session.scalars(query)
    return list(result.all())


async def list_curriculum_items(session: AsyncSession, subject_id) -> list[CurriculumItem]:
    result = await session.scalars(
        select(CurriculumItem).where(CurriculumItem.subject_id == subject_id).order_by(CurriculumItem.order_index, CurriculumItem.title)
    )
    return list(result.all())
