from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int


class ErrorEnvelope(BaseModel):
    error: dict


__all__ = ["ORMModel", "PaginatedResponse", "ErrorEnvelope", "UUID", "date", "datetime", "time"]
