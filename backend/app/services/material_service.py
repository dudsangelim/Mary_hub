from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.errors import error_response
from app.models.curriculum import Subject
from app.models.family import Guardian, Student
from app.models.material import SchoolMaterial
from app.schemas.material import MaterialCreate, MaterialUpdate


async def get_student_for_family(session: AsyncSession, family_id, student_id: UUID) -> Student:
    student = await session.scalar(select(Student).where(Student.id == student_id, Student.family_id == family_id, Student.is_active.is_(True)))
    if student is None:
        raise error_response("STUDENT_NOT_FOUND", "Student not found", http_status=404)
    return student


async def validate_subject_for_grade(session: AsyncSession, grade: str, subject_id: UUID | None) -> Subject | None:
    if subject_id is None:
        return None
    subject = await session.scalar(select(Subject).where(Subject.id == subject_id, Subject.grade == grade, Subject.is_active.is_(True)))
    if subject is None:
        raise error_response("SUBJECT_NOT_FOUND", "Subject not found for student grade", http_status=404)
    return subject


async def list_materials(
    session: AsyncSession,
    guardian: Guardian,
    student_id: UUID | None,
    subject_id: UUID | None,
    material_type: str | None,
    page: int,
    per_page: int,
) -> tuple[list[SchoolMaterial], int]:
    query = (
        select(SchoolMaterial)
        .join(Student, Student.id == SchoolMaterial.student_id)
        .where(Student.family_id == guardian.family_id, SchoolMaterial.deleted_at.is_(None))
        .options(selectinload(SchoolMaterial.subject))
        .order_by(SchoolMaterial.created_at.desc())
    )
    count_query = (
        select(func.count())
        .select_from(SchoolMaterial)
        .join(Student, Student.id == SchoolMaterial.student_id)
        .where(Student.family_id == guardian.family_id, SchoolMaterial.deleted_at.is_(None))
    )
    if student_id:
        query = query.where(SchoolMaterial.student_id == student_id)
        count_query = count_query.where(SchoolMaterial.student_id == student_id)
    if subject_id:
        query = query.where(SchoolMaterial.subject_id == subject_id)
        count_query = count_query.where(SchoolMaterial.subject_id == subject_id)
    if material_type:
        query = query.where(SchoolMaterial.material_type == material_type)
        count_query = count_query.where(SchoolMaterial.material_type == material_type)

    items = list((await session.scalars(query.offset((page - 1) * per_page).limit(per_page))).all())
    total = await session.scalar(count_query) or 0
    return items, total


async def get_material(session: AsyncSession, guardian: Guardian, material_id: UUID) -> SchoolMaterial:
    material = await session.scalar(
        select(SchoolMaterial)
        .join(Student, Student.id == SchoolMaterial.student_id)
        .where(SchoolMaterial.id == material_id, Student.family_id == guardian.family_id, SchoolMaterial.deleted_at.is_(None))
        .options(selectinload(SchoolMaterial.subject))
    )
    if material is None:
        raise error_response("MATERIAL_NOT_FOUND", "Material not found", http_status=404)
    return material


async def create_text_material(session: AsyncSession, guardian: Guardian, payload: MaterialCreate) -> SchoolMaterial:
    student = await get_student_for_family(session, guardian.family_id, payload.student_id)
    await validate_subject_for_grade(session, student.grade, payload.subject_id)
    material = SchoolMaterial(
        student_id=student.id,
        uploaded_by=guardian.id,
        title=payload.title,
        description=payload.description,
        subject_id=payload.subject_id,
        material_type=payload.material_type,
        text_content=payload.text_content,
        source=payload.source,
        tags=payload.tags,
    )
    session.add(material)
    await session.commit()
    await session.refresh(material)
    return material


async def update_material(session: AsyncSession, guardian: Guardian, material_id: UUID, payload: MaterialUpdate) -> SchoolMaterial:
    material = await get_material(session, guardian, material_id)
    student = await get_student_for_family(session, guardian.family_id, material.student_id)
    if payload.subject_id is not None:
        await validate_subject_for_grade(session, student.grade, payload.subject_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(material, field, value)
    await session.commit()
    await session.refresh(material)
    return material


async def soft_delete_material(session: AsyncSession, guardian: Guardian, material_id: UUID) -> None:
    material = await get_material(session, guardian, material_id)
    from datetime import UTC, datetime

    material.deleted_at = datetime.now(UTC)
    await session.commit()
