from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from app.deps import CurrentGuardian, DbSession, RedisDep
from app.errors import error_response
from app.models.family import Family, Guardian
from app.schemas.family import AuthResponse, FamilyRead, LoginRequest, RefreshRequest, TokenPair
from app.security import create_access_token, create_refresh_token, decode_token
from app.services.auth_service import login_guardian

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, session: DbSession) -> AuthResponse:
    auth = await login_guardian(session, payload.email, payload.password)
    if auth is None:
        raise error_response("INVALID_CREDENTIALS", "Invalid email or password", http_status=401)
    return auth


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, session: DbSession, redis: RedisDep) -> TokenPair:
    try:
        claims = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise error_response("INVALID_REFRESH_TOKEN", "Invalid refresh token", http_status=401) from exc
    if claims.get("type") != "refresh":
        raise error_response("INVALID_REFRESH_TOKEN", "Invalid refresh token", http_status=401)
    stored = await redis.get(f"refresh:{payload.refresh_token}")
    if stored != claims.get("sub"):
        raise error_response("INVALID_REFRESH_TOKEN", "Refresh token expired", http_status=401)
    guardian = await session.scalar(select(Guardian).where(Guardian.id == UUID(claims["sub"]), Guardian.is_active.is_(True)))
    if guardian is None:
        raise error_response("GUARDIAN_NOT_FOUND", "Guardian not found", http_status=401)
    access_token = create_access_token(guardian.id, guardian.family_id)
    refresh_token = create_refresh_token(guardian.id, guardian.family_id)
    ttl = 60 * 60 * 24 * 7
    await redis.delete(f"refresh:{payload.refresh_token}")
    await redis.set(f"refresh:{refresh_token}", str(guardian.id), ex=ttl)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=FamilyRead)
async def me(current_guardian: CurrentGuardian, session: DbSession) -> FamilyRead:
    family = await session.get(Family, current_guardian.family_id)
    if family is None:
        raise error_response("FAMILY_NOT_FOUND", "Family not found", http_status=404)
    await session.refresh(family, attribute_names=["guardians"])
    return FamilyRead.model_validate(family)
