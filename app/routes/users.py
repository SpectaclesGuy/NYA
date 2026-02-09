from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, get_db, require_onboarding_complete
from app.schemas.user import CurrentUser, DiscoverUser
from app.services.discovery_service import DiscoveryService
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def _parse_skills(skills: str | None) -> list[str] | None:
    if not skills:
        return None
    parts = re.split(r"[,\s]+", skills)
    return [skill.strip() for skill in parts if skill.strip()]


@router.get("/discover", response_model=list[DiscoverUser])
async def discover_users(
    skills: str | None = Query(default=None),
    search: str | None = Query(default=None),
    looking_for: str | None = Query(default=None),
    mentor_assigned: bool | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=500),
    page: int = Query(default=1, ge=1),
    pool: bool = Query(default=False),
    current_user=Depends(require_onboarding_complete),
    db=Depends(get_db),
):
    service = DiscoveryService(db)
    return await service.discover_users(
        current_user_id=current_user["id"],
        skills=_parse_skills(skills),
        search=search,
        looking_for=looking_for,
        mentor_assigned=mentor_assigned,
        limit=limit,
        page=page,
        pool=pool,
    )


@router.get("/recommended", response_model=list[DiscoverUser])
async def recommended_users(
    limit: int = Query(default=10, ge=1, le=30),
    current_user=Depends(require_onboarding_complete),
    db=Depends(get_db),
):
    service = DiscoveryService(db)
    return await service.recommended_users(current_user_id=current_user["id"], limit=limit)


@router.get("/me", response_model=CurrentUser)
async def current_user(current_user=Depends(get_current_user), db=Depends(get_db)):
    return await UserService(db).get_session_user(current_user)
