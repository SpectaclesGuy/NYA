from __future__ import annotations

import re

from bson import ObjectId

from app.utils.errors import AppError
from app.utils.mongo import normalize_id


class MentorService:
    def __init__(self, db):
        self.db = db

    async def list_mentors(self, domain: str | None = None, search: str | None = None) -> list[dict]:
        query: dict = {"approved_by_admin": True}
        if search:
            regex = re.compile(re.escape(search), re.IGNORECASE)
            user_ids = [user["_id"] async for user in self.db.users.find({"name": regex}, {"_id": 1})]
            or_filters = [{"domain": regex}, {"expertise": regex}]
            if user_ids:
                or_filters.append({"user_id": {"$in": user_ids}})
            query["$or"] = or_filters
        elif domain:
            query["domain"] = domain
        cursor = self.db.mentor_profiles.find(query).sort("domain", 1)
        mentors = []
        async for doc in cursor:
            profile = normalize_id(doc)
            user = await self.db.users.find_one({"_id": profile["user_id"]})
            if not user:
                continue
            mentors.append(
                {
                    "id": profile["id"],
                    "user_id": str(profile["user_id"]),
                    "name": user["name"],
                    "domain": profile.get("domain", ""),
                    "experience_years": profile.get("experience_years", 0),
                    "expertise": profile.get("expertise", []),
                    "bio": profile.get("bio", ""),
                    "availability": profile.get("availability", ""),
                    "approved_by_admin": profile.get("approved_by_admin", False),
                }
            )
        return mentors

    async def get_mentor(self, mentor_id: str) -> dict:
        if not ObjectId.is_valid(mentor_id):
            raise AppError(400, "invalid_mentor_id", "Invalid mentor id")
        object_id = ObjectId(mentor_id)
        doc = await self.db.mentor_profiles.find_one({"_id": object_id, "approved_by_admin": True})
        if not doc:
            doc = await self.db.mentor_profiles.find_one({"user_id": object_id, "approved_by_admin": True})
        if not doc:
            raise AppError(404, "mentor_not_found", "Prefect not found")
        profile = normalize_id(doc)
        user = await self.db.users.find_one({"_id": profile["user_id"]})
        if not user:
            raise AppError(404, "mentor_not_found", "Prefect not found")
        return {
            "id": profile["id"],
            "user_id": str(profile["user_id"]),
            "name": user["name"],
            "domain": profile.get("domain", ""),
            "experience_years": profile.get("experience_years", 0),
            "expertise": profile.get("expertise", []),
            "bio": profile.get("bio", ""),
            "availability": profile.get("availability", ""),
            "approved_by_admin": profile.get("approved_by_admin", False),
        }
