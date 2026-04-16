from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.profile import ClassBlock, FixedActivity, TutorWindow


class ScheduleRead(BaseModel):
    weekly_schedule: dict[str, list[ClassBlock]] = Field(default_factory=dict)
    fixed_activities: list[FixedActivity] = Field(default_factory=list)
    tutor_windows: dict[str, list[TutorWindow]] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class ScheduleUpdate(BaseModel):
    weekly_schedule: dict[str, list[ClassBlock]] | None = None
    fixed_activities: list[FixedActivity] | None = None
    tutor_windows: dict[str, list[TutorWindow]] | None = None
