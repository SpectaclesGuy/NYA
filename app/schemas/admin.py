from __future__ import annotations

from pydantic import BaseModel


class PendingMentor(BaseModel):
    id: str
    user_id: str
    name: str
    email: str
    domain: str
    experience_years: int
    expertise: list[str]
    links: list[str]
    bio: str
    availability: str
