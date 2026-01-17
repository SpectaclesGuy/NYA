from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class PublicProfileResponse(BaseModel):
    id: str
    user_id: str
    name: str
    role: Literal["USER", "MENTOR", "ADMIN"]
    skills: list[str]
    looking_for: Literal["TEAM", "MEMBER"]
    mentor_assigned: bool
    bio: str
    availability: str
