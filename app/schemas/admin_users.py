from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AdminUserSummary(BaseModel):
    id: str
    name: str
    email: str
    role: Literal["USER", "MENTOR", "ADMIN"]
    blocked: bool
    created_at: datetime
    last_login: datetime


class AdminUserUpdate(BaseModel):
    action: Literal["make_admin", "remove_admin", "block", "unblock", "reset_profile"]
