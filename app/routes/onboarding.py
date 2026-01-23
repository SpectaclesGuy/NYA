from __future__ import annotations

from bson import ObjectId
from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, get_db
from app.schemas.onboarding import OnboardingStatus, RoleSelectRequest
from app.services.user_service import UserService
from app.utils.profile import is_capstone_profile_complete

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/status", response_model=OnboardingStatus)
async def onboarding_status(current_user=Depends(get_current_user), db=Depends(get_db)):
    role = current_user.get("role", "USER")
    role_selected = current_user.get("role_selected", False)
    has_profile = False
    mentor_approved = False
    if role == "MENTOR":
        doc = await db.mentor_profiles.find_one({"user_id": ObjectId(current_user["id"])})
        has_profile = doc is not None
        mentor_approved = bool(doc.get("approved_by_admin", False)) if doc else False
    else:
        doc = await db.capstone_profiles.find_one({"user_id": ObjectId(current_user["id"])})
        has_profile = is_capstone_profile_complete(doc)
    if has_profile:
        role_selected = True
    return {
        "role": role,
        "role_selected": role_selected,
        "has_profile": has_profile,
        "mentor_approved": mentor_approved,
    }


@router.post("/role", response_model=OnboardingStatus)
async def select_role(payload: RoleSelectRequest, current_user=Depends(get_current_user), db=Depends(get_db)):
    updated = await UserService(db).set_role(current_user["id"], payload.role)
    role = updated.get("role", "USER")
    return {"role": role, "role_selected": True, "has_profile": False, "mentor_approved": False}
