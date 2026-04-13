from __future__ import annotations

from fastapi import APIRouter

from app.deps import CurrentGuardian, DbSession
from app.models.family import Family
from app.schemas.family import FamilyRead, FamilyUpdate

router = APIRouter(prefix="/families", tags=["families"])


@router.get("/me", response_model=FamilyRead)
async def get_family(current_guardian: CurrentGuardian, session: DbSession) -> FamilyRead:
    family = await session.get(Family, current_guardian.family_id)
    await session.refresh(family, attribute_names=["guardians"])
    return FamilyRead.model_validate(family)


@router.put("/me", response_model=FamilyRead)
async def update_family(payload: FamilyUpdate, current_guardian: CurrentGuardian, session: DbSession) -> FamilyRead:
    family = await session.get(Family, current_guardian.family_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(family, field, value)
    await session.commit()
    await session.refresh(family, attribute_names=["guardians"])
    return FamilyRead.model_validate(family)
