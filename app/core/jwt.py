from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import settings


class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_token(subject: str, token_type: str, expires_delta: timedelta, extra: dict | None = None) -> str:
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(_now().timestamp()),
        "exp": int((_now() + expires_delta).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, extra: dict | None = None) -> str:
    return create_token(subject, TokenType.ACCESS, timedelta(minutes=settings.jwt_access_minutes), extra)


def create_refresh_token(subject: str) -> str:
    return create_token(subject, TokenType.REFRESH, timedelta(days=settings.jwt_refresh_days))


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
