from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.errors import error_response
from app.models.curriculum import Subject
from app.models.family import Student
from app.models.material import SchoolTask
from app.models.planning import StudyPlan, StudySession
from app.models.profile import StudentProfile
from app.schemas.profile import SessionKind


WEEKDAY_MAP = {
    0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday", 4: "friday", 5: "saturday", 6: "sunday"
}


def _is_in_tutor_window(target_date: date, tutor_windows: dict) -> bool:
    weekday = WEEKDAY_MAP[target_date.weekday()]
    return bool(tutor_windows.get(weekday))


def _get_session_kind(target_date: date, tutor_windows: dict) -> str:
    weekday = WEEKDAY_MAP[target_date.weekday()]
    windows = tutor_windows.get(weekday, [])
    if windows:
        return windows[0].get("kind", "homework")
    return "homework"


async def get_or_create_daily_plan(
    session: AsyncSession,
    student_id: UUID,
    target_date: date,
) -> StudyPlan:
    title = f"Plano diário {target_date.isoformat()}"
    plan = await session.scalar(
        select(StudyPlan).where(
            StudyPlan.student_id == str(student_id),
            StudyPlan.start_date == target_date,
            StudyPlan.plan_type == "daily",
            StudyPlan.deleted_at.is_(None),
        )
    )
    if plan is None:
        plan = StudyPlan(
            student_id=str(student_id),
            title=title,
            plan_type="daily",
            start_date=target_date,
            end_date=target_date,
            status="active",
            generated_by="session_engine",
            plan_metadata={},
        )
        session.add(plan)
        await session.flush()
    return plan


async def build_session_steps(
    session: AsyncSession,
    student_id: UUID,
    target_date: date,
    session_kind: str,
) -> list[dict]:
    tasks = list(
        (
            await session.scalars(
                select(SchoolTask)
                .where(
                    SchoolTask.student_id == str(student_id),
                    SchoolTask.due_date == target_date,
                    SchoolTask.status != "done",
                    SchoolTask.deleted_at.is_(None),
                )
                .options(selectinload(SchoolTask.subject))
                .order_by(SchoolTask.created_at.asc())
            )
        ).all()
    )

    steps: list[dict] = []
    steps.append({
        "index": 0,
        "kind": "intro",
        "task_id": None,
        "task_title": None,
        "subject": None,
        "pages": None,
        "book_reference": None,
        "instruction": _build_intro_instruction(session_kind, len(tasks)),
        "audio_key": None,
        "done": False,
    })

    for i, task in enumerate(tasks):
        subject_name = task.subject.name if task.subject else None
        steps.append({
            "index": i + 1,
            "kind": "task",
            "task_id": str(task.id),
            "task_title": task.title,
            "subject": subject_name,
            "pages": task.pages,
            "book_reference": task.book_reference,
            "instruction": _build_task_instruction(task, subject_name),
            "audio_key": None,
            "done": False,
        })

    steps.append({
        "index": len(steps),
        "kind": "celebration",
        "task_id": None,
        "task_title": None,
        "subject": None,
        "pages": None,
        "book_reference": None,
        "instruction": "Parabéns! Você terminou todas as tarefas de hoje! 🎉",
        "audio_key": None,
        "done": False,
    })

    return steps


def _build_intro_instruction(session_kind: str, task_count: int) -> str:
    kind_labels = {
        "homework": "tarefas de casa",
        "review": "revisão",
        "light": "atividades leves",
        "weekly_prep": "preparação da semana",
        "reading": "leitura",
        "free": "tempo livre",
    }
    label = kind_labels.get(session_kind, "tarefas")
    if task_count == 0:
        return f"Olá! Não há {label} para hoje. Que tal revisar algo que você aprendeu?"
    return f"Olá! Temos {task_count} {'tarefa' if task_count == 1 else 'tarefas'} de {label} para hoje. Vamos começar!"


def _build_task_instruction(task: SchoolTask, subject_name: str | None) -> str:
    parts = []
    if subject_name:
        parts.append(f"Matéria: {subject_name}.")
    parts.append(f"Tarefa: {task.title}.")
    if task.pages:
        parts.append(f"Páginas: {task.pages}.")
    if task.book_reference:
        parts.append(f"Livro: {task.book_reference}.")
    if task.description:
        parts.append(task.description)
    return " ".join(parts)


async def get_or_create_tutor_session(
    session: AsyncSession,
    student_id: UUID,
    target_date: date,
    session_kind: str,
) -> StudySession:
    plan = await get_or_create_daily_plan(session, student_id, target_date)
    await session.flush()

    study_session = await session.scalar(
        select(StudySession).where(
            StudySession.student_id == str(student_id),
            StudySession.scheduled_date == target_date,
            StudySession.session_kind == session_kind,
            StudySession.deleted_at.is_(None),
        )
    )

    if study_session is None:
        steps = await build_session_steps(session, student_id, target_date, session_kind)
        study_session = StudySession(
            plan_id=str(plan.id),
            student_id=str(student_id),
            title=f"Sessão {session_kind} — {target_date.isoformat()}",
            scheduled_date=target_date,
            session_kind=session_kind,
            status="scheduled",
            runtime_state={"current_step": 0},
            steps=steps,
            outcome={},
        )
        session.add(study_session)
        await session.flush()

    return study_session


async def advance_session_step(
    session: AsyncSession,
    study_session: StudySession,
    step_index: int,
    mark_done: bool,
) -> StudySession:
    steps: list[dict] = list(study_session.steps)

    if mark_done and 0 <= step_index < len(steps):
        steps[step_index] = {**steps[step_index], "done": True}

    next_index = step_index + 1
    runtime_state = dict(study_session.runtime_state or {})
    runtime_state["current_step"] = next_index
    if runtime_state.get("started_at") is None:
        runtime_state["started_at"] = datetime.now(UTC).isoformat()
    runtime_state["last_activity_at"] = datetime.now(UTC).isoformat()

    study_session.steps = steps
    study_session.runtime_state = runtime_state

    completed = sum(1 for s in steps if s.get("done"))
    if completed >= len(steps) - 1:  # all except celebration
        study_session.status = "done"
        start_str = runtime_state.get("started_at")
        duration = None
        if start_str:
            start_dt = datetime.fromisoformat(start_str)
            duration = int((datetime.now(UTC) - start_dt).total_seconds() / 60)
        task_ids = [s["task_id"] for s in steps if s.get("kind") == "task" and s.get("done") and s.get("task_id")]
        study_session.outcome = {
            "completed_steps": completed,
            "total_steps": len(steps),
            "tasks_done": task_ids,
            "duration_minutes": duration,
        }

    await session.commit()
    await session.refresh(study_session)
    return study_session
