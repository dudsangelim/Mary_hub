from __future__ import annotations

import unicodedata
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.errors import error_response
from app.models.curriculum import Subject
from app.models.family import Guardian, Student
from app.models.material import SchoolMaterial, SchoolTask
from app.schemas.task import AgendaTaskImportItem, AgendaTaskImportRequest, TaskCreate, TaskUpdate
from app.services.material_service import get_student_for_family, validate_subject_for_grade


async def list_tasks(
    session: AsyncSession,
    guardian: Guardian,
    student_id: UUID | None,
    subject_id: UUID | None,
    status: str | None,
    due_date_from: date | None,
    due_date_to: date | None,
    page: int,
    per_page: int,
) -> tuple[list[SchoolTask], int]:
    base_filters = [Student.family_id == guardian.family_id, SchoolTask.deleted_at.is_(None)]
    query = (
        select(SchoolTask)
        .join(Student, Student.id == SchoolTask.student_id)
        .where(*base_filters)
        .options(selectinload(SchoolTask.subject))
        .order_by(SchoolTask.due_date.asc().nulls_last(), SchoolTask.created_at.desc())
    )
    count_query = select(func.count()).select_from(SchoolTask).join(Student, Student.id == SchoolTask.student_id).where(*base_filters)

    if student_id:
        query = query.where(SchoolTask.student_id == student_id)
        count_query = count_query.where(SchoolTask.student_id == student_id)
    if subject_id:
        query = query.where(SchoolTask.subject_id == subject_id)
        count_query = count_query.where(SchoolTask.subject_id == subject_id)
    if status:
        query = query.where(SchoolTask.status == status)
        count_query = count_query.where(SchoolTask.status == status)
    if due_date_from:
        query = query.where(SchoolTask.due_date >= due_date_from)
        count_query = count_query.where(SchoolTask.due_date >= due_date_from)
    if due_date_to:
        query = query.where(SchoolTask.due_date <= due_date_to)
        count_query = count_query.where(SchoolTask.due_date <= due_date_to)

    items = list((await session.scalars(query.offset((page - 1) * per_page).limit(per_page))).all())
    total = await session.scalar(count_query) or 0
    return items, total


async def get_task(session: AsyncSession, guardian: Guardian, task_id: UUID) -> SchoolTask:
    task = await session.scalar(
        select(SchoolTask)
        .join(Student, Student.id == SchoolTask.student_id)
        .where(SchoolTask.id == task_id, Student.family_id == guardian.family_id, SchoolTask.deleted_at.is_(None))
        .options(selectinload(SchoolTask.subject))
    )
    if task is None:
        raise error_response("TASK_NOT_FOUND", "Task not found", http_status=404)
    return task


async def create_task(session: AsyncSession, guardian: Guardian, payload: TaskCreate) -> SchoolTask:
    student = await get_student_for_family(session, guardian.family_id, payload.student_id)
    await validate_subject_for_grade(session, student.grade, payload.subject_id)
    task = SchoolTask(created_by=guardian.id, **payload.model_dump())
    if task.status == "done" and task.completed_at is None:
        task.completed_at = datetime.now(UTC)
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def update_task(session: AsyncSession, guardian: Guardian, task_id: UUID, payload: TaskUpdate) -> SchoolTask:
    task = await get_task(session, guardian, task_id)
    student = await get_student_for_family(session, guardian.family_id, task.student_id)
    updates = payload.model_dump(exclude_unset=True)
    if "subject_id" in updates:
        await validate_subject_for_grade(session, student.grade, updates["subject_id"])
    for field, value in updates.items():
        setattr(task, field, value)
    if task.status == "done":
        task.completed_at = task.completed_at or datetime.now(UTC)
    else:
        task.completed_at = None
    await session.commit()
    await session.refresh(task)
    return task


async def update_task_status(session: AsyncSession, guardian: Guardian, task_id: UUID, new_status: str) -> SchoolTask:
    task = await get_task(session, guardian, task_id)
    task.status = new_status
    task.completed_at = datetime.now(UTC) if new_status == "done" else None
    await session.commit()
    await session.refresh(task)
    return task


async def soft_delete_task(session: AsyncSession, guardian: Guardian, task_id: UUID) -> None:
    task = await get_task(session, guardian, task_id)
    task.deleted_at = datetime.now(UTC)
    await session.commit()


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(ascii_text.lower().strip().split())


def build_agenda_task_title(item: AgendaTaskImportItem) -> str:
    subject = (item.subject_name or "Agenda").strip()
    main_text = (item.homework_text or item.topic or item.classwork_text or "Atividade").strip()
    return f"{subject}: {main_text}"[:500]


def build_agenda_task_description(item: AgendaTaskImportItem) -> str | None:
    parts = []
    if item.topic:
        parts.append(f"Conteudo: {item.topic}")
    if item.classwork_text:
        parts.append(f"Sala: {item.classwork_text}")
    if item.homework_text:
        parts.append(f"Casa: {item.homework_text}")
    if item.raw_text:
        parts.append(f"Bruto: {item.raw_text}")
    return "\n".join(parts) or None


def build_agenda_parent_notes(item: AgendaTaskImportItem, source_app: str, screenshot_date: date | None) -> str | None:
    parts = [f"Fonte: {source_app}_agenda", f"Cor do card: {item.card_color}"]
    if screenshot_date:
        parts.append(f"Screenshot: {screenshot_date.isoformat()}")
    if item.teacher_name:
        parts.append(f"Professor(a): {item.teacher_name}")
    return "\n".join(parts)


def agenda_color_to_status(card_color: str) -> str:
    normalized = normalize_text(card_color)
    if normalized in {"cinza", "gray", "grey"}:
        return "done"
    if normalized in {"verde", "green"}:
        return "pending"
    return "pending"


async def find_subject_for_student_by_name(session: AsyncSession, student: Student, subject_name: str | None) -> Subject | None:
    if not subject_name:
        return None
    target = normalize_text(subject_name)
    aliases = {
        "ciencias humanas": ["historia", "geografia", "ciencias humanas"],
        "matematica": ["matematica"],
        "portugues": ["portugues", "lingua portuguesa"],
        "lingua portuguesa": ["portugues", "lingua portuguesa"],
        "ingles": ["ingles"],
        "ciencias": ["ciencias"],
    }
    candidates = list((await session.scalars(select(Subject).where(Subject.grade == student.grade, Subject.is_active.is_(True)))).all())
    for subject in candidates:
        subject_name_normalized = normalize_text(subject.name)
        if subject_name_normalized == target:
            return subject
    for subject in candidates:
        subject_name_normalized = normalize_text(subject.name)
        if target in aliases and subject_name_normalized in aliases[target]:
            return subject
    return None


async def import_agenda_tasks(
    session: AsyncSession,
    guardian: Guardian,
    payload: AgendaTaskImportRequest,
) -> tuple[list[SchoolTask], int, int, int]:
    student = await get_student_for_family(session, guardian.family_id, payload.student_id)
    imported_tasks: list[SchoolTask] = []
    created = 0
    updated = 0
    skipped = 0

    for item in payload.items:
        title = build_agenda_task_title(item)
        description = build_agenda_task_description(item)
        status = agenda_color_to_status(item.card_color)
        task_type = "agenda_homework" if item.homework_text else "agenda_classwork"
        parent_notes = build_agenda_parent_notes(item, payload.source_app, payload.screenshot_date)
        subject = await find_subject_for_student_by_name(session, student, item.subject_name)

        existing_task = await session.scalar(
            select(SchoolTask).where(
                SchoolTask.student_id == student.id,
                SchoolTask.due_date == item.activity_date,
                SchoolTask.title == title,
                SchoolTask.deleted_at.is_(None),
            )
        )

        if existing_task is None:
            existing_task = SchoolTask(
                student_id=student.id,
                created_by=guardian.id,
                title=title,
                description=description,
                subject_id=subject.id if subject else None,
                task_type=task_type,
                due_date=item.activity_date,
                status=status,
                priority="normal",
                parent_notes=parent_notes,
                source=f"{payload.source_app}_agenda",
                completed_at=datetime.now(UTC) if status == "done" else None,
                pages=item.pages,
                book_reference=item.book_reference,
            )
            session.add(existing_task)
            created += 1
            imported_tasks.append(existing_task)
            continue

        has_changes = False
        if existing_task.source != f"{payload.source_app}_agenda":
            existing_task.source = f"{payload.source_app}_agenda"
            has_changes = True
        if existing_task.description != description:
            existing_task.description = description
            has_changes = True
        if existing_task.subject_id != (subject.id if subject else None):
            existing_task.subject_id = subject.id if subject else None
            has_changes = True
        if existing_task.task_type != task_type:
            existing_task.task_type = task_type
            has_changes = True
        if existing_task.parent_notes != parent_notes:
            existing_task.parent_notes = parent_notes
            has_changes = True
        if existing_task.status != status:
            existing_task.status = status
            existing_task.completed_at = datetime.now(UTC) if status == "done" else None
            has_changes = True
        if existing_task.pages != item.pages:
            existing_task.pages = item.pages
            has_changes = True
        if existing_task.book_reference != item.book_reference:
            existing_task.book_reference = item.book_reference
            has_changes = True

        if has_changes:
            updated += 1
            imported_tasks.append(existing_task)
        else:
            skipped += 1
            imported_tasks.append(existing_task)

    await session.commit()

    for task in imported_tasks:
        await session.refresh(task)

    return imported_tasks, created, updated, skipped


async def build_openclaw_student_context(
    session: AsyncSession,
    guardian: Guardian,
    student_id: UUID,
    imported_tasks: list[SchoolTask],
) -> dict:
    student = await get_student_for_family(session, guardian.family_id, student_id)
    pending_tasks_count = await session.scalar(
        select(func.count())
        .select_from(SchoolTask)
        .where(
            SchoolTask.student_id == student.id,
            SchoolTask.deleted_at.is_(None),
            SchoolTask.status != "done",
        )
    ) or 0

    linked_subjects = sorted(
        {
            subject.name
            for subject in (
                await session.scalars(
                    select(Subject)
                    .join(SchoolTask, SchoolTask.subject_id == Subject.id)
                    .where(SchoolTask.id.in_([task.id for task in imported_tasks if task.subject_id is not None]))
                )
            ).all()
        }
    )

    library_context_titles = list(
        (
            await session.scalars(
                select(SchoolMaterial.title)
                .where(
                    SchoolMaterial.student_id == student.id,
                    SchoolMaterial.source == "plurall_library",
                    SchoolMaterial.deleted_at.is_(None),
                )
                .order_by(SchoolMaterial.title.asc())
            )
        ).all()
    )

    return {
        "student_id": student.id,
        "student_name": student.name,
        "pending_tasks_count": pending_tasks_count,
        "agenda_task_ids": [task.id for task in imported_tasks],
        "linked_subjects": linked_subjects,
        "library_context_titles": library_context_titles,
    }


async def dashboard_today(session: AsyncSession, guardian: Guardian) -> list[dict]:
    students = list((await session.scalars(select(Student).where(Student.family_id == guardian.family_id, Student.is_active.is_(True)).order_by(Student.name))).all())
    today = date.today()
    response: list[dict] = []
    for student in students:
        tasks = list(
            (
                await session.scalars(
                    select(SchoolTask)
                    .where(SchoolTask.student_id == student.id, SchoolTask.deleted_at.is_(None))
                    .order_by(SchoolTask.due_date.asc().nulls_last(), SchoolTask.created_at.desc())
                )
            ).all()
        )
        response.append(
            {
                "student_id": student.id,
                "student_name": student.name,
                "avatar_color": student.avatar_color,
                "tasks_due_today": [task for task in tasks if task.due_date == today and task.status != "done"],
                "tasks_overdue": [task for task in tasks if task.due_date and task.due_date < today and task.status != "done"],
                "tasks_in_progress": [task for task in tasks if task.status == "in_progress"],
            }
        )
    return response


async def dashboard_summary(session: AsyncSession, guardian: Guardian) -> list[dict]:
    from app.models.material import SchoolMaterial

    today = date.today()
    students = list((await session.scalars(select(Student).where(Student.family_id == guardian.family_id, Student.is_active.is_(True)).order_by(Student.name))).all())
    summary: list[dict] = []
    for student in students:
        tasks = list(
            (
                await session.scalars(
                    select(SchoolTask).where(SchoolTask.student_id == student.id, SchoolTask.deleted_at.is_(None))
                )
            ).all()
        )
        materials_count = await session.scalar(
            select(func.count(SchoolMaterial.id)).where(SchoolMaterial.student_id == student.id, SchoolMaterial.deleted_at.is_(None))
        ) or 0
        summary.append(
            {
                "student_id": student.id,
                "student_name": student.name,
                "total_tasks": len(tasks),
                "pending": sum(task.status == "pending" for task in tasks),
                "in_progress": sum(task.status == "in_progress" for task in tasks),
                "done": sum(task.status == "done" for task in tasks),
                "overdue": sum(bool(task.due_date and task.due_date < today and task.status != "done") for task in tasks),
                "materials_count": materials_count,
            }
        )
    return summary
