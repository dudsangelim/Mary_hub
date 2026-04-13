from __future__ import annotations

from datetime import date
from typing import Protocol
from uuid import UUID


class IReportingService(Protocol):
    async def generate_weekly_summary(self, student_id: UUID): ...
    async def generate_progress_report(self, student_id: UUID, period: tuple[date, date]): ...
    async def generate_alert(self, student_id: UUID, alert_type: str): ...
