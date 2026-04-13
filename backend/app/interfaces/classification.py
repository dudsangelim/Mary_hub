from __future__ import annotations

from typing import Protocol
from uuid import UUID


class IClassificationService(Protocol):
    async def classify_material(self, material_id: UUID): ...
    async def classify_task(self, task_id: UUID): ...
    async def suggest_subject(self, text: str, grade: str): ...
