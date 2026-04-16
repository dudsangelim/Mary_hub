from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentGuardian, DbSession
from app.errors import error_response
from app.models.family import Student
from app.schemas.schedule import ScheduleRead, ScheduleUpdate

router = APIRouter(prefix="/students", tags=["schedule"])


async def _get_student(session: DbSession, family_id, student_id):
    student = await session.scalar(
        select(Student)
        .where(Student.id == student_id, Student.family_id == family_id)
        .options(selectinload(Student.profile))
    )
    if student is None:
        raise error_response("STUDENT_NOT_FOUND", "Student not found", http_status=404)
    if student.profile is None:
        raise error_response("PROFILE_NOT_FOUND", "Student profile not found", http_status=404)
    return student


@router.get("/{student_id}/schedule", response_model=ScheduleRead)
async def get_schedule(
    student_id: UUID,
    current_guardian: CurrentGuardian,
    session: DbSession,
) -> ScheduleRead:
    student = await _get_student(session, current_guardian.family_id, student_id)
    profile = student.profile
    return ScheduleRead(
        weekly_schedule=profile.weekly_schedule or {},
        fixed_activities=profile.fixed_activities or [],
        tutor_windows=profile.tutor_windows or {},
    )


@router.put("/{student_id}/schedule", response_model=ScheduleRead)
async def update_schedule(
    student_id: UUID,
    payload: ScheduleUpdate,
    current_guardian: CurrentGuardian,
    session: DbSession,
) -> ScheduleRead:
    student = await _get_student(session, current_guardian.family_id, student_id)
    profile = student.profile

    if payload.weekly_schedule is not None:
        profile.weekly_schedule = {
            day: [b.model_dump() for b in blocks]
            for day, blocks in payload.weekly_schedule.items()
        }
    if payload.fixed_activities is not None:
        profile.fixed_activities = [a.model_dump() for a in payload.fixed_activities]
    if payload.tutor_windows is not None:
        profile.tutor_windows = {
            day: [w.model_dump() for w in windows]
            for day, windows in payload.tutor_windows.items()
        }

    await session.commit()
    await session.refresh(profile)

    return ScheduleRead(
        weekly_schedule=profile.weekly_schedule or {},
        fixed_activities=profile.fixed_activities or [],
        tutor_windows=profile.tutor_windows or {},
    )
