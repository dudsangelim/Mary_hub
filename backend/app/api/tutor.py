from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Response
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentGuardian, DbSession
from app.errors import error_response
from app.models.family import Student
from app.models.material import SchoolTask
from app.models.planning import StudySession
from app.models.profile import StudentProfile
from app.schemas.profile import SessionKind
from app.schemas.tutor import (
    SessionStep,
    TutorCompleteRequest,
    TutorMessageRequest,
    TutorMessageResponse,
    TutorNextRequest,
    TutorNextResponse,
    TutorSessionCreate,
    TutorSessionRead,
    TutorStatusResponse,
    TutorStuckRequest,
    TutorTTSRequest,
    TutorTTSResponse,
)
from app.services import planning_service, tts_service
from app.services.tts_service import audio_cache_key
from app.services.tutor_lucas_service import get_tutor_response

router = APIRouter(prefix="/tutor", tags=["tutor"])

WEEKDAY_MAP = {0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday", 4: "friday", 5: "saturday", 6: "sunday"}

_SP_TZ = ZoneInfo("America/Sao_Paulo")


async def _get_student(session: DbSession, family_id, student_id: UUID) -> Student:
    student = await session.scalar(
        select(Student)
        .where(Student.id == student_id, Student.family_id == family_id)
        .options(selectinload(Student.profile))
    )
    if student is None:
        raise error_response("STUDENT_NOT_FOUND", "Student not found", http_status=404)
    return student


async def _get_session_or_404(session: DbSession, family_id, session_id: UUID) -> StudySession:
    study_session = await session.scalar(
        select(StudySession)
        .join(Student, Student.id == StudySession.student_id)
        .where(StudySession.id == session_id, Student.family_id == family_id, StudySession.deleted_at.is_(None))
    )
    if study_session is None:
        raise error_response("SESSION_NOT_FOUND", "Session not found", http_status=404)
    return study_session


def _build_session_read(study_session: StudySession, student_name: str | None = None) -> TutorSessionRead:
    data = TutorSessionRead.model_validate(study_session)
    data.student_name = student_name
    return data


def _find_next_window(tutor_windows: dict, from_dt: datetime) -> tuple[datetime | None, datetime | None, str | None]:
    """Return (next_start, next_end, kind) scanning up to 7 days from from_dt (SP timezone)."""
    for day_offset in range(8):
        check_dt = from_dt + timedelta(days=day_offset)
        weekday = WEEKDAY_MAP[check_dt.weekday()]
        windows = tutor_windows.get(weekday, [])
        for w in windows:
            start_h, start_m = (int(x) for x in w["start"].split(":"))
            end_h, end_m = (int(x) for x in w["end"].split(":"))
            window_start = check_dt.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
            window_end = check_dt.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
            if window_start > from_dt:
                return window_start, window_end, w.get("kind")
    return None, None, None


@router.get("/status/{student_id}", response_model=TutorStatusResponse)
async def get_tutor_status(
    student_id: UUID,
    current_guardian: CurrentGuardian,
    session: DbSession,
) -> TutorStatusResponse:
    student = await _get_student(session, current_guardian.family_id, student_id)
    profile: StudentProfile | None = student.profile

    now_sp = datetime.now(_SP_TZ)
    weekday = WEEKDAY_MAP[now_sp.weekday()]
    tutor_windows: dict = (profile.tutor_windows or {}) if profile else {}
    windows_today = tutor_windows.get(weekday, [])

    # Check if inside any window right now
    for w in windows_today:
        start_h, start_m = (int(x) for x in w["start"].split(":"))
        end_h, end_m = (int(x) for x in w["end"].split(":"))
        window_start = now_sp.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
        window_end = now_sp.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
        if window_start <= now_sp <= window_end:
            existing = await session.scalar(
                select(StudySession).where(
                    StudySession.student_id == str(student_id),
                    StudySession.scheduled_date == now_sp.date(),
                    StudySession.deleted_at.is_(None),
                )
            )
            return TutorStatusResponse(
                available=True,
                reason="Janela ativa",
                next_window_start=window_start,
                next_window_end=window_end,
                session_type=w.get("kind"),
                existing_session_id=existing.id if existing else None,
            )

    # Not in a window — find next
    if not windows_today:
        reason = "Dia bloqueado"
    else:
        reason = "Fora da janela de tutoria"

    next_start, next_end, next_kind = _find_next_window(tutor_windows, now_sp)
    return TutorStatusResponse(
        available=False,
        reason=reason,
        next_window_start=next_start,
        next_window_end=next_end,
        session_type=next_kind,
        existing_session_id=None,
    )


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
    return _build_session_read(study_session, student.name)


@router.get("/sessions/{session_id}", response_model=TutorSessionRead)
async def get_session(
    session_id: UUID,
    current_guardian: CurrentGuardian,
    session: DbSession,
) -> TutorSessionRead:
    study_session = await _get_session_or_404(session, current_guardian.family_id, session_id)
    student_name: str | None = None
    if study_session.student_id:
        st = await session.scalar(select(Student).where(Student.id == study_session.student_id))
        if st:
            student_name = st.name
    return _build_session_read(study_session, student_name)


@router.post("/sessions/{session_id}/next", response_model=TutorNextResponse)
async def next_step(
    session_id: UUID,
    payload: TutorNextRequest,
    current_guardian: CurrentGuardian,
    session: DbSession,
) -> TutorNextResponse:
    study_session = await _get_session_or_404(session, current_guardian.family_id, session_id)

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


@router.post("/sessions/{session_id}/stuck")
async def report_stuck(
    session_id: UUID,
    payload: TutorStuckRequest,
    current_guardian: CurrentGuardian,
    session: DbSession,
) -> dict:
    study_session = await _get_session_or_404(session, current_guardian.family_id, session_id)

    runtime_state = dict(study_session.runtime_state or {})
    stuck_events: list = list(runtime_state.get("stuck_events", []))
    stuck_events.append({
        "step_id": payload.step_id,
        "reason": payload.reason,
        "at": datetime.now(UTC).isoformat(),
    })
    runtime_state["stuck_events"] = stuck_events
    study_session.runtime_state = runtime_state
    study_session.status = "stuck"

    await session.commit()
    return {"ok": True, "stuck_events": len(stuck_events)}


@router.post("/sessions/{session_id}/complete")
async def complete_session(
    session_id: UUID,
    payload: TutorCompleteRequest,
    current_guardian: CurrentGuardian,
    session: DbSession,
) -> dict:
    study_session = await _get_session_or_404(session, current_guardian.family_id, session_id)

    now = datetime.now(UTC)
    study_session.status = "completed"
    study_session.actual_end = now

    steps: list[dict] = list(study_session.steps or [])
    task_ids = [s["task_id"] for s in steps if s.get("kind") == "task" and s.get("done") and s.get("task_id")]

    runtime_state = dict(study_session.runtime_state or {})
    start_str = runtime_state.get("started_at")
    duration = None
    if start_str:
        start_dt = datetime.fromisoformat(start_str)
        duration = int((now - start_dt).total_seconds() / 60)

    study_session.outcome = {
        "completed_steps": sum(1 for s in steps if s.get("done")),
        "total_steps": len(steps),
        "tasks_done": task_ids,
        "duration_minutes": duration,
        "completion_notes": payload.completion_notes,
        "parent_feedback": payload.parent_feedback,
    }

    # Mark linked tasks as done if all task steps are complete
    done_step_task_ids = set(task_ids)
    if done_step_task_ids:
        all_task_ids_in_session = {s["task_id"] for s in steps if s.get("kind") == "task" and s.get("task_id")}
        if done_step_task_ids >= all_task_ids_in_session:
            for tid in all_task_ids_in_session:
                task = await session.scalar(select(SchoolTask).where(SchoolTask.id == tid))
                if task:
                    task.status = "done"

    await session.commit()
    return {"ok": True, "session_id": str(session_id), "status": "completed"}


@router.post("/sessions/{session_id}/message", response_model=TutorMessageResponse)
async def send_message(
    session_id: UUID,
    payload: TutorMessageRequest,
    current_guardian: CurrentGuardian,
    session: DbSession,
) -> TutorMessageResponse:
    study_session = await _get_session_or_404(session, current_guardian.family_id, session_id)

    student_name = "Lucas"
    if study_session.student_id:
        st = await session.scalar(select(Student).where(Student.id == study_session.student_id))
        if st:
            student_name = st.name

    llm_result = await get_tutor_response(payload.user_message, student_name)
    reply_text: str = llm_result.get("reply", "")
    suggested_next_action: str = llm_result.get("suggested_next_action", "continue")

    # Persist conversation turn in runtime_state
    runtime_state = dict(study_session.runtime_state or {})
    conversation: list = list(runtime_state.get("conversation", []))
    conversation.append({
        "step_id": payload.step_id,
        "user": payload.user_message,
        "reply": reply_text,
        "action": suggested_next_action,
        "at": datetime.now(UTC).isoformat(),
    })
    runtime_state["conversation"] = conversation
    runtime_state["last_activity_at"] = datetime.now(UTC).isoformat()
    study_session.runtime_state = runtime_state
    await session.commit()

    # Generate TTS
    reply_audio_url: str | None = None
    if reply_text:
        audio_bytes, _ = await tts_service.get_or_generate_tts(reply_text)
        if audio_bytes:
            key = audio_cache_key(reply_text)
            reply_audio_url = f"/tutor/tts/{key}"

    return TutorMessageResponse(
        reply_text=reply_text,
        reply_audio_url=reply_audio_url,
        suggested_next_action=suggested_next_action,
    )


@router.post("/tts", response_model=TutorTTSResponse)
async def request_tts(
    payload: TutorTTSRequest,
    current_guardian: CurrentGuardian,
) -> TutorTTSResponse:
    key = audio_cache_key(payload.text, payload.voice)
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
    if not data:
        raise error_response("AUDIO_NOT_FOUND", "Audio not found or expired", http_status=404)
    return Response(content=data, media_type="audio/mpeg")
