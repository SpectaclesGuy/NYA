from __future__ import annotations

from pydantic import BaseModel, Field

from app.utils.mongo import PyObjectId


class MentorProfileModel(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    domain: str
    experience_years: int
    expertise: list[str]
    links: list[str] = []
    bio: str
    availability: str
    approved_by_admin: bool

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
