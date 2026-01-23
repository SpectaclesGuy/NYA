from __future__ import annotations

from bson import ObjectId

from app.utils.errors import AppError
from app.utils.mongo import normalize_id


class CapstoneProfileService:
    def __init__(self, db):
        self.db = db

    async def get_my_profile(self, user_id: str) -> dict:
        doc = await self.db.capstone_profiles.find_one({"user_id": ObjectId(user_id)})
        if not doc:
            raise AppError(404, "profile_not_found", "Profile not found")
        profile = normalize_id(doc)
        return {
            "user_id": str(profile["user_id"]),
            "skills": profile.get("skills", []),
            "required_skills": profile.get("required_skills", []),
            "links": profile.get("links", []),
            "looking_for": profile.get("looking_for"),
            "mentor_assigned": profile.get("mentor_assigned", False),
            "bio": profile.get("bio", ""),
            "availability": profile.get("availability", ""),
        }

    async def upsert_my_profile(
        self,
        user_id: str,
        skills: list[str],
        required_skills: list[str],
        links: list[str],
        looking_for: str,
        bio: str,
        availability: str,
    ) -> dict:
        cleaned_skills = [skill.strip() for skill in skills if skill.strip()]
        cleaned_required = [skill.strip() for skill in required_skills if skill.strip()]
        cleaned_links = [link.strip() for link in links if link.strip()]
        bio = bio.strip()
        availability = availability.strip()
        if not cleaned_skills or not cleaned_required or not cleaned_links or not bio or not availability:
            raise AppError(400, "profile_incomplete", "All profile fields are required.")
        await self.db.capstone_profiles.update_one(
            {"user_id": ObjectId(user_id)},
            {
                "$set": {
                    "user_id": ObjectId(user_id),
                    "skills": cleaned_skills,
                    "required_skills": cleaned_required,
                    "links": cleaned_links,
                    "looking_for": looking_for,
                    "mentor_assigned": False,
                    "bio": bio,
                    "availability": availability,
                }
            },
            upsert=True,
        )
        return await self.get_my_profile(user_id)
