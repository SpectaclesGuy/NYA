from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProfileUpsertRequest(BaseModel):
    skills: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    looking_for: Literal["TEAM", "MEMBER"]
    bio: str = Field(default="", max_length=1000)
    availability: str = Field(default="")


class ProfileMeResponse(BaseModel):
    user_id: str
    skills: list[str]
    required_skills: list[str]
    links: list[str]
    looking_for: Literal["TEAM", "MEMBER"]
    mentor_assigned: bool
    bio: str
    availability: str
