from __future__ import annotations

from typing import Annotated

import jwt
from bson import ObjectId
from fastapi import Cookie, Depends

from app.core.jwt import TokenType, decode_token
from app.core.security import ACCESS_COOKIE
from app.db.client import get_database
from app.services.user_service import UserService
from app.utils.errors import AppError


async def get_db():
    return get_database()


async def get_current_user(
    access_token: Annotated[str | None, Cookie(alias=ACCESS_COOKIE)] = None,
    db=Depends(get_db),
):
    if not access_token:
        raise AppError(401, "auth_required", "Authentication required")
    try:
        payload = decode_token(access_token)
    except jwt.PyJWTError:
        raise AppError(401, "invalid_token", "Invalid token")

    if payload.get("type") != TokenType.ACCESS:
        raise AppError(401, "invalid_token", "Invalid token type")

    user_id = payload.get("sub")
    if not user_id or not ObjectId.is_valid(user_id):
        raise AppError(401, "invalid_token", "Invalid token subject")

    user = await UserService(db).get_user_by_id(user_id)
    if not user:
        raise AppError(401, "user_not_found", "User not found")
    if user.get("blocked"):
        raise AppError(403, "user_blocked", "User account is blocked")
    return user


async def require_admin(current_user=Depends(get_current_user)):
    if current_user["role"] != "ADMIN":
        raise AppError(403, "forbidden", "Admin access required")
    return current_user


async def require_onboarding_complete(current_user=Depends(get_current_user), db=Depends(get_db)):
    if current_user.get("role") == "ADMIN":
        return current_user

    user_id = current_user.get("id")
    if not user_id or not ObjectId.is_valid(user_id):
        raise AppError(403, "profile_incomplete", "Complete your profile")

    object_id = ObjectId(user_id)
    if current_user.get("role") == "MENTOR":
        doc = await db.mentor_profiles.find_one({"user_id": object_id})
        if not doc:
            raise AppError(403, "profile_incomplete", "Complete your mentor profile")
        if not doc.get("approved_by_admin", False):
            raise AppError(403, "mentor_pending", "Mentor profile pending approval")
        return current_user

    doc = await db.capstone_profiles.find_one({"user_id": object_id})
    if not doc:
        raise AppError(403, "profile_incomplete", "Complete your profile")
    return current_user
