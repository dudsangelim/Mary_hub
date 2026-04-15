from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from sqlalchemy import select

from app.deps import CurrentGuardian, DbSession
from app.models.family import Student
from app.schemas.task import AgendaTaskImportRequest, AgendaTaskImportResponse, TaskCreate, TaskRead, TaskStatusUpdate, TaskUpdate
from app.services.classification_service import classify_pending_tasks, classify_task
from app.services.task_service import (
    create_task,
    get_task,
    import_agenda_tasks,
    list_tasks,
    soft_delete_task,
    update_task,
    update_task_status,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=dict)
async def get_tasks(
    session: DbSession,
    current_guardian: CurrentGuardian,
    student_id: UUID | None = Query(default=None),
    subject_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    due_date_from: date | None = Query(default=None),
    due_date_to: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> dict:
    items, total = await list_tasks(session, current_guardian, student_id, subject_id, status_filter, due_date_from, due_date_to, page, per_page)
    return {"items": [TaskRead.model_validate(item).model_dump(mode="json") for item in items], "total": total, "page": page, "per_page": per_page}


@router.get("/{task_id}", response_model=TaskRead)
async def get_task_detail(task_id: UUID, session: DbSession, current_guardian: CurrentGuardian) -> TaskRead:
    return TaskRead.model_validate(await get_task(session, current_guardian, task_id))


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task_item(payload: TaskCreate, session: DbSession, current_guardian: CurrentGuardian) -> TaskRead:
    return TaskRead.model_validate(await create_task(session, current_guardian, payload))


@router.post("/import-agenda", response_model=AgendaTaskImportResponse)
async def import_task_agenda(payload: AgendaTaskImportRequest, session: DbSession, current_guardian: CurrentGuardian) -> AgendaTaskImportResponse:
    tasks, created, updated, skipped = await import_agenda_tasks(session, current_guardian, payload)
    return AgendaTaskImportResponse(
        created=created,
        updated=updated,
        skipped=skipped,
        tasks=[TaskRead.model_validate(task) for task in tasks],
    )


@router.put("/{task_id}", response_model=TaskRead)
async def update_task_item(task_id: UUID, payload: TaskUpdate, session: DbSession, current_guardian: CurrentGuardian) -> TaskRead:
    return TaskRead.model_validate(await update_task(session, current_guardian, task_id, payload))


@router.patch("/{task_id}/status", response_model=TaskRead)
async def patch_task_status(task_id: UUID, payload: TaskStatusUpdate, session: DbSession, current_guardian: CurrentGuardian) -> TaskRead:
    return TaskRead.model_validate(await update_task_status(session, current_guardian, task_id, payload.status))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: UUID, session: DbSession, current_guardian: CurrentGuardian) -> Response:
    await soft_delete_task(session, current_guardian, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{task_id}/classify", status_code=status.HTTP_200_OK)
async def classify_task_endpoint(task_id: UUID, session: DbSession, current_guardian: CurrentGuardian) -> dict:
    """Classify a task using AI (Claude via OpenRouter). Creates or updates a ClassifiedTask record."""
    task = await get_task(session, current_guardian, task_id)
    student = await session.scalar(select(Student).where(Student.id == task.student_id))
    if student is None:
        from app.errors import error_response
        raise error_response("STUDENT_NOT_FOUND", "Student not found for this task", http_status=404)
    classified = await classify_task(session, task, student)
    if classified is None:
        return {"ok": False, "message": "Classification skipped (no API key or no curriculum items for this grade)"}
    return {
        "ok": True,
        "task_id": str(task.id),
        "curriculum_item_id": str(classified.curriculum_item_id) if classified.curriculum_item_id else None,
        "difficulty_assessed": classified.difficulty_assessed,
        "estimated_duration": classified.estimated_duration,
        "classification_confidence": classified.classification_confidence,
        "reasoning": (classified.classification_metadata or {}).get("reasoning", ""),
        "classified_at": classified.classified_at.isoformat() if classified.classified_at else None,
    }


@router.post("/classify-pending", status_code=status.HTTP_200_OK)
async def classify_all_pending(session: DbSession, current_guardian: CurrentGuardian) -> dict:
    """Batch classify all unclassified tasks for this family."""
    result = await classify_pending_tasks(session, current_guardian.family_id)
    return {
        "ok": True,
        "message": f"Classified {result['classified']} of {result['total']} tasks",
        **result,
    }
