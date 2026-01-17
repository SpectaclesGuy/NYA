from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr


class GoogleLoginRequest(BaseModel):
    id_token: str


class DevLoginRequest(BaseModel):
    email: EmailStr
    name: str | None = None


class UserSession(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Literal["USER", "MENTOR", "ADMIN"]
    last_login: datetime


class AuthResponse(BaseModel):
    user: UserSession
