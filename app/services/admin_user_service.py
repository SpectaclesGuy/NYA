from __future__ import annotations

from bson import ObjectId

from app.utils.errors import AppError
from app.utils.mongo import normalize_id


class AdminUserService:
    def __init__(self, db):
        self.db = db

    async def list_users(self) -> list[dict]:
        cursor = self.db.users.find().sort("created_at", -1)
        users = []
        async for doc in cursor:
            user = normalize_id(doc)
            users.append(
                {
                    "id": user["id"],
                    "name": user.get("name", ""),
                    "email": user.get("email", ""),
                    "role": user.get("role", "USER"),
                    "blocked": user.get("blocked", False),
                    "created_at": user.get("created_at"),
                    "last_login": user.get("last_login"),
                }
            )
        return users

    async def update_user(self, user_id: str, action: str) -> None:
        if not ObjectId.is_valid(user_id):
            raise AppError(400, "invalid_user_id", "Invalid user id")
        if action == "make_admin":
            await self.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"role": "ADMIN"}})
            return
        if action == "remove_admin":
            await self.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"role": "USER"}})
            return
        if action == "block":
            await self.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"blocked": True}})
            return
        if action == "unblock":
            await self.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"blocked": False}})
            return
        raise AppError(400, "invalid_action", "Invalid admin action")
