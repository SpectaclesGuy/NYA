from __future__ import annotations

from bson import ObjectId

from app.utils.errors import AppError
from app.utils.mongo import normalize_id


class ProfileService:
    def __init__(self, db):
        self.db = db

    async def get_public_profile(self, user_id: str) -> dict:
        if not ObjectId.is_valid(user_id):
            raise AppError(400, "invalid_user_id", "Invalid user id")

        user = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user or user.get("role") == "ADMIN":
            raise AppError(404, "profile_not_found", "Profile not found")

        profile = await self.db.capstone_profiles.find_one({"user_id": ObjectId(user_id)})
        if not profile:
            raise AppError(404, "profile_not_found", "Profile not found")

        profile = normalize_id(profile)
        return {
            "id": profile["id"],
            "user_id": str(profile["user_id"]),
            "name": user["name"],
            "role": user["role"],
            "skills": profile.get("skills", []),
            "looking_for": profile.get("looking_for"),
            "mentor_assigned": profile.get("mentor_assigned", False),
            "bio": profile.get("bio", ""),
            "availability": profile.get("availability", ""),
        }
