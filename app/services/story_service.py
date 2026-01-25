from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.utils.errors import AppError


DEFAULT_STORIES = [
    {
        "title": "The Big Boy on The Sofa",
        "image": "/assets/yooo.jpeg",
        "description": "A new wave of capstone leaders are forming circles across the community. Review mentor profiles and step into a team that matches your momentum.",
        "link": "/mentors",
    },
    {
        "title": "Mentor Dispatch",
        "image": "/assets/nya_logo_nobg.png",
        "description": "Freshly approved prefects are now live. Scan their focus areas and align with collaborators for the next sprint.",
        "link": "/mentor/dashboard",
    },
    {
        "title": "Project Pulse",
        "image": "/assets/nya_logo_nobg.png",
        "description": "Teams are assembling across product, AI, and design. Capture the brief, map your skill stack, and claim your seat.",
        "link": "/dashboard",
    },
    {
        "title": "Studio Open Calls",
        "image": "/assets/nya_logo_nobg.png",
        "description": "Shortlist hackathons, check deadlines, and commit to the build cycle that fits your timeline.",
        "link": "/hackathons",
    },
]


class StoryService:
    def __init__(self, db):
        self.collection = db.stories

    async def list_stories(self) -> dict[str, Any]:
        doc = await self.collection.find_one({"_id": "main_dashboard"})
        items = doc.get("items") if doc else DEFAULT_STORIES
        updated_at = doc.get("updated_at") if doc else None
        items = self._normalize_items(items)
        return {"items": items, "updated_at": updated_at}

    async def update_stories(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        if len(items) != 4:
            raise AppError(400, "invalid_story_count", "Exactly four stories are required.")
        items = self._normalize_items(items)
        updated_at = datetime.now(timezone.utc)
        await self.collection.update_one(
            {"_id": "main_dashboard"},
            {"$set": {"items": items, "updated_at": updated_at}},
            upsert=True,
        )
        return {"items": items, "updated_at": updated_at}

    def _normalize_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not items:
            return DEFAULT_STORIES
        normalized = items[:4]
        if len(normalized) < 4:
            normalized = (normalized + DEFAULT_STORIES)[:4]
        for item in normalized:
            if not item.get("link"):
                item["link"] = "/mentors"
        return normalized
