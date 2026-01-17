from __future__ import annotations

from app.core.config import settings


class ConfigService:
    def get_public_config(self) -> dict:
        return {"google_client_id": settings.google_client_id}
