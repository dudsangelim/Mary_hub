"""
classification_service.py — AI classification of school tasks using Claude via OpenRouter.

Implements IClassificationService from app/interfaces/classification.py.

For each task it:
  1. Fetches curriculum items for the student's grade (filtered by subject when available)
  2. Calls Claude (via OpenRouter) to match the task to a curriculum item
  3. Returns difficulty, estimated_minutes, confidence, and reasoning
  4. Upserts a ClassifiedTask record

Graceful degradation: if OPENROUTER_API_KEY is not configured, classification
is skipped and the function returns None without raising an error.
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.curriculum import CurriculumItem, Subject
from app.models.family import Student
from app.models.material import ClassifiedTask, SchoolTask

logger = logging.getLogger(__name__)

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

_CLASSIFY_SYSTEM = """You are an educational task classifier for Brazilian elementary and middle school.
Given a school homework task and a list of curriculum items, you identify the best matching curriculum item
and assess the task's difficulty and estimated completion time.

Always respond with valid JSON only — no prose, no markdown, no code fences.
"""

_CLASSIFY_PROMPT = """Task to classify:
Title: {title}
Description: {description}
Subject: {subject}
Grade: {grade_label}

Available curriculum items for this grade:
{curriculum_items_json}

Instructions:
- Choose the BEST matching curriculum_item_id from the list above (use the "id" field).
- If none of the items is a reasonable match, set curriculum_item_id to null.
- Assess difficulty: "easy", "normal", or "hard" relative to the grade level.
- Estimate how many minutes a typical student at this grade would need to complete this task.
- Set confidence between 0.0 (no match) and 1.0 (perfect match).
- Keep reasoning to one sentence in Portuguese.

Respond with JSON in this exact shape:
{{
  "curriculum_item_id": "<uuid or null>",
  "difficulty": "easy|normal|hard",
  "estimated_minutes": <integer>,
  "confidence": <float 0.0-1.0>,
  "reasoning": "<one sentence in Portuguese>"
}}"""


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, stripping markdown code blocks if present."""
    text = text.strip()
    # Strip ```json ... ``` or ``` ... ```
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop first and last lines (``` fences)
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(text.strip())


async def _call_llm(prompt: str) -> dict | None:
    """Call OpenRouter LLM. Returns parsed JSON dict or None on failure."""
    if not settings.openrouter_api_key:
        logger.warning("classification_service: OPENROUTER_API_KEY not configured — skipping")
        return None

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            _OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://mary-education-hub.local",
                "X-Title": "Mary Education Hub",
            },
            json={
                "model": settings.openrouter_model,
                "messages": [
                    {"role": "system", "content": _CLASSIFY_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 400,
            },
        )
        if response.status_code != 200:
            logger.error(
                "classification_service: OpenRouter returned %d: %s",
                response.status_code,
                response.text[:300],
            )
            return None
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return _extract_json(content)


async def _get_curriculum_items(session: AsyncSession, grade: str, subject_id: UUID | None) -> list[CurriculumItem]:
    """Fetch curriculum items for the given grade, optionally filtered by subject."""
    query = (
        select(CurriculumItem)
        .join(Subject, Subject.id == CurriculumItem.subject_id)
        .where(Subject.grade == grade, Subject.is_active.is_(True))
        .order_by(Subject.name, CurriculumItem.order_index)
    )
    if subject_id:
        query = query.where(CurriculumItem.subject_id == subject_id)
    return list((await session.scalars(query)).all())


async def classify_task(
    session: AsyncSession,
    task: SchoolTask,
    student: Student,
) -> ClassifiedTask | None:
    """Classify a single task and upsert a ClassifiedTask record.

    Returns the ClassifiedTask on success, None if classification is skipped
    (e.g. no API key, no curriculum items) or already classified.
    """
    # Skip if already classified
    existing = await session.scalar(
        select(ClassifiedTask).where(ClassifiedTask.task_id == task.id)
    )
    if existing and existing.classification_method not in (None, ""):
        logger.debug("Task %s already classified — skipping", task.id)
        return existing

    curriculum_items = await _get_curriculum_items(session, student.grade, task.subject_id)
    if not curriculum_items:
        logger.info("No curriculum items for grade=%s — skipping task %s", student.grade, task.id)
        return None

    # Get subject name for context
    subject_name = ""
    if task.subject_id:
        subject = await session.scalar(select(Subject).where(Subject.id == task.subject_id))
        subject_name = subject.name if subject else ""

    curriculum_items_data = [
        {
            "id": str(ci.id),
            "title": ci.title,
            "description": ci.description or "",
            "difficulty_level": ci.difficulty_level,
        }
        for ci in curriculum_items
    ]

    prompt = _CLASSIFY_PROMPT.format(
        title=task.title,
        description=task.description or "(sem descrição)",
        subject=subject_name or "(não especificada)",
        grade_label=student.grade_label,
        curriculum_items_json=json.dumps(curriculum_items_data, ensure_ascii=False, indent=2),
    )

    try:
        result = await _call_llm(prompt)
    except httpx.HTTPStatusError as exc:
        logger.error("LLM HTTP error for task %s: %s", task.id, exc)
        return None
    except Exception as exc:
        logger.error("LLM call failed for task %s: %s", task.id, exc)
        return None

    if result is None:
        return None

    # Validate curriculum_item_id
    curriculum_item_id: UUID | None = None
    raw_ci_id = result.get("curriculum_item_id")
    if raw_ci_id:
        valid_ids = {str(ci.id) for ci in curriculum_items}
        if raw_ci_id in valid_ids:
            curriculum_item_id = UUID(raw_ci_id)
        else:
            logger.warning("LLM returned unknown curriculum_item_id=%s for task %s", raw_ci_id, task.id)

    difficulty = result.get("difficulty", "normal")
    if difficulty not in ("easy", "normal", "hard"):
        difficulty = "normal"

    estimated_minutes = result.get("estimated_minutes")
    if not isinstance(estimated_minutes, int) or estimated_minutes <= 0:
        estimated_minutes = None

    confidence = result.get("confidence")
    if not isinstance(confidence, float) or not (0.0 <= confidence <= 1.0):
        confidence = None

    reasoning = result.get("reasoning", "")

    now = datetime.now(UTC)

    if existing is None:
        classified = ClassifiedTask(
            task_id=task.id,
            curriculum_item_id=curriculum_item_id,
            difficulty_assessed=difficulty,
            estimated_duration=estimated_minutes,
            classification_confidence=confidence,
            classification_method="ai_v1",
            classification_metadata={"model": settings.openrouter_model, "reasoning": reasoning},
            classified_at=now,
            classified_by="system",
        )
        session.add(classified)
    else:
        existing.curriculum_item_id = curriculum_item_id
        existing.difficulty_assessed = difficulty
        existing.estimated_duration = estimated_minutes
        existing.classification_confidence = confidence
        existing.classification_method = "ai_v1"
        existing.classification_metadata = {"model": settings.openrouter_model, "reasoning": reasoning}
        existing.classified_at = now
        existing.classified_by = "system"
        classified = existing

    await session.commit()
    await session.refresh(classified)
    logger.info(
        "Classified task %s → ci=%s difficulty=%s conf=%.2f",
        task.id, curriculum_item_id, difficulty, confidence or 0.0,
    )
    return classified


async def classify_pending_tasks(
    session: AsyncSession,
    guardian_family_id: UUID,
) -> dict:
    """Classify all unclassified tasks for a family. Returns summary counts."""
    unclassified_tasks = list(
        (
            await session.scalars(
                select(SchoolTask)
                .join(Student, Student.id == SchoolTask.student_id)
                .where(
                    Student.family_id == guardian_family_id,
                    SchoolTask.deleted_at.is_(None),
                )
                .outerjoin(ClassifiedTask, ClassifiedTask.task_id == SchoolTask.id)
                .where(
                    (ClassifiedTask.id.is_(None)) | (ClassifiedTask.classification_method.is_(None))
                )
            )
        ).all()
    )

    classified_count = 0
    skipped_count = 0
    failed_count = 0

    for task in unclassified_tasks:
        student = await session.scalar(select(Student).where(Student.id == task.student_id))
        if student is None:
            skipped_count += 1
            continue
        try:
            result = await classify_task(session, task, student)
            if result is not None:
                classified_count += 1
            else:
                skipped_count += 1
        except Exception as exc:
            logger.error("Failed to classify task %s: %s", task.id, exc)
            failed_count += 1

    return {
        "total": len(unclassified_tasks),
        "classified": classified_count,
        "skipped": skipped_count,
        "failed": failed_count,
    }
