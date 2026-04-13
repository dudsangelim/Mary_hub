from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models.family import Guardian
from app.redis import get_redis
from app.security import decode_token

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]


async def get_current_guardian(
    session: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> Guardian:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    guardian_id = payload.get("sub")
    guardian = await session.scalar(select(Guardian).where(Guardian.id == UUID(guardian_id), Guardian.is_active.is_(True)))
    if guardian is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Guardian not found")
    return guardian


CurrentGuardian = Annotated[Guardian, Depends(get_current_guardian)]
