from __future__ import annotations

from pydantic import BaseModel


class MentorSummary(BaseModel):
    id: str
    user_id: str
    name: str
    domain: str
    experience_years: int
    expertise: list[str]
    bio: str
    availability: str


class MentorDetail(MentorSummary):
    approved_by_admin: bool


class MentorEmailTemplateSummary(BaseModel):
    id: str
    name: str
    placeholders: list[str]


class MentorEmailTemplateDetail(MentorEmailTemplateSummary):
    content: str


class MentorEmailTemplateUpdate(BaseModel):
    content: str


class MentorEmailTemplatePreviewRequest(BaseModel):
    content: str | None = None


class MentorEmailTemplatePreview(BaseModel):
    id: str
    html: str
