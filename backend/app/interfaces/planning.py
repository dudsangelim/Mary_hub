from __future__ import annotations

from datetime import date
from typing import Protocol
from uuid import UUID


class IPlanningService(Protocol):
    async def generate_daily_plan(self, student_id: UUID, date: date): ...
    async def generate_weekly_plan(self, student_id: UUID, week_start: date): ...
    async def adjust_plan(self, plan_id: UUID, adjustments: dict): ...
