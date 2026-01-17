from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class RoleSelectRequest(BaseModel):
    role: Literal["USER", "MENTOR"]


class OnboardingStatus(BaseModel):
    role: Literal["USER", "MENTOR", "ADMIN"]
    role_selected: bool
    has_profile: bool
    mentor_approved: bool = False
