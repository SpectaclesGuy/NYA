from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class UserSummary(BaseModel):
    id: str
    name: str
    role: Literal["USER", "MENTOR", "ADMIN"]


class DiscoverUser(BaseModel):
    id: str
    name: str
    skills: list[str]
    looking_for: Literal["TEAM", "MEMBER"]
    team_status: Literal["AVAILABLE", "IN_TEAM", "BOOKED"]
    team_count: int


class CurrentUser(BaseModel):
    id: str
    name: str
    role: Literal["USER", "MENTOR", "ADMIN"]
