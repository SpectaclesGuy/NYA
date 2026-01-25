from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StoryItem(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    image: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1, max_length=600)
    link: str = Field(min_length=1, max_length=500)


class StoryResponse(BaseModel):
    items: list[StoryItem]
    updated_at: datetime | None = None


class StoryUpdateRequest(BaseModel):
    items: list[StoryItem]
