from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.family import Guardian
from app.redis import redis_client
from app.schemas.family import AuthResponse, GuardianRead, TokenPair
from app.security import create_access_token, create_refresh_token, verify_password


async def login_guardian(session: AsyncSession, email: str, password: str) -> AuthResponse | None:
    guardian = await session.scalar(select(Guardian).where(Guardian.email == email, Guardian.is_active.is_(True)))
    if guardian is None or not verify_password(password, guardian.password_hash):
        return None

    access_token = create_access_token(guardian.id, guardian.family_id)
    refresh_token = create_refresh_token(guardian.id, guardian.family_id)
    ttl = 60 * 60 * 24 * settings.jwt_refresh_token_expire_days
    await redis_client.set(f"refresh:{refresh_token}", str(guardian.id), ex=ttl)

    return AuthResponse(
        guardian=GuardianRead.model_validate(guardian),
        family_id=guardian.family_id,
        tokens=TokenPair(access_token=access_token, refresh_token=refresh_token),
    )
