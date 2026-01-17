from __future__ import annotations

from bson import ObjectId

from app.utils.errors import AppError
from app.utils.mongo import normalize_id


class MentorProfileService:
    def __init__(self, db):
        self.db = db

    async def get_my_profile(self, user_id: str) -> dict:
        doc = await self.db.mentor_profiles.find_one({"user_id": ObjectId(user_id)})
        if not doc:
            raise AppError(404, "mentor_profile_not_found", "Prefect profile not found")
        profile = normalize_id(doc)
        return {
            "user_id": str(profile["user_id"]),
            "domain": profile.get("domain", ""),
            "experience_years": profile.get("experience_years", 0),
            "expertise": profile.get("expertise", []),
            "links": profile.get("links", []),
            "bio": profile.get("bio", ""),
            "availability": profile.get("availability", ""),
            "approved_by_admin": profile.get("approved_by_admin", False),
        }

    async def upsert_my_profile(
        self,
        user_id: str,
        domain: str,
        experience_years: int,
        expertise: list[str],
        links: list[str],
        bio: str,
        availability: str,
    ) -> dict:
        cleaned_expertise = [skill.strip() for skill in expertise if skill.strip()]
        cleaned_links = [link.strip() for link in links if link.strip()]
        await self.db.mentor_profiles.update_one(
            {"user_id": ObjectId(user_id)},
            {
                "$set": {
                    "user_id": ObjectId(user_id),
                    "domain": domain,
                    "experience_years": experience_years,
                    "expertise": cleaned_expertise,
                    "links": cleaned_links,
                    "bio": bio,
                    "availability": availability,
                    "approved_by_admin": False,
                }
            },
            upsert=True,
        )
        return await self.get_my_profile(user_id)

    async def list_pending(self) -> list[dict]:
        cursor = self.db.mentor_profiles.find({"approved_by_admin": False})
        results = []
        async for doc in cursor:
            profile = normalize_id(doc)
            user = await self.db.users.find_one({"_id": profile["user_id"]})
            if not user:
                continue
            results.append(
                {
                    "id": profile["id"],
                    "user_id": str(profile["user_id"]),
                    "name": user.get("name", ""),
                    "email": user.get("email", ""),
                    "domain": profile.get("domain", ""),
                    "experience_years": profile.get("experience_years", 0),
                    "expertise": profile.get("expertise", []),
                    "links": profile.get("links", []),
                    "bio": profile.get("bio", ""),
                    "availability": profile.get("availability", ""),
                }
            )
        return results

    async def approve(self, mentor_profile_id: str) -> None:
        if not ObjectId.is_valid(mentor_profile_id):
            raise AppError(400, "invalid_mentor_id", "Invalid mentor id")
        await self.db.mentor_profiles.update_one(
            {"_id": ObjectId(mentor_profile_id)},
            {"$set": {"approved_by_admin": True}},
        )

    async def reject(self, mentor_profile_id: str) -> None:
        if not ObjectId.is_valid(mentor_profile_id):
            raise AppError(400, "invalid_mentor_id", "Invalid mentor id")
        await self.db.mentor_profiles.update_one(
            {"_id": ObjectId(mentor_profile_id)},
            {"$set": {"approved_by_admin": False}},
        )
