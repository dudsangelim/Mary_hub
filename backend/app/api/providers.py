from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.deps import CurrentGuardian, DbSession
from app.schemas.provider import (
    PlurallAccountUpsert,
    ProviderAccountRead,
    ProviderSyncLogRead,
    ProviderSyncTriggerResponse,
)
from app.services.provider_service import (
    list_provider_accounts,
    list_provider_sync_logs,
    trigger_plurall_sync,
    upsert_plurall_account,
)

router = APIRouter(prefix="/providers", tags=["providers"])


def serialize_provider_account(account) -> ProviderAccountRead:
    return ProviderAccountRead(
        id=account.id,
        student_id=account.student_id,
        provider_name=account.provider_name,
        provider_type=account.provider_type,
        is_active=account.is_active,
        last_sync_at=account.last_sync_at,
        sync_config=account.sync_config or {},
        created_at=account.created_at,
        updated_at=account.updated_at,
        has_credentials=bool(account.credentials_encrypted),
    )


def serialize_provider_sync_log(log) -> ProviderSyncLogRead:
    return ProviderSyncLogRead(
        id=log.id,
        provider_account_id=log.provider_account_id,
        sync_type=log.sync_type,
        status=log.status,
        items_found=log.items_found,
        items_synced=log.items_synced,
        items_failed=log.items_failed,
        error_message=log.error_message,
        started_at=log.started_at,
        completed_at=log.completed_at,
        sync_metadata=log.sync_metadata or {},
        created_at=log.created_at,
        updated_at=log.updated_at,
    )


@router.get("/accounts", response_model=list[ProviderAccountRead])
async def get_provider_accounts(current_guardian: CurrentGuardian, session: DbSession) -> list[ProviderAccountRead]:
    accounts = await list_provider_accounts(session, current_guardian)
    return [serialize_provider_account(account) for account in accounts]


@router.post("/plurall/accounts", response_model=ProviderAccountRead, status_code=status.HTTP_201_CREATED)
async def create_or_update_plurall_account(
    payload: PlurallAccountUpsert,
    current_guardian: CurrentGuardian,
    session: DbSession,
) -> ProviderAccountRead:
    account = await upsert_plurall_account(session, current_guardian, payload)
    return serialize_provider_account(account)


@router.get("/accounts/{account_id}/logs", response_model=list[ProviderSyncLogRead])
async def get_provider_logs(
    account_id: UUID,
    current_guardian: CurrentGuardian,
    session: DbSession,
) -> list[ProviderSyncLogRead]:
    logs = await list_provider_sync_logs(session, current_guardian, account_id)
    return [serialize_provider_sync_log(log) for log in logs]


@router.post("/accounts/{account_id}/sync", response_model=ProviderSyncTriggerResponse)
async def sync_provider_account(
    account_id: UUID,
    current_guardian: CurrentGuardian,
    session: DbSession,
) -> ProviderSyncTriggerResponse:
    account, sync_log = await trigger_plurall_sync(session, current_guardian, account_id)
    return ProviderSyncTriggerResponse(
        provider_account=serialize_provider_account(account),
        sync_log=serialize_provider_sync_log(sync_log),
        message="Conta Plurall validada. O Mary importou o snapshot atual do portal, atualizou os dados escolares e materializou a biblioteca base do Lucas.",
    )
