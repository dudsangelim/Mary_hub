from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, File, Form, Query, Response, UploadFile, status

from app.deps import CurrentGuardian, DbSession
from app.models.material import SchoolMaterial
from app.schemas.material import MaterialCreate, MaterialRead, MaterialUpdate
from app.services.material_service import (
    create_text_material,
    get_material,
    get_student_for_family,
    list_materials,
    soft_delete_material,
    update_material,
    validate_subject_for_grade,
)
from app.services.upload_service import save_upload_file

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("", response_model=dict)
async def get_materials(
    session: DbSession,
    current_guardian: CurrentGuardian,
    student_id: UUID | None = Query(default=None),
    subject_id: UUID | None = Query(default=None),
    material_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> dict:
    items, total = await list_materials(session, current_guardian, student_id, subject_id, material_type, page, per_page)
    return {"items": [MaterialRead.model_validate(item).model_dump(mode="json") for item in items], "total": total, "page": page, "per_page": per_page}


@router.get("/{material_id}", response_model=MaterialRead)
async def get_material_detail(material_id: UUID, session: DbSession, current_guardian: CurrentGuardian) -> MaterialRead:
    return MaterialRead.model_validate(await get_material(session, current_guardian, material_id))


@router.post("", response_model=MaterialRead, status_code=status.HTTP_201_CREATED)
async def create_material(payload: MaterialCreate, session: DbSession, current_guardian: CurrentGuardian) -> MaterialRead:
    material = await create_text_material(session, current_guardian, payload)
    return MaterialRead.model_validate(material)


@router.post("/upload", response_model=MaterialRead, status_code=status.HTTP_201_CREATED)
async def upload_material(
    session: DbSession,
    current_guardian: CurrentGuardian,
    file: UploadFile = File(...),
    student_id: UUID = Form(...),
    title: str = Form(...),
    subject_id: UUID | None = Form(default=None),
    description: str | None = Form(default=None),
) -> MaterialRead:
    student = await get_student_for_family(session, current_guardian.family_id, student_id)
    await validate_subject_for_grade(session, student.grade, subject_id)
    stored_path, size = await save_upload_file(file, str(current_guardian.family_id), str(student_id))
    material = SchoolMaterial(
        student_id=student_id,
        uploaded_by=current_guardian.id,
        title=title,
        description=description,
        subject_id=subject_id,
        material_type="pdf" if file.content_type == "application/pdf" else "image",
        file_path=stored_path,
        file_name=file.filename,
        file_size_bytes=size,
        mime_type=file.content_type,
        source="manual_upload",
    )
    session.add(material)
    await session.commit()
    await session.refresh(material)
    return MaterialRead.model_validate(material)


@router.put("/{material_id}", response_model=MaterialRead)
async def update_material_detail(material_id: UUID, payload: MaterialUpdate, session: DbSession, current_guardian: CurrentGuardian) -> MaterialRead:
    return MaterialRead.model_validate(await update_material(session, current_guardian, material_id, payload))


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(material_id: UUID, session: DbSession, current_guardian: CurrentGuardian) -> Response:
    await soft_delete_material(session, current_guardian, material_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
