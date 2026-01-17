from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.utils.mongo import PyObjectId


class CapstoneProfileModel(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    skills: list[str]
    required_skills: list[str] = []
    links: list[str] = []
    looking_for: Literal["TEAM", "MEMBER"]
    mentor_assigned: bool
    bio: str
    availability: str

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
