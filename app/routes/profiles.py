from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, get_db
from app.schemas.profile import PublicProfileResponse
from app.schemas.profile_setup import ProfileMeResponse, ProfileUpsertRequest
from app.services.profile_service import ProfileService
from app.services.capstone_profile_service import CapstoneProfileService
from app.utils.errors import AppError

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=ProfileMeResponse)
async def get_my_profile(current_user=Depends(get_current_user), db=Depends(get_db)):
    if current_user.get("role") == "MENTOR":
        raise AppError(403, "forbidden", "Prefects cannot access capstone profile")
    service = CapstoneProfileService(db)
    return await service.get_my_profile(current_user["id"])


@router.post("/me", response_model=ProfileMeResponse)
async def upsert_my_profile(
    payload: ProfileUpsertRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    if current_user.get("role") == "MENTOR":
        raise AppError(403, "forbidden", "Prefects cannot update capstone profile")
    service = CapstoneProfileService(db)
    return await service.upsert_my_profile(
        user_id=current_user["id"],
        skills=payload.skills,
        required_skills=payload.required_skills,
        links=payload.links,
        looking_for=payload.looking_for,
        bio=payload.bio,
        availability=payload.availability,
    )


@router.get("/{user_id}", response_model=PublicProfileResponse)
async def get_profile(user_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    service = ProfileService(db)
    return await service.get_public_profile(user_id)
