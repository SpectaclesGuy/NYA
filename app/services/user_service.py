from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId

from app.utils.mongo import normalize_id


class UserService:
    def __init__(self, db):
        self.db = db

    async def get_user_by_id(self, user_id: str) -> dict | None:
        doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        return normalize_id(doc) if doc else None

    async def get_user_by_email(self, email: str) -> dict | None:
        doc = await self.db.users.find_one({"email": email})
        return normalize_id(doc) if doc else None

    async def create_user(self, name: str, email: str, role: str) -> dict:
        now = datetime.now(tz=timezone.utc)
        result = await self.db.users.insert_one(
            {
                "name": name,
                "email": email,
                "role": role,
                "role_selected": False,
                "created_at": now,
                "last_login": now,
            }
        )
        doc = await self.db.users.find_one({"_id": result.inserted_id})
        return normalize_id(doc)

    async def update_last_login(self, user_id: str) -> None:
        await self.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"last_login": datetime.now(tz=timezone.utc)}})

    async def get_session_user(self, user: dict) -> dict:
        return {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "last_login": user["last_login"],
        }

    async def set_role(self, user_id: str, role: str) -> dict:
        await self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"role": role, "role_selected": True}},
        )
        return await self.get_user_by_id(user_id)
