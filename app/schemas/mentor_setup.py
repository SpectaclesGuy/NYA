from __future__ import annotations

from pydantic import BaseModel, Field


class MentorUpsertRequest(BaseModel):
    domain: str = Field(min_length=1)
    experience_years: int = Field(ge=0, le=60)
    expertise: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    bio: str = Field(default="", max_length=1000)
    availability: str = Field(default="")


class MentorMeResponse(BaseModel):
    user_id: str
    domain: str
    experience_years: int
    expertise: list[str]
    links: list[str]
    bio: str
    availability: str
    approved_by_admin: bool
