from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentGuardian, DbSession
from app.errors import error_response
from app.models.family import Student
from app.schemas.profile import InterestProfileRead, InterestProfileUpdate, StudentProfileRead, StudentProfileUpdate, StudentRead, StudentUpdate

router = APIRouter(prefix="/students", tags=["students"])


async def get_family_student(session: DbSession, family_id, student_id):
    student = await session.scalar(
        select(Student)
        .where(Student.id == student_id, Student.family_id == family_id)
        .options(selectinload(Student.profile), selectinload(Student.interests))
    )
    if student is None:
        raise error_response("STUDENT_NOT_FOUND", "Student not found", http_status=404)
    return student


@router.get("", response_model=list[StudentRead])
async def list_students(current_guardian: CurrentGuardian, session: DbSession) -> list[StudentRead]:
    students = list(
        (
            await session.scalars(
                select(Student)
                .where(Student.family_id == current_guardian.family_id, Student.is_active == True)
                .options(selectinload(Student.profile), selectinload(Student.interests))
                .order_by(Student.name)
            )
        ).all()
    )
    return [StudentRead.model_validate(student) for student in students]


@router.get("/{student_id}", response_model=StudentRead)
async def get_student(student_id, current_guardian: CurrentGuardian, session: DbSession) -> StudentRead:
    return StudentRead.model_validate(await get_family_student(session, current_guardian.family_id, student_id))


@router.put("/{student_id}", response_model=StudentRead)
async def update_student(student_id, payload: StudentUpdate, current_guardian: CurrentGuardian, session: DbSession) -> StudentRead:
    student = await get_family_student(session, current_guardian.family_id, student_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    await session.commit()
    await session.refresh(student)
    await session.refresh(student, attribute_names=["profile", "interests"])
    return StudentRead.model_validate(student)


@router.get("/{student_id}/profile", response_model=StudentProfileRead)
async def get_profile(student_id, current_guardian: CurrentGuardian, session: DbSession) -> StudentProfileRead:
    student = await get_family_student(session, current_guardian.family_id, student_id)
    return StudentProfileRead.model_validate(student.profile)


@router.put("/{student_id}/profile", response_model=StudentProfileRead)
async def update_profile(student_id, payload: StudentProfileUpdate, current_guardian: CurrentGuardian, session: DbSession) -> StudentProfileRead:
    student = await get_family_student(session, current_guardian.family_id, student_id)
    profile = student.profile
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await session.commit()
    await session.refresh(profile)
    return StudentProfileRead.model_validate(profile)


@router.get("/{student_id}/interests", response_model=InterestProfileRead)
async def get_interests(student_id, current_guardian: CurrentGuardian, session: DbSession) -> InterestProfileRead:
    student = await get_family_student(session, current_guardian.family_id, student_id)
    return InterestProfileRead.model_validate(student.interests)


@router.put("/{student_id}/interests", response_model=InterestProfileRead)
async def update_interests(student_id, payload: InterestProfileUpdate, current_guardian: CurrentGuardian, session: DbSession) -> InterestProfileRead:
    student = await get_family_student(session, current_guardian.family_id, student_id)
    interests = student.interests
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(interests, field, value)
    await session.commit()
    await session.refresh(interests)
    return InterestProfileRead.model_validate(interests)
