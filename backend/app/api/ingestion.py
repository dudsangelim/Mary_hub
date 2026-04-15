from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, status
from sqlalchemy import select

from app.config import settings
from app.deps import DbSession
from app.errors import error_response
from app.models.family import Guardian
from app.schemas.task import (
    AgendaTaskImportRequest,
    OpenClawAgendaIngestRequest,
    OpenClawAgendaIngestResponse,
    DashboardTodayResponse,
)
from app.services.task_service import (
    build_openclaw_student_context,
    import_agenda_tasks,
    dashboard_today,
    update_task_status,
)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


async def get_default_guardian(session: DbSession) -> Guardian:
    guardian = await session.scalar(select(Guardian).where(Guardian.is_primary.is_(True), Guardian.is_active.is_(True)).order_by(Guardian.created_at.asc()))
    if guardian is None:
        raise error_response("GUARDIAN_NOT_FOUND", "No active primary guardian configured", http_status=404)
    return guardian


@router.post("/openclaw/agenda", response_model=OpenClawAgendaIngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_openclaw_agenda(
    payload: OpenClawAgendaIngestRequest,
    session: DbSession,
    x_openclaw_secret: str | None = Header(default=None),
) -> OpenClawAgendaIngestResponse:
    if not settings.openclaw_ingest_secret:
        raise error_response(
            "OPENCLAW_INGEST_NOT_CONFIGURED",
            "OPENCLAW_INGEST_SECRET is not configured",
            http_status=503,
        )
    if x_openclaw_secret != settings.openclaw_ingest_secret:
        raise error_response("OPENCLAW_INGEST_FORBIDDEN", "Invalid OpenClaw ingest secret", http_status=403)

    guardian = await get_default_guardian(session)
    imported_tasks, created, updated, skipped = await import_agenda_tasks(
        session,
        guardian,
        AgendaTaskImportRequest(
            student_id=payload.student_id,
            source_app=payload.source_channel,
            screenshot_date=payload.screenshot_date,
            items=payload.items,
        ),
    )
    context = await build_openclaw_student_context(session, guardian, payload.student_id, imported_tasks)

    return OpenClawAgendaIngestResponse(
        created=created,
        updated=updated,
        skipped=skipped,
        student_id=context["student_id"],
        student_name=context["student_name"],
        pending_tasks_count=context["pending_tasks_count"],
        agenda_task_ids=context["agenda_task_ids"],
        linked_subjects=context["linked_subjects"],
        library_context_titles=context["library_context_titles"],
        message=(
            "Agenda recebida do OpenClaw. O Mary atualizou as tarefas do aluno e devolveu "
            "o contexto de biblioteca e disciplinas para tutorias e notificacoes futuras."
        ),
    )


def _require_openclaw_secret(x_openclaw_secret: str | None) -> None:
    if not settings.openclaw_ingest_secret:
        raise error_response("OPENCLAW_INGEST_NOT_CONFIGURED", "OPENCLAW_INGEST_SECRET is not configured", http_status=503)
    if x_openclaw_secret != settings.openclaw_ingest_secret:
        raise error_response("OPENCLAW_INGEST_FORBIDDEN", "Invalid OpenClaw ingest secret", http_status=403)


@router.get("/openclaw/summary")
async def openclaw_summary(
    session: DbSession,
    x_openclaw_secret: str | None = Header(default=None),
) -> dict:
    """Returns today's educational task summary for all active students.
    Authenticated via X-OpenClaw-Secret header (same mechanism as agenda ingest).
    Intended for OpenClaw briefing and skill consumers.
    """
    _require_openclaw_secret(x_openclaw_secret)
    guardian = await get_default_guardian(session)
    students_data = await dashboard_today(session, guardian)

    def _slim_task(t) -> dict:
        return {
            "id": str(t.id),
            "title": t.title,
            "subject_id": str(t.subject_id) if t.subject_id else None,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "status": t.status,
            "priority": t.priority,
            "task_type": t.task_type,
        }

    result = []
    for s in students_data:
        result.append({
            "student_id": str(s["student_id"]),
            "student_name": s["student_name"],
            "avatar_color": s["avatar_color"],
            "tasks_due_today": [_slim_task(t) for t in s["tasks_due_today"]],
            "tasks_overdue": [_slim_task(t) for t in s["tasks_overdue"]],
            "tasks_in_progress": [_slim_task(t) for t in s["tasks_in_progress"]],
            "overdue_count": len(s["tasks_overdue"]),
            "due_today_count": len(s["tasks_due_today"]),
            "in_progress_count": len(s["tasks_in_progress"]),
        })

    from datetime import date
    return {"date": date.today().isoformat(), "students": result}


@router.patch("/openclaw/tasks/{task_id}/status", status_code=status.HTTP_200_OK)
async def openclaw_update_task_status(
    task_id: UUID,
    session: DbSession,
    x_openclaw_secret: str | None = Header(default=None),
    new_status: str = "done",
) -> dict:
    """Updates the status of a task (e.g. mark as done).
    Authenticated via X-OpenClaw-Secret header.
    Query param: new_status (default: done). Allowed: pending, in_progress, done.
    """
    _require_openclaw_secret(x_openclaw_secret)
    if new_status not in {"pending", "in_progress", "done"}:
        raise error_response("INVALID_STATUS", f"Status '{new_status}' is not allowed. Use: pending, in_progress, done", http_status=400)
    guardian = await get_default_guardian(session)
    task = await update_task_status(session, guardian, task_id, new_status)
    return {
        "ok": True,
        "task_id": str(task.id),
        "title": task.title,
        "status": task.status,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }
