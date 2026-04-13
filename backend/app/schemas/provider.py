from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel, datetime


class ProviderAccountRead(ORMModel):
    id: UUID
    student_id: UUID
    provider_name: str
    provider_type: str
    is_active: bool
    last_sync_at: datetime | None
    sync_config: dict
    created_at: datetime
    updated_at: datetime
    has_credentials: bool = False


class ProviderSyncLogRead(ORMModel):
    id: UUID
    provider_account_id: UUID
    sync_type: str
    status: str
    items_found: int
    items_synced: int
    items_failed: int
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
    sync_metadata: dict
    created_at: datetime
    updated_at: datetime


class PlurallAccountUpsert(BaseModel):
    student_id: UUID
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)
    student_login_id: str | None = Field(default=None, max_length=100)
    link_code: str | None = Field(default=None, max_length=100)
    is_active: bool = True


class ProviderSyncTriggerResponse(BaseModel):
    provider_account: ProviderAccountRead
    sync_log: ProviderSyncLogRead
    message: str
