from __future__ import annotations

from typing import Any

import anyio
import jwt
import logging
from google.auth.transport import requests
from google.oauth2 import id_token

from app.core.config import settings
from app.core.jwt import TokenType, create_access_token, create_refresh_token, decode_token
from app.services.user_service import UserService
from app.utils.errors import AppError


class AuthService:
    def __init__(self, db):
        self.db = db
        self.user_service = UserService(db)

    async def login_with_google(self, token: str) -> dict:
        payload = await self._verify_google_token(token)
        email = payload.get("email")
        name = payload.get("name") or payload.get("given_name") or "Student"

        if not email or not self._is_allowed_domain(email):
            raise AppError(403, "invalid_domain", "Only @thapar.edu emails are allowed")

        user = await self.user_service.get_user_by_email(email)
        if not user:
            user = await self.user_service.create_user(name=name, email=email, role="USER")
        else:
            await self.user_service.update_last_login(user["id"])

        access_token = create_access_token(user["id"])
        refresh_token = create_refresh_token(user["id"])
        return {"user": user, "access_token": access_token, "refresh_token": refresh_token}

    async def refresh_tokens(self, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token)
        except jwt.PyJWTError:
            raise AppError(401, "invalid_token", "Invalid token")

        if payload.get("type") != TokenType.REFRESH:
            raise AppError(401, "invalid_token", "Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise AppError(401, "invalid_token", "Invalid token subject")
        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise AppError(401, "user_not_found", "User not found")

        return {
            "user": user,
            "access_token": create_access_token(user["id"]),
            "refresh_token": create_refresh_token(user["id"]),
        }

    async def dev_login(self, email: str, name: str | None = None) -> dict:
        if not self._is_allowed_domain(email):
            raise AppError(403, "invalid_domain", "Only @thapar.edu emails are allowed")
        display_name = name or email.split("@")[0]
        user = await self.user_service.get_user_by_email(email)
        if not user:
            user = await self.user_service.create_user(name=display_name, email=email, role="USER")
        else:
            await self.user_service.update_last_login(user["id"])
        return {
            "user": user,
            "access_token": create_access_token(user["id"]),
            "refresh_token": create_refresh_token(user["id"]),
        }

    async def _verify_google_token(self, token: str) -> dict[str, Any]:
        if not settings.google_client_id:
            raise AppError(500, "google_config_missing", "Google client id is not configured")

        def _verify():
            request = requests.Request()
            return id_token.verify_oauth2_token(token, request, settings.google_client_id)

        try:
            return await anyio.to_thread.run_sync(_verify)
        except ValueError as exc:
            if settings.dev_login_enabled:
                logging.getLogger("nya.auth").warning("Google token verify failed: %s", exc)
            details = str(exc) if settings.dev_login_enabled else None
            raise AppError(401, "invalid_google_token", "Invalid Google token", details)

    def _is_allowed_domain(self, email: str) -> bool:
        if settings.allow_all_domains:
            return True
        return email.lower().endswith("@thapar.edu")
