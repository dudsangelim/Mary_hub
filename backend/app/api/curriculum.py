from __future__ import annotations

from fastapi import APIRouter, Query

from app.deps import CurrentGuardian, DbSession
from app.schemas.curriculum import CurriculumItemRead, SubjectRead
from app.services.curriculum_service import list_curriculum_items, list_subjects

router = APIRouter(prefix="", tags=["curriculum"])


@router.get("/subjects", response_model=list[SubjectRead])
async def get_subjects(
    session: DbSession,
    current_guardian: CurrentGuardian,
    grade: str | None = Query(default=None),
) -> list[SubjectRead]:
    _ = current_guardian
    return [SubjectRead.model_validate(subject) for subject in await list_subjects(session, grade)]


@router.get("/subjects/{subject_id}/curriculum", response_model=list[CurriculumItemRead])
async def get_curriculum(subject_id, session: DbSession, current_guardian: CurrentGuardian) -> list[CurriculumItemRead]:
    _ = current_guardian
    return [CurriculumItemRead.model_validate(item) for item in await list_curriculum_items(session, subject_id)]
