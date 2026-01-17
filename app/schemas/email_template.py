from __future__ import annotations

from pydantic import BaseModel


class EmailTemplateSummary(BaseModel):
    id: str
    name: str
    placeholders: list[str]


class EmailTemplateDetail(EmailTemplateSummary):
    content: str


class EmailTemplateUpdate(BaseModel):
    content: str


class EmailTemplatePreviewRequest(BaseModel):
    content: str | None = None


class EmailTemplatePreview(BaseModel):
    id: str
    html: str
