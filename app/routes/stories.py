from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_db
from app.schemas.story import StoryResponse
from app.services.story_service import StoryService

router = APIRouter(tags=["stories"])


@router.get("/stories", response_model=StoryResponse)
async def list_stories(db=Depends(get_db)):
    return await StoryService(db).list_stories()
