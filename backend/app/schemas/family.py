from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class GuardianRead(ORMModel):
    id: UUID
    name: str
    email: str
    role: str
    is_primary: bool
    is_active: bool


class FamilyRead(ORMModel):
    id: UUID
    name: str
    timezone: str
    settings: dict
    is_active: bool
    guardians: list[GuardianRead] = []


class FamilyUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    timezone: str | None = Field(default=None, max_length=50)
    settings: dict | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    guardian: GuardianRead
    family_id: UUID
    tokens: TokenPair


class RefreshRequest(BaseModel):
    refresh_token: str
