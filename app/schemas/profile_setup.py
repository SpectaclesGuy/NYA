from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProfileUpsertRequest(BaseModel):
    skills: list[str] = Field(min_items=1)
    required_skills: list[str] = Field(min_items=1)
    links: list[str] = Field(min_items=1)
    looking_for: Literal["TEAM", "MEMBER"]
    bio: str = Field(max_length=1000, min_length=1)
    availability: str = Field(min_length=1)


class ProfileMeResponse(BaseModel):
    user_id: str
    skills: list[str]
    required_skills: list[str]
    links: list[str]
    looking_for: Literal["TEAM", "MEMBER"]
    mentor_assigned: bool
    bio: str
    availability: str
