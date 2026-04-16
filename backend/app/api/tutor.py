from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Response
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentGuardian, DbSession
from app.errors import error_response
from app.models.family import Student
from app.models.planning import StudySession
from app.models.profile import StudentProfile
from app.schemas.profile import SessionKind
from app.schemas.tutor import (
    SessionStep,
    TutorNextRequest,
    TutorNextResponse,
    TutorSessionCreate,
    TutorSessionRead,
    TutorTTSRequest,
    TutorTTSResponse,
)
from app.services import planning_service, tts_service
from app.services.tts_service import audio_cache_key

router = APIRouter(prefix="/tutor", tags=["tutor"])

WEEKDAY_MAP = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}


async def _get_student(session: DbSession, family_id, student_id: UUID) -> Student:
    student = await session.scalar(
        select(Student)
        .where(Student.id == student_id, Student.family_id == family_id)
        .options(selectinload(Student.profile))
    )
    if student is None:
        raise error_response("STUDENT_NOT_FOUND", "Student not found", http_status=404)
    return student


@router.post("/sessions", response_model=TutorSessionRead)
async def create_or_get_session(
    payload: TutorSessionCreate,
    current_guardian: CurrentGuardian,
    session: DbSession,
) -> TutorSessionRead:
    student = await _get_student(session, current_guardian.family_id, payload.student_id)
    profile: StudentProfile | None = student.profile

    session_kind = payload.session_kind.value
    if profile and profile.tutor_windows:
        weekday = WEEKDAY_MAP[payload.scheduled_date.weekday()]
        windows = profile.tutor_windows.get(weekday, [])
        if windows:
            session_kind = windows[0].get("kind", session_kind)

    study_session = await planning_service.get_or_create_tutor_session(
        session,
        payload.student_id,
        payload.scheduled_date,
        session_kind,
    )
    return TutorSessionRead.model_validate(study_session)


@router.get("/sessions/{session_id}", response_model=TutorSessionRead)
async def get_session(
    session_id: UUID,
    current_guardian: CurrentGuardian,
    session: DbSession,
) -> TutorSessionRead:
    study_session = await session.scalar(
        select(StudySession)
        .join(Student, Student.id == StudySession.student_id)
        .where(StudySession.id == session_id, Student.family_id == current_guardian.family_id, StudySession.deleted_at.is_(None))
    )
    if study_session is None:
        raise error_response("SESSION_NOT_FOUND", "Session not found", http_status=404)
    return TutorSessionRead.model_validate(study_session)


@router.post("/sessions/{session_id}/next", response_model=TutorNextResponse)
async def next_step(
    session_id: UUID,
    payload: TutorNextRequest,
    current_guardian: CurrentGuardian,
    session: DbSession,
) -> TutorNextResponse:
    study_session = await session.scalar(
        select(StudySession)
        .join(Student, Student.id == StudySession.student_id)
        .where(StudySession.id == session_id, Student.family_id == current_guardian.family_id, StudySession.deleted_at.is_(None))
    )
    if study_session is None:
        raise error_response("SESSION_NOT_FOUND", "Session not found", http_status=404)

    study_session = await planning_service.advance_session_step(
        session,
        study_session,
        payload.step_index,
        payload.mark_done,
    )

    steps = study_session.steps
    next_idx = (study_session.runtime_state or {}).get("current_step", 0)

    if next_idx >= len(steps):
        return TutorNextResponse(
            session_id=session_id,
            step=None,
            is_last=True,
            message="Sessão concluída! Parabéns!",
        )

    raw = steps[next_idx]
    step = SessionStep(**raw)
    is_last = next_idx >= len(steps) - 1
    return TutorNextResponse(session_id=session_id, step=step, is_last=is_last)


@router.post("/tts", response_model=TutorTTSResponse)
async def request_tts(
    payload: TutorTTSRequest,
    current_guardian: CurrentGuardian,
) -> TutorTTSResponse:
    key = audio_cache_key(payload.text, payload.voice)
    # Pre-generate and cache
    _, cached = await tts_service.get_or_generate_tts(payload.text, payload.voice)
    return TutorTTSResponse(audio_key=key, cached=cached)


@router.get("/tts/{audio_key}")
async def stream_tts(
    audio_key: str,
    current_guardian: CurrentGuardian,
) -> Response:
    from app.redis import redis_client
    full_key = f"tts:audio:{audio_key}" if not audio_key.startswith("tts:audio:") else audio_key
    data = await redis_client.get(full_key)
    if data is None:
        raise error_response("AUDIO_NOT_FOUND", "Audio not found or expired", http_status=404)
    return Response(content=data, media_type="audio/mpeg")
