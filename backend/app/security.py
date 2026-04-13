from __future__ import annotations

from datetime import UTC, datetime, timedelta
import base64
import hashlib
import json
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: UUID, family_id: UUID) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {"sub": str(subject), "family_id": str(family_id), "type": "access", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def create_refresh_token(subject: UUID, family_id: UUID) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {"sub": str(subject), "family_id": str(family_id), "type": "refresh", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc


def _provider_credentials_fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.jwt_secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_provider_credentials(payload: dict) -> str:
    serialized = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    return _provider_credentials_fernet().encrypt(serialized).decode("utf-8")


def decrypt_provider_credentials(token: str | None) -> dict:
    if not token:
        return {}
    try:
        decrypted = _provider_credentials_fernet().decrypt(token.encode("utf-8"))
    except InvalidToken as exc:
        raise ValueError("Invalid provider credential token") from exc
    return json.loads(decrypted.decode("utf-8"))
