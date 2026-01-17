from __future__ import annotations

from fastapi import APIRouter

from app.schemas.config import PublicConfig
from app.services.config_service import ConfigService

router = APIRouter(tags=["config"])


@router.get("/config", response_model=PublicConfig)
async def get_config():
    return ConfigService().get_public_config()
