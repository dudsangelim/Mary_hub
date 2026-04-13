from __future__ import annotations

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
)
from app.services.task_service import build_openclaw_student_context, import_agenda_tasks

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
